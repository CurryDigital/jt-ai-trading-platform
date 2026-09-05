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
# task t_e71cffde). The lateral below computes the 20th trading day's close from
# silver.unified_prices and is used ONLY as a fallback when the gold column is NULL
# (via COALESCE on the pct). day20_price always comes from the lateral so the UI can
# show the level.
_DAY20_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT sp.close AS close, sp.date AS dt
        FROM silver.unified_prices sp
        WHERE sp.ticker = c.ticker AND sp.date >= c.listing_date
        ORDER BY sp.date OFFSET 19 LIMIT 1
    ) d20 ON TRUE
"""

# Day-40 close: exit leg of the post-listing drift rule (enter +20td, hold 20td ->
# exit at the 40th trading day). Computed from silver.unified_prices via lateral;
# NULL until 40 trading days have elapsed since listing. Durable gold column
# backfill is qr_etl's deliverable (same pattern as return_day20_pct, t_e71cffde).
_DAY40_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT sp.close AS close, sp.date AS dt
        FROM silver.unified_prices sp
        WHERE sp.ticker = c.ticker AND sp.date >= c.listing_date
        ORDER BY sp.date OFFSET 39 LIMIT 1
    ) d40 ON TRUE
"""


@router.get("/ipos")
def get_hkex_ipos(status: str = None, sector: str = None, year: int = None, limit: int = 50,
                  db: Session = Depends(get_db)):
    zh_col = "c.stock_name_zh" if _has_column(db, "gold", "hk_ipo_calendar", "stock_name_zh") \
        else "NULL::varchar AS stock_name_zh"
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
               p.return_day30_pct, p.total_return_pct, p.current_price, p.performance_tier,
               s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
               s.grey_close, s.grey_session_date,
               CASE WHEN c.listing_date > CURRENT_DATE THEN 'Upcoming'
                    WHEN c.listing_date = CURRENT_DATE THEN 'Listing Today' ELSE 'Listed' END as status
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        LEFT JOIN LATERAL (
            SELECT s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
                   s.grey_close, s.grey_session_date
            FROM silver.unified_ipo_calendar s
            WHERE s.ticker = c.ticker
            ORDER BY s.listing_date DESC LIMIT 1
        ) s ON TRUE
        {_DAY20_LATERAL}
        {_DAY40_LATERAL}
        WHERE 1=1
    """
    params = {}
    if status == "upcoming": query += " AND c.listing_date >= CURRENT_DATE"
    elif status == "listed": query += " AND c.listing_date < CURRENT_DATE"
    if sector: query += " AND c.sector = :sector"; params["sector"] = sector
    if year: query += " AND EXTRACT(YEAR FROM c.listing_date) = :year"; params["year"] = year
    query += " ORDER BY c.listing_date DESC LIMIT :limit"; params["limit"] = limit

    result = db.execute(text(query), params).fetchall()
    return {"ipos": [{
        "ticker": r.ticker, "stock_name": r.stock_name, "stock_name_zh": r.stock_name_zh,
        "listing_date": str(r.listing_date),
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
        "return_day30": _f(r.return_day30_pct),
        "total_return": _f(r.total_return_pct),
        "current_price": _f(r.current_price),
        "performance_tier": r.performance_tier,
        "offer_price_low": _f(r.offer_price_low), "offer_price_high": _f(r.offer_price_high),
        "lot_size": r.lot_size, "fixed_price": r.fixed_price,
        "grey_close": _f(r.grey_close), "grey_session_date": _d(r.grey_session_date),
        "status": r.status,
    } for r in result], "count": len(result)}


@router.get("/ipos/subscription")
def get_hkex_ipo_subscription(db: Session = Depends(get_db)):
    """IPOs currently in (or approaching) their public subscription window.

    Subscription windows come from gold.hk_ipo_details.application_start/end (backfilled
    by qr_etl, task t_e71cffde). An empty list means no tracked windows are open right now.
    """
    zh_col = "c.stock_name_zh" if _has_column(db, "gold", "hk_ipo_calendar", "stock_name_zh") \
        else "NULL::varchar AS stock_name_zh"
    result = db.execute(text(f"""
        SELECT c.ticker, c.stock_name, {zh_col}, c.listing_date, c.offer_price, c.sector, c.sponsor,
               d.application_start, d.application_end,
               d.oversubscription_retail,
               s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
               s.grey_close, s.grey_session_date
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN LATERAL (
            SELECT s.offer_price_low, s.offer_price_high, s.lot_size, s.fixed_price,
                   s.grey_close, s.grey_session_date
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
               AVG(p.total_return_pct) as avg_current_return,
               COUNT(p.total_return_pct) as current_n,
               COUNT(CASE WHEN p.first_day_return_pct > 0 THEN 1 END)::DECIMAL / COUNT(*) * 100 as win_rate
        FROM gold.hk_ipo_calendar c
        JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        {_DAY20_LATERAL}
        WHERE c.listing_date >= {cutoff}
        GROUP BY c.sector ORDER BY avg_first_day_return DESC NULLS LAST
    """)).fetchall()
    return {"window": window, "sectors": [{
        "sector": r.sector, "ipo_count": r.ipo_count,
        "avg_first_day_return": round(float(r.avg_first_day_return), 2) if r.avg_first_day_return is not None else None,
        "avg_day20_return": round(float(r.avg_day20_return), 2) if r.avg_day20_return is not None else None,
        "day20_n": r.day20_n,
        "avg_current_return": round(float(r.avg_current_return), 2) if r.avg_current_return is not None else None,
        "current_n": r.current_n,
        "win_rate": round(float(r.win_rate), 1) if r.win_rate is not None else None}
        for r in result]}


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
