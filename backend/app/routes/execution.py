"""Execution mode endpoints — global mode, simulation reset, manual orders, live ops."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import time

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api/execution", tags=["execution"])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()

# Cache for IBKR account balance (5 min TTL), keyed per session
_ibkr_balance_cache: dict = {"data": None, "timestamp": None, "session": None}


@router.get("/global-mode")
def get_global_execution_mode(db: Session = Depends(get_db)):
    """Get global platform execution mode and account balance info."""
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    sim_capital = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'simulation_capital'"
    )).fetchone()
    sim_amount = float(sim_capital.value) if sim_capital else 100000

    sim_used, sim_positions = 0, 0
    if current_mode == "SIMULATION":
        sim_stats = db.execute(text("""
            SELECT COALESCE(SUM(capital), 0) as total_allocated, COUNT(*) as position_count
            FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE'
        """)).fetchone()
        sim_used = float(sim_stats.total_allocated) if sim_stats else 0
        sim_positions = int(sim_stats.position_count) if sim_stats else 0

    response = {
        "execution_mode": current_mode,
        "available_modes": ["SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"],
        "risk_level": {"SIMULATION": "ZERO", "PAPER_TRADING": "LOW", "UAT": "LOW", "LIVE_TRADING": "HIGH"}.get(current_mode, "UNKNOWN"),
        "simulation_capital": sim_amount, "simulation_used": sim_used,
        "simulation_available": sim_amount - sim_used, "simulation_positions": sim_positions,
    }

    # IBKR balance for broker-backed modes.
    # UAT reads the dedicated UAT paper session; PAPER_TRADING /
    # LIVE_TRADING read the primary session (existing behaviour).
    if current_mode in ["PAPER_TRADING", "UAT", "LIVE_TRADING"]:
        try:
            if current_mode == "UAT":
                from app.services.ib_service import ib_uat_service as _svc
                session_name = "uat"
            else:
                from app.services.ib_service import ib_quant_service as _svc
                session_name = "primary"
            now = time.time()
            if (_ibkr_balance_cache["data"] and _ibkr_balance_cache["timestamp"]
                    and (now - _ibkr_balance_cache["timestamp"]) < 300
                    and _ibkr_balance_cache.get("session") == session_name):
                response.update(_ibkr_balance_cache["data"])
                response["cached"] = True
            else:
                try:
                    tws_status = _svc.get_status()
                    if tws_status.get("is_connected"):
                        account_info = _svc.get_account_summary()
                        if account_info:
                            # Currency-labeled contract (t_22dee93d): every
                            # figure carries its own currency + a USD
                            # conversion from the payload's ExchangeRate rows.
                            # No `hkd or usd` cross-currency fallbacks.
                            ibkr_data = {
                                "ibkr_connected": True,
                                "account_currency": account_info.get("base_currency"),
                                "account_balance": account_info.get("available_funds"),
                                "account_balance_currency": account_info.get("available_funds_currency"),
                                "account_balance_usd": account_info.get("available_funds_usd"),
                                "net_liquidation": account_info.get("net_liquidation"),
                                "net_liquidation_currency": account_info.get("net_liquidation_currency"),
                                "net_liquidation_usd": account_info.get("net_liquidation_usd"),
                                "buying_power": account_info.get("buying_power"),
                                "buying_power_currency": account_info.get("buying_power_currency"),
                                "buying_power_usd": account_info.get("buying_power_usd"),
                                "cash_hkd": account_info.get("cash_hkd"),
                                "cash_usd": account_info.get("cash_usd"),
                                "cash_total": account_info.get("cash_total"),
                                "cash_total_currency": account_info.get("cash_total_currency"),
                                "fx": account_info.get("fx"),
                                "fx_error": account_info.get("fx_error"),
                                "account": account_info.get("account", "Unknown"),
                                "account_type": "LIVE" if current_mode == "LIVE_TRADING" else "PAPER",
                                "session": session_name,
                            }
                            _ibkr_balance_cache["data"] = ibkr_data
                            _ibkr_balance_cache["timestamp"] = now
                            _ibkr_balance_cache["session"] = session_name
                            response.update(ibkr_data)
                            response["cached"] = False
                        else:
                            response["ibkr_connected"] = True
                            response["session"] = session_name
                            response["warning"] = "Connected but could not fetch account details"
                    else:
                        response["ibkr_connected"] = False
                        response["session"] = session_name
                        response["warning"] = "TWS not connected" if session_name == "primary" else "UAT paper session not connected"
                except Exception as ibkr_err:
                    response["ibkr_connected"] = False
                    response["session"] = session_name
                    response["warning"] = f"IBKR check failed ({session_name} session): {ibkr_err}"
        except Exception:
            response["ibkr_connected"] = False

    return response


@router.post("/global-mode")
def set_global_execution_mode(payload: dict, db: Session = Depends(get_db)):
    mode = payload.get("execution_mode", "SIMULATION")
    sim_capital = payload.get("simulation_capital")

    if mode not in ["SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    db.execute(text("""
        INSERT INTO gold.platform_settings (key, value, updated_at)
        VALUES ('global_execution_mode', :mode, NOW())
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
    """), {"mode": mode})

    if sim_capital is not None and mode == "SIMULATION":
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_capital', :capital::text, NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """), {"capital": float(sim_capital)})

    db.commit()
    return get_global_execution_mode(db)


@router.post("/simulation/reset")
def reset_simulation(db: Session = Depends(get_db)):
    """Reset all simulation data."""
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    if current_mode != "SIMULATION":
        raise HTTPException(status_code=400, detail=f"Cannot reset in {current_mode} mode")

    try:
        count = db.execute(text("SELECT COUNT(*) as cnt FROM consumption.portfolio_positions_current")).fetchone()
        trades = db.execute(text("SELECT COUNT(*) as cnt FROM gold.trade_executions")).fetchone()
        positions_count = count.cnt if count else 0
        trades_count = trades.cnt if trades else 0

        db.execute(text("DELETE FROM consumption.portfolio_positions_current"))
        db.execute(text("DELETE FROM gold.trade_executions"))
        try: db.execute(text("DELETE FROM consumption.Portfolio_Positions_Current"))
        except: pass
        # NOTE: Performance_Trades_History dropped - no longer need to delete

        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_capital', '100000', NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """))
        db.commit()

        return {"success": True,
                "message": f"Simulation reset. Deleted {positions_count} positions and {trades_count} trades.",
                "positions_deleted": positions_count, "trades_deleted": trades_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")


# =============================================================================
# JTCML workspace redesign additions — trades, manual orders, live ops panels.
# See design-bundle handoff/API_SPEC_v2.md §6 and DB_CHANGES_v2.md §5.
# =============================================================================

@router.get("/trades")
def get_execution_trades(book: str = "live", limit: int = 50, db: Session = Depends(get_db)):
    """Recent fills for the Live/Paper trade log — algo executions + manual orders."""
    # Legacy alias: pre-rename clients and existing gold.manual_orders rows use
    # 'paper_uat'; canonical book value is now 'uat'.
    if book == "paper_uat":
        book = "uat"
    book_variants = ("uat", "paper_uat") if book == "uat" else (book,)
    # Alias as "ts" (not "t") — SQLAlchemy 2.0's Row conflicts with a column literally named "t".
    rows = safe_query(db, """
        SELECT executed_at AS ts, side, ticker, quantity AS qty, price, 'algo' AS source
        FROM gold.trade_executions ORDER BY executed_at DESC LIMIT :limit
    """, {"limit": limit}, label="execution_trades_algo")
    manual_rows = safe_query(db, """
        SELECT created_at AS ts, side, ticker, qty, entry_price AS price, 'manual' AS source
        FROM gold.manual_orders WHERE book = ANY(:books) ORDER BY created_at DESC LIMIT :limit
    """, {"books": list(book_variants), "limit": limit}, label="execution_trades_manual")
    combined = list(rows) + list(manual_rows)
    combined.sort(key=lambda r: r.ts, reverse=True)
    data = [{
        "t": r.ts.isoformat() if r.ts else None, "side": r.side, "ticker": r.ticker,
        "qty": float(r.qty) if r.qty is not None else None,
        "price": float(r.price) if r.price is not None else None, "source": r.source,
    } for r in combined[:limit]]
    return {"data": data, "as_of": _now_iso() if data else None}


# =============================================================================
# Book Overview (Execution tab layout, 2026-09-14): per-book performance
# summary for the SIM / PAPER / UAT subtabs — best-performing strategies,
# headline stats, and the YTD cumulative realized P&L curve in dollars.
# Ledgers (canonical, qr_etl-owned — same mapping as /api/command/pnl-by-mode):
#   SIM   -> gold.paper_trades_synthetic x registry SIMULATION (closed, exit_date)
#   PAPER -> gold.paper_trades_synthetic x registry PAPER      (closed, exit_date)
#   UAT   -> gold.paper_uat_fills (fill_time) — fills only, no round-trip P&L;
#            strategy P&L / win-rate stay NULL until a per-strategy UAT
#            round-trip ledger exists (qr_etl's domain — never derived here).
# Read-only; a book with no data returns nulls, never a misleading $0.
# =============================================================================

def _book_overview_sim_paper(db, exec_mode):
    """Shared query block for the two synthetic-ledger books (mode-scoped via
    the registry join so SIM and PAPER stay distinct). exec_mode is a fixed
    internal literal ('SIMULATION' | 'PAPER'), never request input."""
    closed_row = safe_query_one(db, f"""
        SELECT COUNT(*) AS closed,
               COUNT(*) FILTER (WHERE t.pnl > 0) AS wins,
               SUM(t.pnl) AS cum_pnl,
               SUM(t.pnl) FILTER (
                   WHERE t.exit_date >= date_trunc('year', now())::date
               ) AS ytd_pnl,
               COUNT(*) FILTER (
                   WHERE t.exit_date >= date_trunc('year', now())::date
               ) AS ytd_trades
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        WHERE t.status = 'closed' AND (t.ticker IS NULL OR t.ticker != 'CASH')
    """, label=f"book_overview_{exec_mode}_closed")

    today_row = safe_query_one(db, f"""
        SELECT COUNT(*) AS trades, SUM(t.pnl) AS pnl
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        WHERE t.status = 'closed' AND t.exit_date = CURRENT_DATE
          AND (t.ticker IS NULL OR t.ticker != 'CASH')
    """, label=f"book_overview_{exec_mode}_today")

    open_row = safe_query_one(db, f"""
        SELECT COUNT(*) AS n
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        JOIN gold.strategy_paper_monitoring m
          ON m.strategy_id = t.strategy_id AND m.is_active
        WHERE t.status = 'open' AND (t.ticker IS NULL OR t.ticker != 'CASH')
    """, label=f"book_overview_{exec_mode}_open")

    # YTD cumulative realized P&L in dollars, carry-forward over quiet days.
    daily_rows = safe_query(db, f"""
        SELECT t.exit_date AS d, SUM(t.pnl) AS pnl
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        WHERE t.status = 'closed' AND t.exit_date IS NOT NULL
          AND t.exit_date >= date_trunc('year', now())::date
          AND (t.ticker IS NULL OR t.ticker != 'CASH')
        GROUP BY t.exit_date ORDER BY t.exit_date
    """, label=f"book_overview_{exec_mode}_daily")

    # Best-performing strategies: all-time realized ranking with the YTD
    # slice alongside, so a strategy that won big last year but is flat this
    # year reads honestly in both columns.
    strat_rows = safe_query(db, f"""
        SELECT t.strategy_id, r.name,
               COUNT(*) AS closed,
               COUNT(*) FILTER (WHERE t.pnl > 0) AS wins,
               SUM(t.pnl) AS cum_pnl,
               SUM(t.pnl) FILTER (
                   WHERE t.exit_date >= date_trunc('year', now())::date
               ) AS ytd_pnl
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        WHERE t.status = 'closed' AND (t.ticker IS NULL OR t.ticker != 'CASH')
        GROUP BY t.strategy_id, r.name
        ORDER BY SUM(t.pnl) DESC NULLS LAST
        LIMIT 6
    """, label=f"book_overview_{exec_mode}_strats")

    # Worst-performing strategies: identical ranking, ascending.
    strat_rows_worst = safe_query(db, f"""
        SELECT t.strategy_id, r.name,
               COUNT(*) AS closed,
               COUNT(*) FILTER (WHERE t.pnl > 0) AS wins,
               SUM(t.pnl) AS cum_pnl,
               SUM(t.pnl) FILTER (
                   WHERE t.exit_date >= date_trunc('year', now())::date
               ) AS ytd_pnl
        FROM gold.paper_trades_synthetic t
        JOIN gold.strategy_registry r
          ON r.strategy_id = t.strategy_id AND r.execution_mode = '{exec_mode}'
        WHERE t.status = 'closed' AND (t.ticker IS NULL OR t.ticker != 'CASH')
        GROUP BY t.strategy_id, r.name
        ORDER BY SUM(t.pnl) ASC NULLS LAST
        LIMIT 6
    """, label=f"book_overview_{exec_mode}_strats_worst")

    closed = int(closed_row.closed or 0) if closed_row else 0
    wins = int(closed_row.wins or 0) if closed_row else 0
    cum_pnl = float(closed_row.cum_pnl) if closed_row and closed_row.cum_pnl is not None else None
    ytd_trades = int(closed_row.ytd_trades or 0) if closed_row else 0
    ytd_pnl = float(closed_row.ytd_pnl) if closed_row and closed_row.ytd_pnl is not None else None
    today = None
    if today_row and today_row.trades:
        today = {"trades": int(today_row.trades), "pnl": float(today_row.pnl or 0)}

    by_day = {r.d: float(r.pnl or 0) for r in daily_rows}
    ytd_curve = []
    if by_day:
        start = datetime.now(timezone.utc).date().replace(month=1, day=1)
        end = datetime.now(timezone.utc).date()
        run = 0.0
        d = start
        while d <= end:
            run += by_day.get(d, 0.0)
            ytd_curve.append({"d": str(d), "cum": round(run, 2)})
            d += timedelta(days=1)

    def _strat_row(r):
        return {
            "strategy_id": r.strategy_id,
            "name": r.name or r.strategy_id,
            "closed_trades": int(r.closed or 0),
            "win_rate": round(int(r.wins or 0) / int(r.closed) * 100, 1) if r.closed else None,
            "cum_pnl": round(float(r.cum_pnl), 2) if r.cum_pnl is not None else None,
            "ytd_pnl": round(float(r.ytd_pnl), 2) if r.ytd_pnl is not None else None,
        }

    strategies = [_strat_row(r) for r in strat_rows]
    worst_strategies = [_strat_row(r) for r in strat_rows_worst]

    return {
        "stats": {
            "closed_trades": closed,
            "win_rate": round(wins / closed * 100, 1) if closed else None,
            "open_trades": int(open_row.n or 0) if open_row else 0,
            "today": today,
            "ytd_pnl": round(ytd_pnl, 2) if ytd_pnl is not None else None,
            "ytd_trades": ytd_trades,
            "cum_pnl": round(cum_pnl, 2) if cum_pnl is not None else None,
        },
        "ytd_curve": ytd_curve,
        "top_strategies": strategies,
        "worst_strategies": worst_strategies,
        "strategy_metric": "realized_pnl",
    }


def _book_overview_uat(db):
    """UAT book: broker-rehearsal fills only (gold.paper_uat_fills has no
    per-fill pnl — they are fills, not round-trips). Strategy ranking is by
    fill activity, clearly flagged; P&L / win-rate stay NULL."""
    agg = safe_query_one(db, """
        SELECT COUNT(*) AS fills,
               COUNT(*) FILTER (WHERE fill_time::date = CURRENT_DATE) AS fills_today,
               COUNT(*) FILTER (WHERE fill_time >= date_trunc('year', now())) AS fills_ytd,
               COUNT(DISTINCT strategy_id) AS strategies,
               MAX(fill_time) AS last_fill_at
        FROM gold.paper_uat_fills
    """, label="book_overview_uat_agg")

    strat_rows = safe_query(db, """
        SELECT f.strategy_id, r.name,
               COUNT(*) AS fills,
               COUNT(DISTINCT f.symbol) AS symbols,
               MAX(f.fill_time) AS last_fill_at
        FROM gold.paper_uat_fills f
        LEFT JOIN gold.strategy_registry r ON r.strategy_id = f.strategy_id
        GROUP BY f.strategy_id, r.name
        ORDER BY COUNT(*) DESC
        LIMIT 6
    """, label="book_overview_uat_strats")

    strategies = [{
        "strategy_id": r.strategy_id,
        "name": r.name or r.strategy_id,
        "fills": int(r.fills or 0),
        "symbols": int(r.symbols or 0),
        "last_fill_at": r.last_fill_at.isoformat() if r.last_fill_at else None,
        "closed_trades": None, "win_rate": None, "cum_pnl": None, "ytd_pnl": None,
    } for r in strat_rows]

    return {
        "stats": {
            "closed_trades": None,
            "win_rate": None,
            "open_trades": None,
            "today": ({"trades": int(agg.fills_today), "pnl": None}
                      if agg and agg.fills_today else None),
            "ytd_pnl": None,
            "ytd_trades": int(agg.fills_ytd or 0) if agg else 0,
            "cum_pnl": None,
            "total_fills": int(agg.fills or 0) if agg else 0,
            "last_fill_at": agg.last_fill_at.isoformat() if agg and agg.last_fill_at else None,
        },
        "ytd_curve": [],
        "top_strategies": strategies,
        "strategy_metric": "fills",
    }


@router.get("/book-overview")
def get_book_overview(book: str = "sim", db: Session = Depends(get_db)):
    """Execution-tab per-book overview: stats, YTD cumulative realized P&L
    (dollars), and the best-performing strategies for SIM / PAPER / UAT."""
    if book == "paper_uat":
        book = "uat"
    if book not in ("sim", "paper", "uat"):
        raise HTTPException(status_code=400, detail="book must be sim, paper or uat")
    if book == "uat":
        out = _book_overview_uat(db)
    else:
        out = _book_overview_sim_paper(db, "SIMULATION" if book == "sim" else "PAPER")
    return {"book": book, **out, "as_of": _now_iso()}


class ManualOrderRequest(BaseModel):
    book: str
    ticker: str
    market: str
    asset: str
    side: str
    qty: float
    entry: float
    limit: Optional[float] = None
    note: Optional[str] = None


@router.post("/manual-order", status_code=201)
def post_manual_order(payload: ManualOrderRequest, db: Session = Depends(get_db)):
    """The only platform write endpoint — a manual order ticket. Persists to gold.manual_orders."""
    if payload.qty <= 0:
        raise HTTPException(status_code=422, detail="qty must be > 0")
    if payload.entry <= 0 and payload.limit is None:
        raise HTTPException(status_code=422, detail="entry or limit must be > 0")
    if payload.asset == "STOCK" and payload.market not in ("US", "HK"):
        raise HTTPException(status_code=422, detail="market must be US or HK for STOCK orders")
    if payload.asset not in ("STOCK", "CRYPTO", "FX"):
        raise HTTPException(status_code=422, detail="asset must be one of STOCK, CRYPTO, FX")

    if payload.book == "live":
        mode_result = db.execute(text(
            "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
        )).fetchone()
        current_mode = mode_result.value if mode_result else "SIMULATION"
        if current_mode != "LIVE_TRADING":
            raise HTTPException(status_code=409, detail={"error": "mode_mismatch"})

    order_id = f"m{int(time.time() * 1000)}"
    row = safe_query_one(db, """
        INSERT INTO gold.manual_orders
            (order_id, book, ticker, market, asset_class, side, qty, entry_price, limit_price, note, created_by)
        VALUES (:order_id, :book, :ticker, :market, :asset, :side, :qty, :entry, :limit, :note, 'workspace')
        RETURNING order_id, book, ticker, qty, entry_price, created_at
    """, {
        "order_id": order_id, "book": payload.book, "ticker": payload.ticker, "market": payload.market,
        "asset": payload.asset, "side": payload.side, "qty": payload.qty, "entry": payload.entry,
        "limit": payload.limit, "note": payload.note,
    }, label="manual_order_insert")
    if row is None:
        raise HTTPException(status_code=503, detail="gold.manual_orders is not provisioned yet")
    db.commit()
    m = row._mapping
    return {
        "order_id": m["order_id"], "status": "accepted", "book": m["book"], "ticker": m["ticker"],
        "filled_qty": float(m["qty"]), "avg_price": float(m["entry_price"]),
        "created_at": m["created_at"].isoformat() if m["created_at"] else _now_iso(),
    }


@router.get("/orders")
def get_execution_orders(db: Session = Depends(get_db)):
    """Order Queue panel — pending/working orders en route to IBKR."""
    rows = safe_query(db, """
        SELECT order_id, ticker, side, qty, order_type AS type, status, venue, submitted_at AS ts
        FROM consumption.execution_order_queue ORDER BY submitted_at DESC
    """, label="execution_orders")
    data = [{
        "order_id": r.order_id, "ticker": r.ticker, "side": r.side, "qty": float(r.qty) if r.qty is not None else None,
        "type": r.type, "status": r.status, "venue": r.venue, "ts": r.ts.isoformat() if r.ts else None,
    } for r in rows]
    return {"data": data, "as_of": _now_iso() if data else None}


@router.get("/fills")
def get_execution_fills(db: Session = Depends(get_db)):
    """Fills & Reconciliation panel — executions matched against the broker statement."""
    rows = safe_query(db, """
        SELECT fill_id, order_id, ticker, qty, price, broker_ref, matched, filled_at AS ts
        FROM consumption.execution_fills ORDER BY filled_at DESC
    """, label="execution_fills")
    data = [{
        "fill_id": r.fill_id, "order_id": r.order_id, "ticker": r.ticker,
        "qty": float(r.qty) if r.qty is not None else None, "price": float(r.price) if r.price is not None else None,
        "broker_ref": r.broker_ref, "matched": bool(r.matched), "ts": r.ts.isoformat() if r.ts else None,
    } for r in rows]
    return {"data": data, "as_of": _now_iso() if data else None}


@router.get("/gateway")
def get_execution_gateway(db: Session = Depends(get_db)):
    """IBKR Gateway panel — connection state, latency, account, plus the current global_mode.

    Per-session truth: top-level fields stay the primary session (backwards
    compatible); `sessions` carries one entry per gateway session (primary, uat)
    combining the DB heartbeat (consumption.ib_gateway_state_sessions) with the
    backend's live in-process session state.
    """
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    global_mode = mode_result.value if mode_result else "SIMULATION"

    row_list = safe_query(db, """
        SELECT connected, host, port, latency_ms, account, last_heartbeat
        FROM consumption.ib_gateway_state LIMIT 1
    """, label="execution_gateway")
    primary = {"connected": None, "host": None, "port": None, "latency_ms": None,
               "account": None, "last_heartbeat": None}
    if row_list:
        r = row_list[0]
        primary = {
            "connected": r.connected, "host": r.host, "port": r.port,
            "latency_ms": r.latency_ms, "account": r.account,
            "last_heartbeat": r.last_heartbeat.isoformat() if r.last_heartbeat else None,
        }

    # Per-session DB heartbeat rows (primary + uat)
    sessions = {"primary": dict(primary)}
    session_rows = safe_query(db, """
        SELECT session, connected, host, port, latency_ms, account, last_heartbeat
        FROM consumption.ib_gateway_state_sessions
    """, label="execution_gateway_sessions")
    for r in session_rows:
        sessions[r.session] = {
            "connected": r.connected, "host": r.host, "port": r.port,
            "latency_ms": r.latency_ms, "account": r.account,
            "last_heartbeat": r.last_heartbeat.isoformat() if r.last_heartbeat else None,
        }

    # Live in-process truth per session (no side effects — never starts threads)
    live_state = {}
    try:
        from app.services.ib_service import ib_quant_service
        live_state["primary"] = {
            "connected": ib_quant_service.is_connected,
            "host": ib_quant_service.host, "port": ib_quant_service.port,
            "client_id": ib_quant_service.client_id,
            "account": ib_quant_service.account,
        }
    except Exception as e:
        live_state["primary"] = {"connected": None, "error": str(e)}
    try:
        from app.services.ib_service import ib_uat_service
        live_state["uat"] = {
            "connected": ib_uat_service.is_connected,
            "host": ib_uat_service.host, "port": ib_uat_service.port,
            "client_id": ib_uat_service.client_id,
            "account": ib_uat_service.account,
        }
    except Exception as e:
        live_state["uat"] = {"connected": None, "error": str(e)}

    for name, state in live_state.items():
        sessions.setdefault(name, {})
        sessions[name]["live"] = state

    return {
        **primary,
        "global_mode": global_mode,
        "sessions": sessions,
    }


@router.get("/limits")
def get_execution_limits(db: Session = Depends(get_db)):
    """Kill Switch & Limits panel — halt state + per-strategy capital caps."""
    rows = safe_query(db, """
        SELECT halt_phrase_set, global_halt, strategy_id, capital_cap_pct, used_pct
        FROM gold.risk_limits
    """, label="execution_limits")
    global_row = next((r for r in rows if r.strategy_id is None), None)
    per_strategy = [{
        "strategy_id": r.strategy_id,
        "capital_cap_pct": float(r.capital_cap_pct) if r.capital_cap_pct is not None else None,
        "used_pct": float(r.used_pct) if r.used_pct is not None else None,
    } for r in rows if r.strategy_id is not None]
    return {
        "halt_phrase_set": bool(global_row.halt_phrase_set) if global_row else False,
        "global_halt": bool(global_row.global_halt) if global_row else False,
        "per_strategy": per_strategy,
    }


# =============================================================================
# Manual book (Execution > Manual tab, 2026-09-25 goal): discretionary
# positions entered by hand — tracked in gold.manual_positions, marked with
# the SAME quote source as the Paper book (silver.unified_prices latest
# close, fallback gold.daily_ohlcv). No IBKR routing anywhere in this
# section: add writes a row, close writes exit legs. Siloed by design —
# manual positions do NOT feed Command aggregates or NAV.
# =============================================================================

def _latest_mark(db, symbol):
    """Latest close for a symbol — identical source/fallback order as the
    paper book's close-position mark."""
    mark = db.execute(text("""
        SELECT close, date FROM silver.unified_prices
        WHERE ticker = :t AND close IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """), {"t": symbol}).fetchone()
    if mark:
        return float(mark.close), str(mark.date), "silver.unified_prices"
    mark = db.execute(text("""
        SELECT close, date FROM gold.daily_ohlcv
        WHERE ticker = :t AND close IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """), {"t": symbol}).fetchone()
    if mark:
        return float(mark.close), str(mark.date), "gold.daily_ohlcv"
    return None, None, None


def _signed_pnl(side, entry, exit_or_mark, qty):
    sign = -1.0 if (side or "").upper() == "SHORT" else 1.0
    return sign * (float(exit_or_mark) - float(entry)) * float(qty)


@router.get("/manual/positions")
def get_manual_positions(db: Session = Depends(get_db)):
    """Manual book — open positions marked to the latest close + closed
    positions with realized P&L, plus the summary strip figures."""
    rows = safe_query(db, """
        SELECT id, symbol, market, asset_type, side, qty,
               entry_price, entry_date, exit_price, exit_date, realized_pnl,
               notes, created_at
        FROM gold.manual_positions
        ORDER BY (exit_date IS NULL) DESC, entry_date DESC, id DESC
    """, label="manual_positions_list")

    open_positions, closed_positions = [], []
    tot_unreal = 0.0
    for r in rows:
        m = r._mapping
        base = {
            "id": m["id"],
            "symbol": m["symbol"],
            "market": m["market"],
            "asset_type": m["asset_type"],
            "side": m["side"],
            "qty": float(m["qty"]),
            "entry_price": float(m["entry_price"]),
            "entry_date": str(m["entry_date"]),
            "held_days": (datetime.now(timezone.utc).date() - m["entry_date"]).days if m["entry_date"] else None,
            "notes": m["notes"],
        }
        if m["exit_date"] is None:
            mark, mark_date, mark_source = _latest_mark(db, m["symbol"])
            unreal = _signed_pnl(m["side"], m["entry_price"], mark, m["qty"]) if mark is not None else None
            if unreal is not None:
                tot_unreal += unreal
            open_positions.append({
                **base,
                "current_price": mark,
                "current_price_date": mark_date,
                "price_source": mark_source,
                "unrealized_pnl": round(unreal, 2) if unreal is not None else None,
                "market_value": round(mark * float(m["qty"]), 2) if mark is not None else None,
            })
        else:
            closed_positions.append({
                **base,
                "exit_price": float(m["exit_price"]) if m["exit_price"] is not None else None,
                "exit_date": str(m["exit_date"]),
                "realized_pnl": round(float(m["realized_pnl"]), 2) if m["realized_pnl"] is not None else None,
            })

    agg = safe_query_one(db, """
        SELECT COUNT(*) FILTER (WHERE exit_date IS NOT NULL) AS closed,
               COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND realized_pnl > 0) AS wins,
               SUM(realized_pnl) AS cum_pnl,
               SUM(realized_pnl) FILTER (WHERE exit_date >= date_trunc('year', now())::date) AS ytd_pnl,
               COUNT(*) FILTER (WHERE exit_date = CURRENT_DATE) AS today_trades,
               SUM(realized_pnl) FILTER (WHERE exit_date = CURRENT_DATE) AS today_pnl
        FROM gold.manual_positions
    """, label="manual_positions_summary")

    # Per-market aggregates (2026-09-25; CN added 2026-09-26): each book
    # marks in its own currency (US=USD, HK=HKD, CN=CNY) — per-market
    # summaries keep each book in its native currency so performance is
    # evaluated without silent FX mixing.
    per_market_rows = safe_query(db, """
        SELECT market,
               COUNT(*) FILTER (WHERE exit_date IS NULL) AS open,
               COUNT(*) FILTER (WHERE exit_date IS NOT NULL) AS closed,
               COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND realized_pnl > 0) AS wins,
               SUM(realized_pnl) AS cum_pnl,
               SUM(realized_pnl) FILTER (WHERE exit_date >= date_trunc('year', now())::date) AS ytd_pnl,
               COUNT(*) FILTER (WHERE exit_date = CURRENT_DATE) AS today_trades,
               SUM(realized_pnl) FILTER (WHERE exit_date = CURRENT_DATE) AS today_pnl
        FROM gold.manual_positions
        GROUP BY market
    """, label="manual_positions_by_market")

    unreal_by_market = {}
    for p in open_positions:
        if p["unrealized_pnl"] is not None:
            unreal_by_market[p["market"]] = round(unreal_by_market.get(p["market"], 0.0) + p["unrealized_pnl"], 2)

    # Monthly realized P&L by exit month per market (2026-09-26) — powers the
    # per-market heatmap on the Manual tab. Keyed "YYYY-MM"; unrealized P&L
    # is never mixed in (realized only, native currency).
    monthly_rows = safe_query(db, """
        SELECT market,
               EXTRACT(YEAR FROM exit_date)::int AS yr,
               EXTRACT(MONTH FROM exit_date)::int AS mo,
               SUM(realized_pnl) AS pnl,
               COUNT(*) AS n
        FROM gold.manual_positions
        WHERE exit_date IS NOT NULL
        GROUP BY market, EXTRACT(YEAR FROM exit_date), EXTRACT(MONTH FROM exit_date)
    """, label="manual_positions_monthly")
    monthly_by_market = {}
    for r in monthly_rows:
        m = r._mapping
        monthly_by_market.setdefault(m["market"], {})[f"{m['yr']}-{m['mo']:02d}"] = {
            "pnl": round(float(m["pnl"]), 2) if m["pnl"] is not None else None,
            "n": int(m["n"]),
        }

    # Unrealized P&L by month-end mark per market (2026-09-26, per user): for
    # each OPEN position, every calendar month from entry month to the current
    # month is marked at that month's last close (current month = latest
    # close), side-signed vs entry price, summed per market. Same quote
    # source/fallback as the live marks; native currency, never FX-mixed.
    unreal_monthly_by_market = {}
    if open_positions:
        tickers = sorted({p["symbol"] for p in open_positions})
        month_marks = {}
        for tbl, lbl in (("silver.unified_prices", "manual_monthly_marks_silver"),
                         ("gold.daily_ohlcv", "manual_monthly_marks_gold")):
            for r in safe_query(db, f"""
                SELECT DISTINCT ON (ticker, date_trunc('month', date))
                       ticker, to_char(date_trunc('month', date), 'YYYY-MM') AS mo, close
                FROM {tbl}
                WHERE ticker = ANY(:tickers) AND close IS NOT NULL
                ORDER BY ticker, date_trunc('month', date), date DESC
            """, {"tickers": tickers}, label=lbl):
                month_marks.setdefault((r._mapping["ticker"], r._mapping["mo"]),
                                       float(r._mapping["close"]))
        today = datetime.now(timezone.utc).date()
        cur_ym = f"{today.year}-{today.month:02d}"
        for p in open_positions:
            if not p["entry_date"]:
                continue
            y, m = int(p["entry_date"][:4]), int(p["entry_date"][5:7])
            while (y, m) <= (today.year, today.month):
                ym = f"{y}-{m:02d}"
                mark = p["current_price"] if ym == cur_ym else month_marks.get((p["symbol"], ym))
                if mark is not None:
                    pnl = _signed_pnl(p["side"], p["entry_price"], mark, p["qty"])
                    mkt_agg = unreal_monthly_by_market.setdefault(p["market"], {})
                    mkt_agg[ym] = round(mkt_agg.get(ym, 0.0) + pnl, 2)
                m += 1
                if m == 13:
                    y, m = y + 1, 1

    summary_by_market = {}
    for r in per_market_rows:
        m = r._mapping
        mk = m["market"]
        cl = int(m["closed"] or 0)
        w = int(m["wins"] or 0)
        summary_by_market[mk] = {
            "open": int(m["open"] or 0),
            "closed": cl,
            "win_rate": round(w / cl * 100, 1) if cl else None,
            "ytd_pnl": round(float(m["ytd_pnl"]), 2) if m["ytd_pnl"] is not None else None,
            "cum_pnl": round(float(m["cum_pnl"]), 2) if m["cum_pnl"] is not None else None,
            "today": ({"trades": int(m["today_trades"]), "pnl": round(float(m["today_pnl"] or 0), 2)}
                      if m["today_trades"] else None),
            "unrealized_pnl": unreal_by_market.get(mk, 0.0),
        }

    closed_n = int(agg.closed or 0) if agg else 0
    wins = int(agg.wins or 0) if agg else 0
    summary = {
        "open": len(open_positions),
        "closed": closed_n,
        "win_rate": round(wins / closed_n * 100, 1) if closed_n else None,
        "ytd_pnl": round(float(agg.ytd_pnl), 2) if agg and agg.ytd_pnl is not None else None,
        "cum_pnl": round(float(agg.cum_pnl), 2) if agg and agg.cum_pnl is not None else None,
        "today": ({"trades": int(agg.today_trades), "pnl": round(float(agg.today_pnl or 0), 2)}
                  if agg and agg.today_trades else None),
        "unrealized_pnl": round(tot_unreal, 2),
    }
    return {"open": open_positions, "closed": closed_positions,
            "summary": summary, "summary_by_market": summary_by_market,
            "monthly_by_market": monthly_by_market,
            "unrealized_monthly_by_market": unreal_monthly_by_market,
            "as_of": _now_iso()}


class ManualPositionAdd(BaseModel):
    symbol: str
    market: str
    asset_type: Optional[str] = "STOCK"
    side: str
    qty: float
    entry_price: float
    entry_date: str
    notes: Optional[str] = None


@router.post("/manual/positions", status_code=201)
def post_manual_position(payload: ManualPositionAdd, db: Session = Depends(get_db)):
    """Add a discretionary position. Row insert only — never routes to IBKR."""
    symbol = payload.symbol.strip().upper()
    side = payload.side.strip().upper()
    market = payload.market.strip().upper()
    asset_type = (payload.asset_type or "STOCK").strip().upper()
    if not symbol:
        raise HTTPException(status_code=422, detail="symbol is required")
    if side not in ("LONG", "SHORT"):
        raise HTTPException(status_code=422, detail="side must be LONG or SHORT")
    if market not in ("US", "HK", "CN"):
        raise HTTPException(status_code=422, detail="market must be US, HK or CN")
    if asset_type not in ("STOCK", "CRYPTO", "FX"):
        raise HTTPException(status_code=422, detail="asset_type must be STOCK, CRYPTO or FX")
    if payload.qty <= 0:
        raise HTTPException(status_code=422, detail="qty must be > 0")
    if payload.entry_price <= 0:
        raise HTTPException(status_code=422, detail="entry_price must be > 0")
    try:
        entry_date = datetime.strptime(payload.entry_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="entry_date must be YYYY-MM-DD")
    if entry_date > datetime.now(timezone.utc).date():
        raise HTTPException(status_code=422, detail="entry_date cannot be in the future")

    row = safe_query_one(db, """
        INSERT INTO gold.manual_positions
            (symbol, market, asset_type, side, qty, entry_price, entry_date, notes, created_by)
        VALUES (:symbol, :market, :asset_type, :side, :qty, :entry_price, :entry_date, :notes, 'workspace')
        RETURNING id
    """, {
        "symbol": symbol, "market": market, "asset_type": asset_type, "side": side,
        "qty": payload.qty, "entry_price": payload.entry_price,
        "entry_date": entry_date, "notes": (payload.notes or None),
    }, label="manual_position_insert")
    if row is None:
        raise HTTPException(status_code=503, detail="gold.manual_positions is not provisioned yet")
    db.commit()
    return {"id": row._mapping["id"], "status": "accepted", "symbol": symbol, "as_of": _now_iso()}


class ManualPositionClose(BaseModel):
    exit_price: float
    exit_date: str
    notes: Optional[str] = None


@router.post("/manual/positions/{position_id}/close")
def close_manual_position(position_id: int, payload: ManualPositionClose, db: Session = Depends(get_db)):
    """Close a manual position with exit legs; realized P&L computed server-side
    (side-signed). Update only — no order routing."""
    if payload.exit_price <= 0:
        raise HTTPException(status_code=422, detail="exit_price must be > 0")
    try:
        exit_date = datetime.strptime(payload.exit_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="exit_date must be YYYY-MM-DD")

    cur = safe_query_one(db, """
        SELECT id, symbol, side, qty, entry_price, entry_date
        FROM gold.manual_positions WHERE id = :id
    """, {"id": position_id}, label="manual_position_get")
    if cur is None:
        raise HTTPException(status_code=404, detail=f"No manual position id={position_id}")
    m = cur._mapping
    if m["entry_date"] and exit_date < m["entry_date"]:
        raise HTTPException(status_code=422, detail="exit_date cannot be before entry_date")

    realized = _signed_pnl(m["side"], m["entry_price"], payload.exit_price, m["qty"])
    note_sql = "notes = COALESCE(:notes, notes)," if payload.notes else ""
    updated = safe_query_one(db, f"""
        UPDATE gold.manual_positions
        SET exit_price = :exit_price, exit_date = :exit_date, realized_pnl = :realized,
            {note_sql} updated_at = now()
        WHERE id = :id AND exit_date IS NULL
        RETURNING id
    """, {
        "exit_price": payload.exit_price, "exit_date": exit_date,
        "realized": realized, "notes": payload.notes, "id": position_id,
    }, label="manual_position_close")
    if updated is None:
        raise HTTPException(status_code=409, detail="Position is already closed")
    db.commit()
    return {"id": position_id, "status": "closed", "realized_pnl": round(realized, 2), "as_of": _now_iso()}


@router.delete("/manual/positions/{position_id}")
def purge_manual_position(position_id: int, db: Session = Depends(get_db)):
    """Purge a manual position row entirely (2026-09-29, per user — testing
    tickers): DELETE removes the ledger row, so it is never counted as open
    OR closed (closed stats / monthly heatmap / win rate all ignore it).
    Hard delete by design — not an undo-close."""
    deleted = safe_query_one(db, """
        DELETE FROM gold.manual_positions WHERE id = :id RETURNING id
    """, {"id": position_id}, label="manual_position_purge")
    if deleted is None:
        raise HTTPException(status_code=404, detail=f"No manual position id={position_id}")
    db.commit()
    return {"id": position_id, "status": "purged", "as_of": _now_iso()}


class KillSwitchRequest(BaseModel):
    phrase: str


@router.post("/kill-switch")
def post_kill_switch(payload: KillSwitchRequest, db: Session = Depends(get_db)):
    """Fire the global halt — cancels working orders and flattens the book. Writes gold.audit_events."""
    if payload.phrase.strip().upper() != "HALT ALL":
        raise HTTPException(status_code=422, detail="confirmation phrase does not match")

    updated = safe_query(db, """
        UPDATE gold.risk_limits SET global_halt = true WHERE strategy_id IS NULL RETURNING strategy_id
    """, label="kill_switch_update")
    safe_query(db, """
        INSERT INTO gold.audit_events (event_type, detail, created_at)
        VALUES ('execution.kill_switch', 'Global kill switch triggered from workspace', NOW())
    """, label="kill_switch_audit")
    db.commit()
    return {"status": "halted" if updated else "acknowledged", "as_of": _now_iso()}
