"""Command Center endpoints — home-page aggregator + account equity curve.

New surfaces added by the JTCML workspace redesign (see design-bundle
handoff/API_SPEC_v2.md + DB_CHANGES_v2.md). All reads degrade to empty via
safe_query() until the underlying gold/consumption objects are materialized
by the qr_etl data-engineering process.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from datetime import datetime, timezone

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api", tags=["command"])

SEV_ORDER = {'critical': 0, 'warning': 1, 'info': 2}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _is_cash_position(p):
    """Identify synthetic cash rows inserted by execution/IBKR sync."""
    if p.ticker == "HKD":
        return True
    if p.strategy_id and "CASH" in p.strategy_id.upper():
        return True
    return False


def _book_from_row(row):
    """Map one consumption.account_summary row verbatim (canonical, ETL-owned)."""
    if not row:
        return None
    m = row._mapping

    def _f(k):
        v = m[k]
        return float(v) if v is not None else None

    return {
        "equity": _f("equity"),
        "day_pnl": _f("day_pnl"),
        "day_pnl_pct": _f("day_pnl_pct"),
        "buying_power": _f("buying_power"),
        "cash_pct": _f("cash_pct"),
        "open_pnl": _f("open_pnl"),
        "gross_exp_pct": _f("gross_exp_pct"),
        "net_exp_pct": _f("net_exp_pct"),
        "positions": int(m["positions"]) if m["positions"] is not None else None,
    }


def _combined_account(live, paper):
    """
    'My Book' aggregate over the canonical consumption.account_summary rows
    (qr_etl, t_2b2ac824). Per-book numbers are used verbatim; the aggregate
    only re-weights them against the combined equity base:

      equity        = live.equity + paper.equity
      gross_exp_pct = combined gross deployed MV / combined equity
      net_exp_pct   = combined net deployed MV / combined equity
      cash_pct      = (equity - net deployed MV) / equity
      buying_power  = equity - gross deployed MV (matches the canonical paper
                      definition; the live row's own buying_power is IBKR
                      margin and is NOT additive, so it stays per-book only)

    If only one book row exists, it is returned verbatim. If neither exists,
    returns {} so the UI renders '—' rather than a misleading zero.
    """
    books = [b for b in (live, paper) if b and b.get("equity")]
    if not books:
        return live or paper or {}
    if len(books) == 1:
        only = dict(books[0])
        only["books"] = {"live": live, "paper": paper}
        return only

    total_equity = sum(b["equity"] for b in books)

    def _deployed(b, key):
        pct = b.get(key)
        if pct is None:
            return None
        return b["equity"] * pct / 100.0

    gross_parts = [v for v in (_deployed(b, "gross_exp_pct") for b in books) if v is not None]
    net_parts = [v for v in (_deployed(b, "net_exp_pct") for b in books) if v is not None]
    gross_mv = sum(gross_parts) if gross_parts else None
    net_mv = sum(net_parts) if net_parts else None

    def _sum(key):
        vals = [b[key] for b in books if b.get(key) is not None]
        return sum(vals) if vals else None

    day_pnl = _sum("day_pnl")
    return {
        "equity": total_equity,
        "day_pnl": day_pnl,
        "day_pnl_pct": (day_pnl / total_equity * 100.0) if day_pnl is not None and total_equity else None,
        "buying_power": max(total_equity - gross_mv, 0.0) if gross_mv is not None else _sum("buying_power"),
        "cash_pct": ((total_equity - net_mv) / total_equity * 100.0) if net_mv is not None and total_equity else None,
        "open_pnl": _sum("open_pnl"),
        "gross_exp_pct": (gross_mv / total_equity * 100.0) if gross_mv is not None and total_equity else None,
        "net_exp_pct": (net_mv / total_equity * 100.0) if net_mv is not None and total_equity else None,
        "positions": _sum("positions"),
        "books": {"live": live, "paper": paper},
    }


@router.get("/command/overview")
def get_command_overview(db: Session = Depends(get_db)):
    """Single aggregator for the Command page: account, equity curve, pipeline, deployed health, attention queue."""
    # Canonical account rows (qr_etl, t_2b2ac824): book='live' is the IBKR
    # book, book='paper' is the aggregate paper book (equity = SUM of assigned
    # capital over actively monitored PAPER strategies). Both are used
    # verbatim; 'My Book' shows their combination.
    account_rows = safe_query(db, """
        SELECT book, equity, day_pnl, day_pnl_pct, open_pnl, buying_power, cash_pct,
               gross_exp_pct, net_exp_pct, positions
        FROM consumption.account_summary WHERE book IN ('live', 'paper')
    """, label="command_account_summary")

    live_book = None
    paper_book = None
    for r in account_rows:
        if r.book == 'live':
            live_book = _book_from_row(r)
        elif r.book == 'paper':
            paper_book = _book_from_row(r)

    account = _combined_account(live_book, paper_book)

    curve_rows = safe_query(db, """
        SELECT d, equity FROM consumption.account_equity_curve
        WHERE book = 'live' ORDER BY d DESC LIMIT 30
    """, label="command_equity_curve")
    equity_curve = [{"d": str(r.d), "equity": float(r.equity)} for r in reversed(curve_rows)]

    # Pipeline counts source of truth: gold.v_pipeline_ui_feed, which is built from
    # gold.strategy_research and overlays the latest backtest/live metrics. This keeps
    # the Command Center funnel in sync with the Strategy Lab / pipeline-feed view
    # (experimental/near-golden/golden/deployed) rather than the narrower registry view.
    pipeline = None
    try:
        pipeline_row = db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE stage = 'experimental') AS experimental,
                COUNT(*) FILTER (WHERE stage = 'near_golden') AS near_golden,
                COUNT(*) FILTER (WHERE stage = 'golden') AS golden,
                COUNT(*) FILTER (WHERE stage = 'deployed') AS deployed,
                COUNT(*) AS total
            FROM gold.v_pipeline_ui_feed
        """)).fetchone()
        if pipeline_row:
            m = pipeline_row._mapping
            pipeline = {k: int(m[k] or 0) for k in ["experimental", "near_golden", "golden", "deployed", "total"]}
    except ProgrammingError as e:
        logger.warning(f"command_pipeline_counts: gold.v_pipeline_ui_feed missing: {e}")
        db.rollback()

    deployed_health = []
    try:
        deployed_rows = db.execute(text("""
            SELECT id AS strategy_id, name, asset, trades AS live_trades,
                   livewr AS live_win_rate, sharpe
            FROM gold.v_pipeline_ui_feed
            WHERE stage = 'deployed'
            ORDER BY sharpe DESC NULLS LAST LIMIT 10
        """)).fetchall()
        def _pct(v):
            if v is None:
                return None
            v = float(v)
            return round(v, 1) if v > 1.5 else round(v * 100, 1)

        deployed_health = [{
            "strategy_id": r.strategy_id, "name": r.name, "asset": r.asset,
            "live_trades": r.live_trades, "live_win_rate": _pct(r.live_win_rate),
            "sharpe": round(float(r.sharpe), 2) if r.sharpe is not None else None,
        } for r in deployed_rows]
    except ProgrammingError as e:
        logger.warning(f"command_deployed_health: gold.v_pipeline_ui_feed missing: {e}")
        db.rollback()

    attention_rows = safe_query(db, """
        SELECT item_id, severity AS sev, tag, title, impact, target, ref_id, created_at
        FROM consumption.attention_queue
        ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, created_at DESC
        LIMIT 20
    """, label="command_attention_queue")
    attention = [{
        "sev": r.sev, "tag": r.tag, "title": r.title, "impact": r.impact,
        "target": r.target, "ref_id": r.ref_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in attention_rows]

    # Strategy-perspective risks: computed from the real paper ledger
    # (gold.paper_trades, closed non-rehearsal trades — same source as
    # /api/strategies/researcher). Surfaces paper strategies whose track record
    # is deteriorating: PF below breakeven, negative cumulative P&L, low WR.
    strategy_risks = []
    risk_rows = safe_query(db, """
        SELECT r.strategy_id, r.name,
               COUNT(*) FILTER (WHERE t.status = 'closed') AS closed,
               COUNT(*) FILTER (WHERE t.status = 'closed' AND t.pnl > 0) AS wins,
               SUM(t.pnl) FILTER (WHERE t.status = 'closed') AS pnl,
               SUM(t.pnl) FILTER (WHERE t.status = 'closed' AND t.pnl > 0) AS gp,
               SUM(t.pnl) FILTER (WHERE t.status = 'closed' AND t.pnl < 0) AS gl
        FROM gold.strategy_registry r
        JOIN gold.paper_trades t ON t.strategy_id = r.strategy_id AND t.rehearsal = false
        WHERE r.status NOT IN ('DEPRECATED', 'retired')
        GROUP BY r.strategy_id, r.name
    """, label="command_strategy_risks")
    for r in risk_rows:
        closed = int(r.closed or 0)
        if closed < 10:
            continue  # too few trades to judge
        gp = float(r.gp or 0)
        gl = float(r.gl or 0)
        pf = gp / abs(gl) if gl else None
        pnl = float(r.pnl or 0)
        wr = int(r.wins or 0) / closed * 100
        sev = None
        if pf is not None and pf < 0.5:
            sev = 'critical'
        elif (pf is not None and pf < 0.8) or pnl < 0 or wr < 30:
            sev = 'warning'
        if pnl <= -2000:
            sev = 'critical'
        if sev:
            strategy_risks.append({
                "strategy_id": r.strategy_id, "name": r.name or r.strategy_id,
                "sev": sev, "closed_trades": closed,
                "paper_pf": round(pf, 2) if pf is not None else None,
                "paper_pnl": round(pnl, 2),
                "paper_wr": round(wr, 1),
            })
    strategy_risks.sort(key=lambda x: (SEV_ORDER.get(x['sev'], 9), x['paper_pf'] if x['paper_pf'] is not None else 9))

    # Monitoring gap: strategies marked PAPER in the registry but without an
    # ACTIVE paper deployment — surfaced as one aggregate info item, not 19 rows.
    gap_row = safe_query_one(db, """
        SELECT COUNT(*) AS n
        FROM gold.strategy_registry r
        WHERE UPPER(r.execution_mode) IN ('PAPER', 'PAPER_TRADING')
          AND r.status NOT IN ('DEPRECATED', 'retired')
          AND NOT EXISTS (
              SELECT 1 FROM consumption.portfolio_positions_current p
              WHERE p.strategy_id = r.strategy_id
                AND p.status = 'ACTIVE'
                AND p.execution_mode = 'PAPER_TRADING'
          )
    """, label="command_monitoring_gap")
    monitoring_gap = int(gap_row.n) if gap_row and gap_row.n is not None else 0

    # Current-calendar-month realized P&L per execution mode, from the canonical
    # ledgers (realized closed trades only — no estimates, no synthetic rows):
    #   SIM   -> gold.paper_trades_synthetic (closed, exit_date this month)
    #   PAPER -> gold.paper_trades (closed, rehearsal=false, updated_at this month)
    #   LIVE  -> gold.trade_executions (LIVE modes, executed_at this month)
    # Each mode is null when it has no closed trades this month so the UI can
    # render '—' instead of a misleading $0.
    def _month_bucket(row):
        if not row or not row.trades:
            return None
        return {"trades": int(row.trades), "pnl": float(row.pnl or 0)}

    monthly_pnl = {
        "sim": _month_bucket(safe_query_one(db, """
            SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
            FROM gold.paper_trades_synthetic
            WHERE status = 'closed' AND exit_date >= date_trunc('month', now())::date
        """, label="command_monthly_pnl_sim")),
        "paper": _month_bucket(safe_query_one(db, """
            SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
            FROM gold.paper_trades
            WHERE status = 'closed' AND rehearsal = false
              AND updated_at >= date_trunc('month', now())
        """, label="command_monthly_pnl_paper")),
        "live": _month_bucket(safe_query_one(db, """
            SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
            FROM gold.trade_executions
            WHERE UPPER(execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND pnl IS NOT NULL
              AND executed_at >= date_trunc('month', now())
        """, label="command_monthly_pnl_live")),
    }

    # Paper book attribution for the current month: per-strategy realized P&L
    # (same ledger as strategy_risks). Powers the Command panel that shows
    # leaders/laggards while nothing is live-deployed.
    book_rows = safe_query(db, """
        SELECT t.strategy_id, r.name,
               COUNT(*) AS closed, SUM(t.pnl) AS pnl
        FROM gold.paper_trades t
        LEFT JOIN gold.strategy_registry r ON r.strategy_id = t.strategy_id
        WHERE t.status = 'closed' AND t.rehearsal = false
          AND t.updated_at >= date_trunc('month', now())
        GROUP BY t.strategy_id, r.name
    """, label="command_paper_book_month")
    book = [{
        "strategy_id": r.strategy_id, "name": r.name or r.strategy_id,
        "closed_trades": int(r.closed or 0), "pnl": round(float(r.pnl or 0), 2),
    } for r in book_rows]
    book.sort(key=lambda x: x["pnl"], reverse=True)
    paper_book_month = {
        "leaders": [b for b in book if b["pnl"] > 0][:3],
        "laggards": sorted([b for b in book if b["pnl"] < 0], key=lambda x: x["pnl"])[:3],
    }

    # Per-asset-class paper-book breakdown for the Command "My Book" strip:
    # each class shows open P&L (mark-to-market) vs closed P&L YTD (realized),
    # plus open/closed trade counts. Asset class comes from the strategy
    # registry, normalized to the platform's canonical classes. Open P&L reads
    # the canonical ETL mark (sync_paper_positions_current.py, t_646c098a:
    # latest gold.daily_ohlcv close, fallback entry_price) — no serve-time
    # recomputation. Closed stats use the canonical paper ledger
    # gold.paper_trades_synthetic (same source as the Lab Closed P&L column).
    def _norm_asset(v):
        v = (v or '').upper()
        if v in ('ETF',):
            return 'ETF'
        if v in ('COMMODITY', 'COMMODITIES', 'FUTURE', 'FUTURES'):
            return 'COMMODITY'
        if v == 'FX':
            return 'FX'
        if v == 'CRYPTO':
            return 'CRYPTO'
        return 'EQUITY'

    breakdown = {}

    def _bucket(asset_class):
        k = _norm_asset(asset_class)
        return breakdown.setdefault(k, {
            "asset_class": k, "open_positions": 0, "open_pnl": 0.0,
            "unpriced": 0, "closed_trades_ytd": 0, "closed_pnl_ytd": 0.0,
        })

    open_rows = safe_query(db, """
        SELECT p.strategy_id, p.ticker, p.entry_price, p.current_price,
               p.unrealized_pnl, r.asset_class
        FROM consumption.portfolio_positions_current p
        LEFT JOIN gold.strategy_registry r
          ON r.strategy_id = p.strategy_id
        WHERE p.status = 'ACTIVE' AND p.quantity > 0
          AND p.execution_mode = 'PAPER_TRADING'
    """, label="command_asset_breakdown_open")
    for p in open_rows:
        if _is_cash_position(p):
            continue
        b = _bucket(p.asset_class)
        b["open_positions"] += 1
        if p.unrealized_pnl is not None:
            b["open_pnl"] += float(p.unrealized_pnl)
        else:
            b["unpriced"] += 1

    closed_rows = safe_query(db, """
        SELECT r.asset_class, COUNT(*) AS n, SUM(t.pnl) AS pnl
        FROM gold.paper_trades_synthetic t
        LEFT JOIN gold.strategy_registry r ON r.strategy_id = t.strategy_id
        WHERE t.status = 'closed'
          AND t.exit_date >= date_trunc('year', now())::date
          AND (t.ticker IS NULL OR t.ticker != 'CASH')
        GROUP BY r.asset_class
    """, label="command_asset_breakdown_closed")
    for r in closed_rows:
        b = _bucket(r.asset_class)
        b["closed_trades_ytd"] = int(r.n or 0)
        b["closed_pnl_ytd"] = float(r.pnl or 0)

    ASSET_ORDER = {'EQUITY': 0, 'ETF': 1, 'COMMODITY': 2, 'FX': 3, 'CRYPTO': 4}
    asset_breakdown = sorted(breakdown.values(), key=lambda b: ASSET_ORDER.get(b["asset_class"], 9))
    for b in asset_breakdown:
        b["open_pnl"] = round(b["open_pnl"], 2)
        b["closed_pnl_ytd"] = round(b["closed_pnl_ytd"], 2)

    # --- Regime + Alignment (Command P0-2) ---
    # Per market: current regime label (consumption.market_sentiment, canonical),
    # HMM posterior confidence + days-in-regime run length (gold.regime_label,
    # US-scope — SPY/VIX features), and count of active strategies whose
    # declared regime_scope (gold.v_strategy_book_extended) matches vs conflicts
    # with the current regime. 'ANY' scope counts as agnostic, never conflict.
    # Missing data stays null so the UI renders '—' instead of inventing zeros.
    sentiment_rows = safe_query(db, """
        SELECT region, regime, updated_at FROM consumption.market_sentiment
        WHERE region IN ('US', 'HK')
    """, label="command_regime_sentiment")
    regime_by_region = {r.region: r for r in sentiment_rows}

    # US regime series: latest label + consecutive run length
    rl_rows = safe_query(db, """
        SELECT date, regime, confidence FROM gold.regime_label ORDER BY date DESC LIMIT 120
    """, label="command_regime_label")
    us_series = None
    if rl_rows:
        latest = rl_rows[0]
        run = 0
        for r in rl_rows:
            if r.regime == latest.regime:
                run += 1
            else:
                break
        us_series = {
            "regime": latest.regime,
            # Raw posterior — do NOT round here. round(x, 4) turns genuine
            # 0.99999998 posteriors into exactly 1.0, which reads as a
            # placeholder. The UI formats honestly (>=0.99995 → '>99.99%').
            "confidence": float(latest.confidence) if latest.confidence is not None else None,
            "days_in_regime": run,
            "as_of": str(latest.date),
            "staleness_days": (datetime.now(timezone.utc).date() - latest.date).days,
        }

    # Regime-fit over active strategies (registry is the active-set source of
    # truth; regime_scope declared in the extended book).
    fit_rows = safe_query(db, """
        SELECT b.regime_scope, COUNT(*) AS n
        FROM gold.strategy_registry r
        LEFT JOIN gold.v_strategy_book_extended b ON b.strategy_id = r.strategy_id
        WHERE UPPER(r.execution_mode) IN ('PAPER', 'PAPER_TRADING', 'LIVE', 'LIVE_TRADING')
          AND r.status NOT IN ('retired', 'DEPRECATED', 'rejected', 'paused')
        GROUP BY b.regime_scope
    """, label="command_regime_fit")

    def _fit(regime):
        matched = agnostic = conflicted = active = 0
        for r in fit_rows:
            scope = (r.regime_scope or 'ANY').upper()
            n = int(r.n or 0)
            active += n
            if scope == 'ANY':
                agnostic += n
            elif regime and scope == regime.upper():
                matched += n
            else:
                conflicted += n
        return {"matched": matched, "agnostic": agnostic, "conflicted": conflicted, "active": active}

    regime_alignment = {}
    for region in ('US', 'HK'):
        sent = regime_by_region.get(region)
        regime = (sent.regime if sent else None) or (us_series["regime"] if region == 'US' and us_series else None)
        entry = {
            "regime": regime,
            "confidence": us_series["confidence"] if region == 'US' and us_series else None,
            "days_in_regime": us_series["days_in_regime"] if region == 'US' and us_series else None,
            "as_of": us_series["as_of"] if region == 'US' and us_series else None,
            "staleness_days": us_series["staleness_days"] if region == 'US' and us_series else None,
            "sentiment_updated_at": sent.updated_at.isoformat() if sent and sent.updated_at else None,
            "fit": _fit(regime),
        }
        regime_alignment[region] = entry

    return {
        "account": account,
        "equity_curve": equity_curve,
        "pipeline": pipeline,
        "monthly_pnl": monthly_pnl,
        "paper_book_month": paper_book_month,
        "asset_breakdown": asset_breakdown,
        "deployed_health": deployed_health,
        "attention": attention,
        "strategy_risks": strategy_risks,
        "monitoring_gap": monitoring_gap,
        "regime_alignment": regime_alignment,
        "as_of": _now_iso(),
    }


@router.get("/account/equity-curve")
def get_account_equity_curve(days: int = 30, book: str = "live", db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT d, equity FROM consumption.account_equity_curve
        WHERE book = :book ORDER BY d DESC LIMIT :days
    """, {"book": book, "days": days}, label="account_equity_curve")
    data = [{"d": str(r.d), "equity": float(r.equity)} for r in reversed(rows)]
    return {"data": data, "as_of": _now_iso() if data else None}
