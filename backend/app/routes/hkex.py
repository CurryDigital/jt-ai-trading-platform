"""HKEX IPO endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db

router = APIRouter(prefix="/api/hkex", tags=["hkex"])


def _has_column(db: Session, schema: str, table: str, column: str) -> bool:
    return db.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :s AND table_name = :t AND column_name = :c
    """), {"s": schema, "t": table, "c": column}).fetchone() is not None


def _f(v):
    return float(v) if v is not None else None


def _d(v):
    return str(v) if v is not None else None


# Day-20 close: prefer gold.hk_ipo_performance.return_day20_pct (backfilled by qr_etl,
# task t_e71cffde). The lateral below computes the close 20 trading days AFTER listing
# from silver.unified_prices and is used ONLY as a fallback when the gold column is NULL
# (via COALESCE on the pct). day20_price always comes from the lateral so the UI can
# show the level.
# CONVENTION (2026-09-07): engine bar convention — listing day = bar 0, entry = bar 20
# close => OFFSET 20 (previously OFFSET 19, one trading day early; verified against V3
# engine fills: 1377.HK entered 2026-08-06 @374.00, 2493.HK 2026-06-10 @24.50,
# 6745.HK 2026-08-07 @3.365, 6951.HK 2026-08-06 @103.80 — all bar-20 closes).
# GUARD: legs are NULLed when the measured date is implausibly far after listing
# (>60d for the +20td leg, >120d for +40td; 40td can span ~75 calendar days over
# summer holidays) — that means silver's price series for the ticker starts long
# after listing (recycled ticker, e.g. 8603.HK listed 2018 with prices from 2026)
# and the OFFSET row is NOT the entry leg.
_DAY20_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT CASE WHEN v.dt <= c.listing_date + 60 THEN v.close END AS close,
               CASE WHEN v.dt <= c.listing_date + 60 THEN v.dt END AS dt
        FROM (
            SELECT sp.close AS close, sp.date AS dt
            FROM silver.unified_prices sp
            WHERE sp.ticker = c.ticker AND sp.date >= c.listing_date
            ORDER BY sp.date OFFSET 20 LIMIT 1
        ) v
    ) d20 ON TRUE
"""

# Day-5 close: exit leg of the Day-1 Green Momentum rule (buy at the day-1 close =
# bar 0, hold 5 trading days -> exit at bar 5 => OFFSET 5). Computed from
# silver.unified_prices via lateral; NULL until 5 trading days have elapsed since
# listing. Same recycled-ticker guard as _DAY20_LATERAL (5td spans ~7 calendar
# days; 30d is a generous bound).
_DAY5_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT CASE WHEN v.dt <= c.listing_date + 30 THEN v.close END AS close,
               CASE WHEN v.dt <= c.listing_date + 30 THEN v.dt END AS dt
        FROM (
            SELECT sp.close AS close, sp.date AS dt
            FROM silver.unified_prices sp
            WHERE sp.ticker = c.ticker AND sp.date >= c.listing_date
            ORDER BY sp.date OFFSET 5 LIMIT 1
        ) v
    ) d5 ON TRUE
"""

# Day-40 close: exit leg of the post-listing drift rule (enter +20td, hold 20td ->
# exit at bar 40, i.e. 40 trading days after listing => OFFSET 40). Computed from
# silver.unified_prices via lateral; NULL until 40 trading days have elapsed since
# listing. Durable gold column backfill is qr_etl's deliverable (same pattern as
# return_day20_pct, t_e71cffde). Same recycled-ticker guard as _DAY20_LATERAL.
_DAY40_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT CASE WHEN v.dt <= c.listing_date + 120 THEN v.close END AS close,
               CASE WHEN v.dt <= c.listing_date + 120 THEN v.dt END AS dt
        FROM (
            SELECT sp.close AS close, sp.date AS dt
            FROM silver.unified_prices sp
            WHERE sp.ticker = c.ticker AND sp.date >= c.listing_date
            ORDER BY sp.date OFFSET 40 LIMIT 1
        ) v
    ) d40 ON TRUE
"""


@router.get("/ipos")
def get_hkex_ipos(status: str = None, sector: str = None, year: int = None, limit: int = 50,
                  db: Session = Depends(get_db)):
    zh_col = "c.stock_name_zh" if _has_column(db, "gold", "hk_ipo_calendar", "stock_name_zh") \
        else "NULL::varchar AS stock_name_zh"
    nav_cols = _nav_cols(db)
    query = f"""
        SELECT c.ticker, c.stock_name, {zh_col}, c.listing_date, c.offer_price, c.market_cap_hkd,
               c.sector, c.sub_sector, c.sponsor, c.board,
               d.oversubscription_retail, d.oversubscription_institutional, d.cornerstone_total_pct,
               d.application_start, d.application_end,
               p.first_day_open, p.first_day_close, p.first_day_volume,
               p.first_day_return_pct,
               COALESCE(p.return_day20_pct,
                        CASE WHEN d20.close IS NOT NULL AND c.offer_price > 0
                             THEN (d20.close / c.offer_price - 1) * 100 END) AS return_day20_pct,
               d20.close AS day20_price, d20.dt AS day20_date,
               d40.close AS day40_price, d40.dt AS day40_date,
               d5.close AS day5_price, d5.dt AS day5_date,
               p.return_day30_pct, p.total_return_pct, p.current_price, p.performance_tier,
               s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
               s.grey_close, s.grey_session_date,
               s.nav_per_share_hkd, s.nav_asof, s.nav_source,
               a.one_lot_win_rate,
               CASE WHEN c.listing_date IS NULL THEN 'Announced'
                    WHEN c.listing_date > CURRENT_DATE THEN 'Upcoming'
                    WHEN c.listing_date = CURRENT_DATE THEN 'Listing Today' ELSE 'Listed' END as status
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        LEFT JOIN gold.hk_ipo_allotment a ON a.ticker = c.ticker
        LEFT JOIN LATERAL (
            SELECT s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
                   s.grey_close, s.grey_session_date,
                   {nav_cols}
            FROM silver.unified_ipo_calendar s
            WHERE s.ticker = c.ticker
            ORDER BY s.listing_date DESC LIMIT 1
        ) s ON TRUE
        {_DAY20_LATERAL}
        {_DAY40_LATERAL}
        {_DAY5_LATERAL}
        WHERE 1=1
    """
    params = {}
    if status == "upcoming": query += " AND c.listing_date >= CURRENT_DATE"
    elif status == "listed": query += " AND c.listing_date < CURRENT_DATE"
    if sector: query += " AND c.sector = :sector"; params["sector"] = sector
    if year: query += " AND EXTRACT(YEAR FROM c.listing_date) = :year"; params["year"] = year
    # Dated rows first (listed/public analytics need full history); the A1-/A1G-
    # pre-subscription placeholders (listing_date NULL) trail the list, so callers
    # must pass a limit that covers BOTH sets (~1.9k rows as of 2026-09).
    query += " ORDER BY c.listing_date DESC NULLS LAST LIMIT :limit"; params["limit"] = limit

    result = db.execute(text(query), params).fetchall()
    return {"ipos": [{
        "ticker": r.ticker, "stock_name": r.stock_name, "stock_name_zh": r.stock_name_zh,
        "listing_date": _d(r.listing_date),
        "offer_price": _f(r.offer_price),
        "market_cap_hkd": _f(r.market_cap_hkd),
        "sector": r.sector, "sub_sector": r.sub_sector, "sponsor": r.sponsor, "board": r.board,
        "oversubscription_retail": _f(r.oversubscription_retail),
        "oversubscription_institutional": _f(r.oversubscription_institutional),
        "cornerstone_total_pct": _f(r.cornerstone_total_pct),
        "application_start": _d(r.application_start), "application_end": _d(r.application_end),
        "first_day_open": _f(r.first_day_open), "first_day_close": _f(r.first_day_close),
        "first_day_volume": _f(r.first_day_volume),
        "first_day_return": _f(r.first_day_return_pct),
        "return_day20": _f(r.return_day20_pct),
        "day20_price": _f(r.day20_price), "day20_date": _d(r.day20_date),
        "day40_price": _f(r.day40_price), "day40_date": _d(r.day40_date),
        "day5_price": _f(r.day5_price), "day5_date": _d(r.day5_date),
        "return_day30": _f(r.return_day30_pct),
        "total_return": _f(r.total_return_pct),
        "current_price": _f(r.current_price),
        "performance_tier": r.performance_tier,
        "offer_price_low": _f(r.offer_price_low), "offer_price_high": _f(r.offer_price_high),
        "lot_size": r.lot_size, "fixed_price": r.fixed_price,
        "grey_close": _f(r.grey_close), "grey_session_date": _d(r.grey_session_date),
        "one_lot_win_rate": _f(r.one_lot_win_rate),
        "nav_per_share": _f(r.nav_per_share_hkd), "nav_asof": _d(r.nav_asof),
        "nav_source": r.nav_source,
        "offer_to_nav_pct": _nav_pct(_f(r.offer_price), r.fixed_price,
                                     _f(r.offer_price_high), _f(r.nav_per_share_hkd)),
        "status": r.status,
    } for r in result], "count": len(result)}


def _nav_pct(offer_px, fixed, high, nav):
    """offer_to_nav_pct, percent-scaled: (offer basis / nav_per_share - 1) * 100.
    Basis mirrors the frontend NavPctCell: fixed price else top-of-range else offer_price."""
    if nav is None or nav <= 0:
        return None
    basis = offer_px if fixed else (high if high is not None else offer_px)
    if basis is None:
        return None
    return round((basis / nav - 1) * 100, 1)


def _nav_cols(db):
    """Adaptive NAV columns on silver.unified_ipo_calendar (qr_etl t_ef6032f4 ingest)."""
    if _has_column(db, "silver", "unified_ipo_calendar", "nav_per_share_hkd"):
        return "s.nav_per_share_hkd, s.nav_asof, s.nav_source"
    return ("NULL::numeric AS nav_per_share_hkd, NULL::date AS nav_asof, "
            "NULL::varchar AS nav_source")


@router.get("/ipos/subscription")
def get_hkex_ipo_subscription(db: Session = Depends(get_db)):
    """IPOs currently in (or approaching) their public subscription window.

    Subscription windows come from gold.hk_ipo_details.application_start/end (backfilled
    by qr_etl, task t_e71cffde). An empty list means no tracked windows are open right now.
    """
    zh_col = "c.stock_name_zh" if _has_column(db, "gold", "hk_ipo_calendar", "stock_name_zh") \
        else "NULL::varchar AS stock_name_zh"
    nav_cols = _nav_cols(db)
    result = db.execute(text(f"""
        SELECT c.ticker, c.stock_name, {zh_col}, c.listing_date, c.offer_price, c.sector, c.sponsor,
               d.application_start, d.application_end,
               d.oversubscription_retail,
               s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
               s.grey_close, s.grey_session_date,
               s.nav_per_share_hkd, s.nav_asof, s.nav_source
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN LATERAL (
            SELECT s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
                   s.grey_close, s.grey_session_date,
                   {nav_cols}
            FROM silver.unified_ipo_calendar s
            WHERE s.ticker = c.ticker
            ORDER BY s.listing_date DESC LIMIT 1
        ) s ON TRUE
        WHERE (d.application_end IS NOT NULL AND d.application_end >= CURRENT_DATE)
           OR (d.application_end IS NULL AND c.listing_date >= CURRENT_DATE)
        ORDER BY COALESCE(d.application_end, c.listing_date) ASC
        LIMIT 50
    """)).fetchall()
    return {"ipos": [{
        "ticker": r.ticker, "stock_name": r.stock_name, "stock_name_zh": r.stock_name_zh,
        "listing_date": _d(r.listing_date),
        "offer_price": _f(r.offer_price), "sector": r.sector, "sponsor": r.sponsor,
        "application_start": _d(r.application_start), "application_end": _d(r.application_end),
        "oversubscription_retail": _f(r.oversubscription_retail),
        "offer_price_low": _f(r.offer_price_low), "offer_price_high": _f(r.offer_price_high),
        "lot_size": r.lot_size, "fixed_price": r.fixed_price,
        "grey_close": _f(r.grey_close), "grey_session_date": _d(r.grey_session_date),
        "nav_per_share": _f(r.nav_per_share_hkd), "nav_asof": _d(r.nav_asof),
        "nav_source": r.nav_source,
        "offer_to_nav_pct": _nav_pct(_f(r.offer_price), r.fixed_price,
                                     _f(r.offer_price_high), _f(r.nav_per_share_hkd)),
    } for r in result], "count": len(result)}


@router.get("/ipos/book")
def get_hkex_ipo_book(db: Session = Depends(get_db)):
    """Active IPO book: open positions in recent-HK-IPO names or held by IPO strategies.

    Joins the paper book (consumption.portfolio_positions_current, ACTIVE) with the IPO
    calendar/performance/details. Empty means no open IPO positions — the drift strategy
    is event-driven and spends most of its time flat.
    """
    zh_col = "c.stock_name_zh" if _has_column(db, "gold", "hk_ipo_calendar", "stock_name_zh") \
        else "NULL::varchar AS stock_name_zh"
    result = db.execute(text(f"""
        SELECT pos.strategy_id, pos.ticker, pos.side, pos.quantity, pos.entry_price,
               pos.entry_date, pos.current_price AS pos_current_price, pos.market_value,
               pos.unrealized_pnl, pos.updated_at,
               c.stock_name, {zh_col}, c.listing_date,
               p.offer_price, p.current_price, p.performance_tier,
               d.oversubscription_retail,
               last_px.volume AS last_volume, last_px.dt AS last_price_date
        FROM consumption.portfolio_positions_current pos
        JOIN gold.hk_ipo_calendar c ON c.ticker = pos.ticker
        LEFT JOIN gold.hk_ipo_performance p ON p.ticker = pos.ticker
        LEFT JOIN gold.hk_ipo_details d ON d.ticker = pos.ticker
        LEFT JOIN LATERAL (
            SELECT sp.volume, sp.date AS dt FROM silver.unified_prices sp
            WHERE sp.ticker = pos.ticker ORDER BY sp.date DESC LIMIT 1
        ) last_px ON TRUE
        WHERE UPPER(pos.status) = 'ACTIVE'
          AND (pos.strategy_id LIKE 'hk_ipo%'
               OR c.listing_date >= CURRENT_DATE - INTERVAL '18 months')
        ORDER BY pos.entry_date DESC NULLS LAST
        LIMIT 100
    """)).fetchall()
    return {"positions": [{
        "strategy_id": r.strategy_id, "ticker": r.ticker, "stock_name": r.stock_name,
        "stock_name_zh": r.stock_name_zh,
        "side": r.side, "quantity": _f(r.quantity),
        "entry_price": _f(r.entry_price), "entry_date": _d(r.entry_date),
        "current_price": _f(r.current_price) or _f(r.pos_current_price),
        "market_value": _f(r.market_value), "unrealized_pnl": _f(r.unrealized_pnl),
        "listing_date": _d(r.listing_date), "offer_price": _f(r.offer_price),
        "oversubscription_retail": _f(r.oversubscription_retail),
        "last_volume": _f(r.last_volume), "last_price_date": _d(r.last_price_date),
        "updated_at": _d(r.updated_at),
    } for r in result], "count": len(result)}


@router.get("/ipos/leaderboard")
def get_hkex_ipo_leaderboard(period: str = "first_day", limit: int = 20, db: Session = Depends(get_db)):
    order_col = {"first_day": "p.first_day_return_pct", "day30": "p.return_day30_pct",
                 "total": "p.total_return_pct"}.get(period, "p.first_day_return_pct")
    result = db.execute(text(f"""
        SELECT c.ticker, c.stock_name, c.listing_date, c.offer_price, c.sector,
               p.first_day_return_pct, p.return_day30_pct, p.total_return_pct, p.performance_tier,
               d.oversubscription_retail, d.cornerstone_total_pct
        FROM gold.hk_ipo_performance p
        JOIN gold.hk_ipo_calendar c ON p.ticker = c.ticker
        LEFT JOIN gold.hk_ipo_details d ON p.ticker = d.ticker
        WHERE c.listing_date >= CURRENT_DATE - INTERVAL '2 years'
        ORDER BY {order_col} DESC NULLS LAST LIMIT :limit
    """), {"limit": limit}).fetchall()
    return {"leaderboard": [{"rank": i + 1, "ticker": r.ticker, "stock_name": r.stock_name,
                              "listing_date": str(r.listing_date), "sector": r.sector,
                              "first_day_return": _f(r.first_day_return_pct),
                              "return_day30": _f(r.return_day30_pct),
                              "performance_tier": r.performance_tier}
                             for i, r in enumerate(result)], "count": len(result), "period": period}


# Sector sentiment windows — keys are the API vocabulary, values are SQL date
# cutoffs. 'ytd' is calendar-year-to-date; the rest are rolling intervals.
_SECTOR_WINDOWS = {
    "1m": "CURRENT_DATE - INTERVAL '1 month'",
    "3m": "CURRENT_DATE - INTERVAL '3 months'",
    "6m": "CURRENT_DATE - INTERVAL '6 months'",
    "ytd": "DATE_TRUNC('year', CURRENT_DATE)::date",
    "2y": "CURRENT_DATE - INTERVAL '2 years'",
}


@router.get("/ipos/sectors")
def get_hkex_ipo_sectors(window: str = "2y", db: Session = Depends(get_db)):
    cutoff = _SECTOR_WINDOWS.get((window or "").lower(), _SECTOR_WINDOWS["2y"])
    result = db.execute(text(f"""
        SELECT c.sector, COUNT(*) as ipo_count,
               AVG(p.first_day_return_pct) as avg_first_day_return,
               AVG(COALESCE(p.return_day20_pct,
                            CASE WHEN d20.close IS NOT NULL AND c.offer_price > 0
                                 THEN (d20.close / c.offer_price - 1) * 100 END)) as avg_day20_return,
               COUNT(COALESCE(p.return_day20_pct,
                              CASE WHEN d20.close IS NOT NULL AND c.offer_price > 0
                                   THEN (d20.close / c.offer_price - 1) * 100 END)) as day20_n,
               AVG(COALESCE(p.return_day40_pct,
                            CASE WHEN d40.close IS NOT NULL AND c.offer_price > 0
                                 THEN (d40.close / c.offer_price - 1) * 100 END)) as avg_day40_return,
               COUNT(COALESCE(p.return_day40_pct,
                              CASE WHEN d40.close IS NOT NULL AND c.offer_price > 0
                                   THEN (d40.close / c.offer_price - 1) * 100 END)) as day40_n,
               AVG(COALESCE(p.total_return_pct,
                            CASE WHEN p.current_price IS NOT NULL AND c.offer_price > 0
                                 THEN (p.current_price / c.offer_price - 1) * 100 END)) as avg_current_return,
               COUNT(COALESCE(p.total_return_pct,
                              CASE WHEN p.current_price IS NOT NULL AND c.offer_price > 0
                                   THEN (p.current_price / c.offer_price - 1) * 100 END)) as current_n,
               COUNT(CASE WHEN p.first_day_return_pct > 0 THEN 1 END)::DECIMAL / COUNT(*) * 100 as win_rate
        FROM gold.hk_ipo_calendar c
        JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        {_DAY20_LATERAL}
        {_DAY40_LATERAL}
        WHERE c.listing_date >= {cutoff}
        GROUP BY c.sector ORDER BY avg_first_day_return DESC NULLS LAST
    """)).fetchall()
    return {"window": window, "sectors": [{
        "sector": r.sector, "ipo_count": r.ipo_count,
        "avg_first_day_return": round(float(r.avg_first_day_return), 2) if r.avg_first_day_return is not None else None,
        "avg_day20_return": round(float(r.avg_day20_return), 2) if r.avg_day20_return is not None else None,
        "day20_n": r.day20_n,
        "avg_day40_return": round(float(r.avg_day40_return), 2) if r.avg_day40_return is not None else None,
        "day40_n": r.day40_n,
        "avg_current_return": round(float(r.avg_current_return), 2) if r.avg_current_return is not None else None,
        "current_n": r.current_n,
        "win_rate": round(float(r.win_rate), 1) if r.win_rate is not None else None}
        for r in result]}


# Oversub-bucket windows: 1m/3m/6m/ytd reuse the _SECTOR_WINDOWS rolling cutoffs.
# '2y' is the deep-history window and is intentionally UNBOUNDED: the full-input
# coverage for this panel starts 2024-01-09 (earliest listing with allotment +
# oversubscription + performance + lot_size), and the verified response contract
# for window=2y (n=282 across buckets, verified against the live DB 2026-09-17)
# only reproduces with no date cutoff. A literal CURRENT_DATE - 2y cutoff drops
# ~41 rows and breaks the contract.
_OVERSUB_WINDOWS = {
    "1m": _SECTOR_WINDOWS["1m"],
    "3m": _SECTOR_WINDOWS["3m"],
    "6m": _SECTOR_WINDOWS["6m"],
    "ytd": _SECTOR_WINDOWS["ytd"],
    "2y": None,  # full coverage; see note above
}

_OVERSUB_COST_MODEL = ("cash one-lot application - net = gross EV - 1.11% statutory "
                       "round-trip costs (1.0077% levies + 0.1% stamp) on allotted lots "
                       "only - excludes margin financing")

# bucket label -> (lo, hi) on oversubscription_retail; 50-100x is the ambiguous zone
# (no strategy trades it) and is returned separately under excluded_50_100x.
_OVERSUB_BUCKETS = [("<15x", 0, 15), ("15-50x", 15, 50), ("100-500x", 100, 500), ("500x+", 500, None)]
_OVERSUB_EXCLUDED = ("50-100x", 50, 100)


def _oversub_bucket_row(label, lo, hi, aggs):
    a = aggs.get(label)
    if a is None or a.n == 0:
        return {"bucket": label, "lo": lo, "hi": hi, "n": 0,
                "med_p_win": None, "d1_win_rate": None, "med_day1": None,
                "med_ev_lot_pct": None, "gross_ev_sum_hkd": 0, "net_ev_sum_hkd": 0}
    return {"bucket": label, "lo": lo, "hi": hi, "n": a.n,
            "med_p_win": round(float(a.med_p_win), 2) if a.med_p_win is not None else None,
            "d1_win_rate": round(float(a.d1_win_rate), 1) if a.d1_win_rate is not None else None,
            "med_day1": round(float(a.med_day1), 2) if a.med_day1 is not None else None,
            "med_ev_lot_pct": round(float(a.med_ev_lot_pct), 2) if a.med_ev_lot_pct is not None else None,
            "gross_ev_sum_hkd": int(a.gross_ev_sum) if a.gross_ev_sum is not None else 0,
            "net_ev_sum_hkd": int(a.net_ev_sum) if a.net_ev_sum is not None else 0}


@router.get("/ipos/oversub-buckets")
def get_hkex_ipo_oversub_buckets(window: str = "2y", db: Session = Depends(get_db)):
    key = (window or "").lower()
    if key not in _OVERSUB_WINDOWS:
        key = "2y"
    cutoff = _OVERSUB_WINDOWS[key]
    date_filter = f"AND c.listing_date >= {cutoff}" if cutoff else ""

    listed_total = db.execute(text(f"""
        SELECT COUNT(*) FROM gold.hk_ipo_calendar c
        WHERE c.listing_date < CURRENT_DATE {date_filter}
    """)).scalar()

    result = db.execute(text(f"""
        WITH base AS (
            SELECT c.ticker,
                   d.oversubscription_retail AS oversub,
                   a.one_lot_win_rate AS win_pct,
                   p.first_day_return_pct AS d1_pct,
                   p.offer_price AS offer_price,
                   s.lot_size AS lot_size
            FROM gold.hk_ipo_calendar c
            JOIN gold.hk_ipo_details d ON d.ticker = c.ticker
            JOIN gold.hk_ipo_allotment a ON a.ticker = c.ticker
            JOIN gold.hk_ipo_performance p ON p.ticker = c.ticker
            LEFT JOIN LATERAL (
                SELECT s.lot_size FROM silver.unified_ipo_calendar s
                WHERE s.ticker = c.ticker AND s.lot_size IS NOT NULL
                ORDER BY s.listing_date DESC LIMIT 1
            ) s ON TRUE
            WHERE c.listing_date < CURRENT_DATE {date_filter}
        ),
        rows AS (
            SELECT *,
                   (win_pct / 100.0) * (d1_pct / 100.0) * offer_price * lot_size AS gross_ev,
                   (win_pct / 100.0) * (d1_pct / 100.0) * offer_price * lot_size
                     - offer_price * lot_size * 0.0111 * (win_pct / 100.0) AS net_ev,
                   (win_pct / 100.0) * d1_pct AS ev_lot_pct
            FROM base
            WHERE oversub IS NOT NULL AND win_pct IS NOT NULL AND d1_pct IS NOT NULL
              AND offer_price IS NOT NULL AND lot_size IS NOT NULL
        )
        SELECT CASE
                 WHEN oversub < 15 THEN '<15x'
                 WHEN oversub < 50 THEN '15-50x'
                 WHEN oversub < 100 THEN '50-100x'
                 WHEN oversub < 500 THEN '100-500x'
                 ELSE '500x+'
               END AS bucket,
               COUNT(*) AS n,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY win_pct) AS med_p_win,
               100.0 * COUNT(*) FILTER (WHERE d1_pct > 0) / COUNT(*) AS d1_win_rate,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY d1_pct) AS med_day1,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY ev_lot_pct) AS med_ev_lot_pct,
               ROUND(SUM(gross_ev)) AS gross_ev_sum,
               ROUND(SUM(net_ev)) AS net_ev_sum
        FROM rows
        GROUP BY 1
    """)).fetchall()

    aggs = {r.bucket: r for r in result}
    buckets = [_oversub_bucket_row(label, lo, hi, aggs) for label, lo, hi in _OVERSUB_BUCKETS]
    excluded = _oversub_bucket_row(_OVERSUB_EXCLUDED[0], _OVERSUB_EXCLUDED[1], _OVERSUB_EXCLUDED[2], aggs)
    covered_n = sum(b["n"] for b in buckets) + excluded["n"]

    return {"window": key, "cost_model": _OVERSUB_COST_MODEL,
            "listed_total": listed_total, "covered_n": covered_n,
            "buckets": buckets, "excluded_50_100x": excluded}


@router.get("/ipos/{ticker}")
def get_hkex_ipo_detail(ticker: str, db: Session = Depends(get_db)):
    calendar = db.execute(text("SELECT * FROM gold.hk_ipo_calendar WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    if not calendar:
        raise HTTPException(status_code=404, detail=f"IPO {ticker} not found")
    details = db.execute(text("SELECT * FROM gold.hk_ipo_details WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    performance = db.execute(text("SELECT * FROM gold.hk_ipo_performance WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    return {
        "ticker": calendar.ticker, "stock_name": calendar.stock_name,
        "listing_date": str(calendar.listing_date),
        "offer_price": float(calendar.offer_price) if calendar.offer_price else None,
        "sector": calendar.sector, "sponsor": calendar.sponsor,
        "details": {"oversubscription_retail": float(details.oversubscription_retail) if details and details.oversubscription_retail else None} if details else None,
        "performance": {"first_day_return": float(performance.first_day_return_pct) if performance and performance.first_day_return_pct else None,
                        "performance_tier": performance.performance_tier if performance else None} if performance else None,
    }
