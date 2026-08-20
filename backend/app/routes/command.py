"""Command Center endpoints — home-page aggregator + account equity curve.

New surfaces added by the JTCML workspace redesign (see design-bundle
handoff/API_SPEC_v2.md + DB_CHANGES_v2.md). All reads degrade to empty via
safe_query() until the underlying gold/consumption objects are materialized
by the qr_etl data-engineering process.
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from datetime import datetime, timezone, timedelta

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one
from app.db.session import engine

router = APIRouter(prefix="/api", tags=["command"])

SEV_ORDER = {'critical': 0, 'warning': 1, 'info': 2}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Alert acknowledgements (Command P0-3): acks/snoozes persist server-side with
# actor + timestamp so a dismissed alert stays dismissed across sessions.
# Table is self-healing (CREATE IF NOT EXISTS); formal ownership migration is
# qr_etl's call. Key space: attention item_id, 'risk:<strategy_id>', 'gap:*'.
# ---------------------------------------------------------------------------
_ACK_DDL = """
CREATE TABLE IF NOT EXISTS consumption.alert_acknowledgements (
    alert_key    TEXT PRIMARY KEY,
    action       TEXT NOT NULL,            -- 'acknowledge' | 'snooze'
    actor        TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    snooze_until TIMESTAMPTZ               -- set only for snooze
)
"""
_ack_ready = False


def _ensure_ack_table():
    global _ack_ready
    if _ack_ready:
        return
    try:
        with engine.begin() as conn:
            conn.execute(text(_ACK_DDL))
        _ack_ready = True
    except Exception as e:
        logger.warning(f"alert_acknowledgements DDL failed: {e}")


def _actor(request) -> str:
    """Best-effort actor from the bearer token; 'local' when auth is off."""
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            from app.auth import verify_token
            payload = verify_token(auth[7:])
            if payload:
                return payload.get("sub") or payload.get("username") or "user"
    except Exception:
        pass
    return "local"


def _ack_map(db) -> dict:
    """alert_key -> {action, actor, at, snooze_until}; active dismissals only."""
    _ensure_ack_table()
    try:
        rows = safe_query(db, """
            SELECT alert_key, action, actor, created_at, snooze_until
            FROM consumption.alert_acknowledgements
            WHERE action = 'acknowledge'
               OR (action = 'snooze' AND snooze_until > now())
        """, label="command_alert_acks")
    except Exception:
        return {}
    now = datetime.now(timezone.utc)
    out = {}
    for r in rows:
        out[r.alert_key] = {
            "action": r.action,
            "actor": r.actor,
            "at": r.created_at.isoformat() if r.created_at else None,
            "snooze_until": r.snooze_until.isoformat() if r.snooze_until else None,
        }
    return out


@router.post("/command/alerts/ack")
def ack_command_alert(payload: dict, request: Request, db: Session = Depends(get_db)):
    """Acknowledge or snooze a Command-page alert. Upserts by alert_key."""
    key = (payload or {}).get("alert_key") or ""
    key = key.strip()
    action = (payload or {}).get("action")
    if not key:
        raise HTTPException(status_code=400, detail="alert_key required")
    if action not in ("acknowledge", "snooze"):
        raise HTTPException(status_code=400, detail="action must be 'acknowledge' or 'snooze'")
    minutes = 60
    if action == "snooze":
        try:
            minutes = max(1, min(10080, int((payload or {}).get("snooze_minutes") or 60)))
        except (TypeError, ValueError):
            minutes = 60
    _ensure_ack_table()
    actor = _actor(request)
    db.execute(text("""
        INSERT INTO consumption.alert_acknowledgements (alert_key, action, actor, created_at, snooze_until)
        VALUES (:k, :a, :actor, now(), CASE WHEN :a = 'snooze' THEN now() + make_interval(mins => :m) ELSE NULL END)
        ON CONFLICT (alert_key) DO UPDATE SET
            action = EXCLUDED.action, actor = EXCLUDED.actor,
            created_at = EXCLUDED.created_at, snooze_until = EXCLUDED.snooze_until
    """), {"k": key, "a": action, "actor": actor, "m": minutes})
    db.commit()
    return {"ok": True, "alert_key": key, "action": action, "actor": actor,
            "snooze_minutes": minutes if action == "snooze" else None, "at": _now_iso()}


@router.get("/command/alerts/acks")
def command_alert_acks(db: Session = Depends(get_db)):
    """Active dismissals map for the Command page (ack + unexpired snoozes)."""
    return {"acks": _ack_map(db), "as_of": _now_iso()}


def _alert_action(tag, ref_id):
    """Primary action verb for an attention item. Only wired to real
    endpoints: 'reconnect' exists solely for ibkr (POST /api/ib/tws/connect);
    ETL-side feeds have no reconnect — honest 'open' (Settings data sources)."""
    if (tag or "").upper() == "DATA" and ref_id == "ibkr":
        return "reconnect"
    return "open"


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

    # Net Cash Flow (t_b662b4e9 delivered the source; t_98afd0f5 wires it):
    # consumption.account_cash_flow_summary is the canonical per-book ledger
    # rollup (live SQL view over consumption.account_cash_flows). NULL means
    # 'no data' — never coerced to 0. The live book currently has NO
    # cash-flow source (IBKR cash transactions are not yet ingested), so
    # live stays all-NULL and the UI renders '—' with a distinct no-source
    # treatment rather than a fake zero.
    cf_rows = safe_query(db, """
        SELECT book, today_net, mtd_net, flows_today_count, flows_mtd_count,
               last_flow_date, net_all_time, updated_at
        FROM consumption.account_cash_flow_summary
        WHERE book IN ('live', 'paper')
    """, label="command_cash_flow_summary")

    def _cf_row(row):
        m = row._mapping

        def _f(k):
            v = m[k]
            return float(v) if v is not None else None

        return {
            "today_net": _f("today_net"),
            "mtd_net": _f("mtd_net"),
            "flows_today_count": int(m["flows_today_count"] or 0),
            "flows_mtd_count": int(m["flows_mtd_count"] or 0),
            "last_flow_date": str(m["last_flow_date"]) if m["last_flow_date"] else None,
            "net_all_time": _f("net_all_time"),
            "updated_at": m["updated_at"].isoformat() if m["updated_at"] else None,
        }

    cash_flow = {"live": None, "paper": None}
    for r in cf_rows:
        if r.book in cash_flow:
            cash_flow[r.book] = _cf_row(r)

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
    acks = _ack_map(db)
    attention = [{
        "id": str(r.item_id), "sev": r.sev, "tag": r.tag, "title": r.title,
        "impact": r.impact, "target": r.target, "ref_id": r.ref_id,
        "action": _alert_action(r.tag, r.ref_id),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in attention_rows if str(r.item_id) not in acks]

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
            # Only the metrics that BREACHED, with their thresholds — the UI
            # renders these as labeled chips; the full metric set stays
            # available on hover (P0-3). Falls back gracefully if absent.
            triggers = []
            if pf is not None and pf < 0.5:
                triggers.append(f"PF {pf:.2f} < 0.50")
            elif pf is not None and pf < 0.8:
                triggers.append(f"PF {pf:.2f} < 0.80")
            if pnl <= -2000:
                triggers.append(f"P&L {pnl:+,.0f} ≤ -2K")
            elif pnl < 0:
                triggers.append(f"P&L {pnl:+,.0f} < 0")
            if wr < 30:
                triggers.append(f"WR {wr:.0f}% < 30%")
            strategy_risks.append({
                "strategy_id": r.strategy_id, "name": r.name or r.strategy_id,
                "sev": sev, "closed_trades": closed,
                "paper_pf": round(pf, 2) if pf is not None else None,
                "paper_pnl": round(pnl, 2),
                "paper_wr": round(wr, 1),
                "triggers": triggers,
            })
    strategy_risks = [s for s in strategy_risks if f"risk:{s['strategy_id']}" not in acks]
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
    if 'gap:monitoring' in acks:
        monitoring_gap = 0

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
    # regime_scope_declared (2026-08-19 contract, qr_etl t_469a21c1): the view
    # defaults every unmapped strategy to regime_scope='ANY'. Counting those
    # rows inflates 'agnostic' with DEFAULTS, not researched declarations, so
    # matched/conflicted/agnostic are computed ONLY over declared=true rows.
    # Undeclared actives are surfaced via `classified` (declared-row count);
    # classified==0 with active>0 means the whole active book is unclassified.
    fit_rows = safe_query(db, """
        SELECT b.regime_scope, b.regime_scope_declared, COUNT(*) AS n
        FROM gold.strategy_registry r
        LEFT JOIN gold.v_strategy_book_extended b ON b.strategy_id = r.strategy_id
        WHERE UPPER(r.execution_mode) IN ('PAPER', 'PAPER_TRADING', 'LIVE', 'LIVE_TRADING')
          AND r.status NOT IN ('retired', 'DEPRECATED', 'rejected', 'paused')
        GROUP BY b.regime_scope, b.regime_scope_declared
    """, label="command_regime_fit")

    def _fit(regime):
        matched = agnostic = conflicted = active = classified = 0
        for r in fit_rows:
            n = int(r.n or 0)
            active += n
            # NULL (join miss) or false = unmapped default, not a declaration
            if not r.regime_scope_declared:
                continue
            classified += n
            scope = (r.regime_scope or 'ANY').upper()
            if scope == 'ANY':
                agnostic += n
            elif regime and scope == regime.upper():
                matched += n
            else:
                conflicted += n
        return {"matched": matched, "agnostic": agnostic, "conflicted": conflicted,
                "classified": classified, "active": active}

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
        "cash_flow": cash_flow,
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


# ---------------------------------------------------------------------------
# Command redesign (2026-08-20): P&L-by-Mode hero + Order Book.
# Per-mode realized ledgers (canonical mapping, qr_etl-owned):
#   SIM   -> gold.paper_trades_synthetic (closed, exit_date)
#   PAPER -> gold.paper_trades (closed, rehearsal=false, updated_at)
#   LIVE  -> gold.trade_executions (LIVE modes, executed_at)
# Everything is read-only; a mode with no data returns nulls (never a
# misleading $0) so the UI can render '—'.
# ---------------------------------------------------------------------------

def _mode_ledger_queries(mode):
    """Query block per mode. Date columns differ per ledger, so the mode
    selects whole SQL statements; nothing is interpolated at request time."""
    if mode == "sim":
        return {
            "closed": """
                SELECT COUNT(*) AS closed,
                       COUNT(*) FILTER (WHERE pnl > 0) AS wins,
                       SUM(pnl) AS cum_pnl
                FROM gold.paper_trades_synthetic
                WHERE status = 'closed' AND (ticker IS NULL OR ticker != 'CASH')
            """,
            "today": """
                SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
                FROM gold.paper_trades_synthetic
                WHERE status = 'closed' AND exit_date = CURRENT_DATE
                  AND (ticker IS NULL OR ticker != 'CASH')
            """,
            "daily": """
                SELECT exit_date AS d, SUM(pnl) AS pnl
                FROM gold.paper_trades_synthetic
                WHERE status = 'closed' AND exit_date IS NOT NULL
                  AND exit_date >= CURRENT_DATE - 29
                  AND (ticker IS NULL OR ticker != 'CASH')
                GROUP BY exit_date ORDER BY exit_date
            """,
            "open_strats": """
                SELECT t.strategy_id, r.name, COUNT(*) AS n
                FROM gold.paper_trades_synthetic t
                LEFT JOIN gold.strategy_registry r ON r.strategy_id = t.strategy_id
                WHERE t.status = 'open' AND (t.ticker IS NULL OR t.ticker != 'CASH')
                GROUP BY t.strategy_id, r.name ORDER BY n DESC
            """,
            "open_count": """
                SELECT COUNT(*) AS n FROM gold.paper_trades_synthetic
                WHERE status = 'open' AND (ticker IS NULL OR ticker != 'CASH')
            """,
        }
    if mode == "paper":
        return {
            "closed": """
                SELECT COUNT(*) AS closed,
                       COUNT(*) FILTER (WHERE pnl > 0) AS wins,
                       SUM(pnl) AS cum_pnl
                FROM gold.paper_trades
                WHERE status = 'closed' AND rehearsal = false
                  AND (ticker IS NULL OR ticker != 'CASH')
            """,
            "today": """
                SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
                FROM gold.paper_trades
                WHERE status = 'closed' AND rehearsal = false
                  AND updated_at::date = CURRENT_DATE
                  AND (ticker IS NULL OR ticker != 'CASH')
            """,
            "daily": """
                SELECT updated_at::date AS d, SUM(pnl) AS pnl
                FROM gold.paper_trades
                WHERE status = 'closed' AND rehearsal = false
                  AND updated_at >= CURRENT_DATE - 29
                  AND (ticker IS NULL OR ticker != 'CASH')
                GROUP BY updated_at::date ORDER BY 1
            """,
            "open_strats": """
                SELECT t.strategy_id, r.name, COUNT(*) AS n
                FROM gold.paper_trades t
                LEFT JOIN gold.strategy_registry r ON r.strategy_id = t.strategy_id
                WHERE t.status = 'open' AND t.rehearsal = false
                  AND (t.ticker IS NULL OR t.ticker != 'CASH')
                GROUP BY t.strategy_id, r.name ORDER BY n DESC
            """,
            "open_count": """
                SELECT COUNT(*) AS n FROM gold.paper_trades
                WHERE status = 'open' AND rehearsal = false
                  AND (ticker IS NULL OR ticker != 'CASH')
            """,
        }
    # live
    return {
        "closed": """
            SELECT COUNT(*) AS closed,
                   COUNT(*) FILTER (WHERE pnl > 0) AS wins,
                   SUM(pnl) AS cum_pnl
            FROM gold.trade_executions
            WHERE UPPER(execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND pnl IS NOT NULL
        """,
        "today": """
            SELECT COUNT(*) AS trades, SUM(pnl) AS pnl
            FROM gold.trade_executions
            WHERE UPPER(execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND pnl IS NOT NULL AND executed_at::date = CURRENT_DATE
        """,
        "daily": """
            SELECT executed_at::date AS d, SUM(pnl) AS pnl
            FROM gold.trade_executions
            WHERE UPPER(execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND pnl IS NOT NULL AND executed_at >= CURRENT_DATE - 29
            GROUP BY executed_at::date ORDER BY 1
        """,
        "open_strats": """
            SELECT t.strategy_id, r.name, COUNT(*) AS n
            FROM gold.trade_executions t
            LEFT JOIN gold.strategy_registry r ON r.strategy_id = t.strategy_id
            WHERE UPPER(t.execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND UPPER(COALESCE(t.status, '')) IN ('OPEN', 'WORKING', 'FILLED')
            GROUP BY t.strategy_id, r.name ORDER BY n DESC
        """,
        "open_count": """
            SELECT COUNT(*) AS n FROM gold.trade_executions
            WHERE UPPER(execution_mode) IN ('LIVE', 'LIVE_TRADING')
              AND UPPER(COALESCE(status, '')) IN ('OPEN', 'WORKING', 'FILLED')
        """,
    }


@router.get("/command/pnl-by-mode")
def get_command_pnl_by_mode(db: Session = Depends(get_db)):
    """P&L by execution mode — the Command page hero.

    Per mode: cumulative realized P&L, today's realized P&L (null when no
    exits today), win rate over closed trades, open/closed trade counts,
    strategies currently deployed in that mode (open-trade bearers), and a
    30-day cumulative realized P&L sparkline (carry-forward over quiet days).
    """
    modes = {}
    for mode in ("live", "paper", "sim"):
        q = _mode_ledger_queries(mode)
        closed_row = safe_query_one(db, q["closed"], label=f"pnl_mode_{mode}_closed")
        today_row = safe_query_one(db, q["today"], label=f"pnl_mode_{mode}_today")
        daily_rows = safe_query(db, q["daily"], label=f"pnl_mode_{mode}_daily")
        strat_rows = safe_query(db, q["open_strats"], label=f"pnl_mode_{mode}_strats")
        open_row = safe_query_one(db, q["open_count"], label=f"pnl_mode_{mode}_open")

        closed = int(closed_row.closed or 0) if closed_row else 0
        wins = int(closed_row.wins or 0) if closed_row else 0
        cum_pnl = float(closed_row.cum_pnl) if closed_row and closed_row.cum_pnl is not None else None
        today = None
        if today_row and today_row.trades:
            today = {"trades": int(today_row.trades), "pnl": float(today_row.pnl or 0)}

        # 30-day carry-forward cumulative sparkline
        by_day = {r.d: float(r.pnl or 0) for r in daily_rows}
        spark = []
        if by_day or cum_pnl is not None:
            start = datetime.now(timezone.utc).date() - timedelta(days=29)
            # Anchor the cumulation on all-time P&L before the window so the
            # sparkline level matches cum_pnl, not just the window's delta.
            prior = (cum_pnl or 0.0) - sum(by_day.values()) if cum_pnl is not None else 0.0
            run = prior
            for i in range(30):
                d = start + timedelta(days=i)
                run += by_day.get(d, 0.0)
                spark.append({"d": str(d), "cum": round(run, 2)})

        strategies = [{"strategy_id": r.strategy_id, "name": r.name or r.strategy_id,
                       "open_trades": int(r.n or 0)} for r in strat_rows[:6]]
        modes[mode] = {
            "cum_pnl": round(cum_pnl, 2) if cum_pnl is not None else None,
            "today": today,
            "win_rate": round(wins / closed * 100, 1) if closed else None,
            "closed_trades": closed,
            "open_trades": int(open_row.n or 0) if open_row else 0,
            "strategies": strategies,
            "strategies_overflow": max(0, len(strat_rows) - 6),
            "spark": spark,
        }
    return {"modes": modes, "as_of": _now_iso()}


# Order Book (Command redesign): working orders across the live and paper
# books, unified into one queue. Sources (all read-only):
#   gold.paper_pending_orders (status='pending')  -> paper working orders
#   gold.ibkr_orders (IBKR working statuses)      -> live working orders
# Last price = latest gold.daily_ohlcv close (canonical mark, exact ticker
# match only — no invented suffix mapping). est_gain is side-aware limit-vs-
# last and stays null for MKT orders or unpriced tickers.
_IBKR_WORKING = ('PreSubmitted', 'Submitted', 'ApiPending', 'PendingSubmit', 'PartiallyFilled')
_ORDER_STATUS_MAP = {
    'PartiallyFilled': 'Part Fill',
    'Submitted': 'Working',
    'PreSubmitted': 'Pending',
    'ApiPending': 'Pending',
    'PendingSubmit': 'Pending',
}


@router.get("/command/order-book")
def get_command_order_book(db: Session = Depends(get_db)):
    orders = []

    paper_rows = safe_query(db, """
        SELECT p.ticker, p.order_kind, p.n_shares, p.signal_weight,
               p.assigned_capital, p.signal_date, p.created_at,
               p.strategy_id, r.name AS strategy_name
        FROM gold.paper_pending_orders p
        LEFT JOIN gold.strategy_registry r ON r.strategy_id = p.strategy_id
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC LIMIT 50
    """, label="command_order_book_paper")
    for r in paper_rows:
        orders.append({
            "source": "paper",
            "ticker": r.ticker,
            "side": "BUY" if (r.order_kind or "").upper() == "OPEN" else (r.order_kind or None),
            "qty": float(r.n_shares) if r.n_shares is not None else None,
            "limit_price": None,  # paper orders fill at next mark — no limit
            "status": "Pending",
            "venue": "PAPER",
            "strategy_id": r.strategy_id,
            "strategy_name": r.strategy_name,
            "assigned_capital": float(r.assigned_capital) if r.assigned_capital is not None else None,
            "submitted_at": r.created_at.isoformat() if r.created_at else None,
            "signal_date": str(r.signal_date) if r.signal_date else None,
        })

    ibkr_rows = safe_query(db, """
        SELECT ticker, action, quantity, order_type, price, status,
               filled, remaining, submit_time
        FROM gold.ibkr_orders
        WHERE status = ANY(:st)
        ORDER BY submit_time DESC NULLS LAST LIMIT 50
    """, {"st": list(_IBKR_WORKING)}, label="command_order_book_ibkr")
    for r in ibkr_rows:
        limit = float(r.price) if r.price is not None and float(r.price) > 0 else None
        orders.append({
            "source": "live",
            "ticker": r.ticker,
            "side": (r.action or "").upper() or None,
            "qty": float(r.quantity) if r.quantity is not None else None,
            "limit_price": limit,
            "status": _ORDER_STATUS_MAP.get(r.status, r.status),
            "venue": "IBKR",
            "order_type": r.order_type,
            "filled": int(r.filled or 0),
            "remaining": int(r.remaining or 0),
            "submitted_at": r.submit_time.isoformat() if r.submit_time else None,
        })

    # Latest close per ticker (exact match; tickers that don't resolve keep
    # last_price=null rather than guessing a suffix mapping).
    tickers = sorted({o["ticker"] for o in orders if o.get("ticker")})
    last_px = {}
    if tickers:
        px_rows = safe_query(db, """
            SELECT DISTINCT ON (ticker) ticker, close, date
            FROM gold.daily_ohlcv
            WHERE ticker = ANY(:t)
            ORDER BY ticker, date DESC
        """, {"t": tickers}, label="command_order_book_marks")
        for r in px_rows:
            last_px[r.ticker] = {"last": float(r.close), "as_of": str(r.date)}

    for o in orders:
        mark = last_px.get(o["ticker"])
        o["last_price"] = mark["last"] if mark else None
        o["last_price_as_of"] = mark["as_of"] if mark else None
        est = None
        if o.get("limit_price") is not None and o.get("last_price") is not None and o.get("qty"):
            if o["side"] == "BUY":
                est = (o["last_price"] - o["limit_price"]) * o["qty"]
            elif o["side"] == "SELL":
                est = (o["limit_price"] - o["last_price"]) * o["qty"]
        o["est_gain"] = round(est, 2) if est is not None else None

    return {"orders": orders, "as_of": _now_iso()}


# Regime Forecast (Command redesign): 7-day risk-on probability per market
# from consumption.macro_regime_7d (qr_etl-owned, momentum_nowcast). The raw
# table carries forecast_date per day_offset so the UI labels bars with real
# weekdays instead of guessing offsets from the client clock. Label rule is
# display policy: >=60 Risk-On, <=40 Risk-Off, else Neutral.
def _risk_label(pct):
    if pct is None:
        return None
    if pct >= 60:
        return "Risk-On"
    if pct <= 40:
        return "Risk-Off"
    return "Neutral"


@router.get("/command/regime-forecast")
def get_command_regime_forecast(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT scope, day_offset, risk_on_pct, forecast_date, method, is_stale, updated_at
        FROM consumption.macro_regime_7d
        WHERE scope IN ('US', 'HK')
        ORDER BY scope, day_offset
    """, label="command_regime_forecast")
    markets = {}
    for r in rows:
        m = markets.setdefault(r.scope, {"days": [], "method": r.method,
                                         "is_stale": bool(r.is_stale),
                                         "updated_at": r.updated_at.isoformat() if r.updated_at else None})
        m["days"].append({
            "offset": int(r.day_offset),
            "date": str(r.forecast_date) if r.forecast_date else None,
            "risk_on": float(r.risk_on_pct) if r.risk_on_pct is not None else None,
        })
    out = {}
    for scope, m in markets.items():
        days = sorted(m["days"], key=lambda d: d["offset"])
        latest = days[0]["risk_on"] if days else None
        out[scope] = {
            "days": days,
            "latest": latest,
            "label": _risk_label(latest),
            "method": m["method"],
            "is_stale": m["is_stale"],
            "updated_at": m["updated_at"],
        }
    return {"markets": out, "as_of": _now_iso()}
