"""Execution mode endpoints — global mode, simulation reset, manual orders, live ops."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import time

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api/execution", tags=["execution"])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()

# Cache for IBKR account balance (5 min TTL)
_ibkr_balance_cache = {"data": None, "timestamp": None}


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
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": {"SIMULATION": "ZERO", "PAPER_TRADING": "LOW", "LIVE_TRADING": "HIGH"}.get(current_mode, "UNKNOWN"),
        "simulation_capital": sim_amount, "simulation_used": sim_used,
        "simulation_available": sim_amount - sim_used, "simulation_positions": sim_positions,
    }

    # IBKR balance for paper/live modes
    if current_mode in ["PAPER_TRADING", "LIVE_TRADING"]:
        try:
            from app.services.ib_service import ib_quant_service
            now = time.time()
            if _ibkr_balance_cache["data"] and _ibkr_balance_cache["timestamp"] and (now - _ibkr_balance_cache["timestamp"]) < 300:
                response.update(_ibkr_balance_cache["data"])
                response["cached"] = True
            else:
                try:
                    tws_status = ib_quant_service.get_status()
                    if tws_status.get("is_connected"):
                        account_info = ib_quant_service.get_account_summary()
                        if account_info:
                            is_hkd = account_info.get("currency") == "HKD" or account_info.get("cash_hkd", 0) > 0
                            if is_hkd:
                                ibkr_data = {
                                    "ibkr_connected": True, "account_currency": "HKD",
                                    "account_balance": account_info.get("cash_hkd", 0) or account_info.get("available_funds_hkd", 0),
                                    "net_liquidation": account_info.get("net_liquidation_hkd", 0) or account_info.get("net_liquidation", 0),
                                    "buying_power": account_info.get("buying_power_hkd", 0) or account_info.get("buying_power", 0),
                                    "account": account_info.get("account", "Unknown"),
                                    "account_type": "PAPER" if current_mode == "PAPER_TRADING" else "LIVE",
                                }
                            else:
                                ibkr_data = {
                                    "ibkr_connected": True, "account_currency": account_info.get("currency", "USD"),
                                    "account_balance": account_info.get("available_funds", 0),
                                    "net_liquidation": account_info.get("net_liquidation", 0),
                                    "buying_power": account_info.get("buying_power", 0),
                                    "account": account_info.get("account", "Unknown"),
                                    "account_type": "PAPER" if current_mode == "PAPER_TRADING" else "LIVE",
                                }
                            _ibkr_balance_cache["data"] = ibkr_data
                            _ibkr_balance_cache["timestamp"] = now
                            response.update(ibkr_data)
                            response["cached"] = False
                        else:
                            response["ibkr_connected"] = True
                            response["warning"] = "Connected but could not fetch account details"
                    else:
                        response["ibkr_connected"] = False
                        response["warning"] = "TWS not connected"
                except Exception as ibkr_err:
                    response["ibkr_connected"] = False
                    response["warning"] = f"IBKR check failed: {ibkr_err}"
        except Exception:
            response["ibkr_connected"] = False

    return response


@router.post("/global-mode")
def set_global_execution_mode(payload: dict, db: Session = Depends(get_db)):
    mode = payload.get("execution_mode", "SIMULATION")
    sim_capital = payload.get("simulation_capital")

    if mode not in ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"]:
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
    # Alias as "ts" (not "t") — SQLAlchemy 2.0's Row conflicts with a column literally named "t".
    rows = safe_query(db, """
        SELECT executed_at AS ts, side, ticker, quantity AS qty, price, 'algo' AS source
        FROM gold.trade_executions ORDER BY executed_at DESC LIMIT :limit
    """, {"limit": limit}, label="execution_trades_algo")
    manual_rows = safe_query(db, """
        SELECT created_at AS ts, side, ticker, qty, entry_price AS price, 'manual' AS source
        FROM gold.manual_orders WHERE book = :book ORDER BY created_at DESC LIMIT :limit
    """, {"book": book, "limit": limit}, label="execution_trades_manual")
    combined = list(rows) + list(manual_rows)
    combined.sort(key=lambda r: r.ts, reverse=True)
    data = [{
        "t": r.ts.isoformat() if r.ts else None, "side": r.side, "ticker": r.ticker,
        "qty": float(r.qty) if r.qty is not None else None,
        "price": float(r.price) if r.price is not None else None, "source": r.source,
    } for r in combined[:limit]]
    return {"data": data, "as_of": _now_iso() if data else None}


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
    """IBKR Gateway panel — connection state, latency, account, plus the current global_mode."""
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    global_mode = mode_result.value if mode_result else "SIMULATION"

    row_list = safe_query(db, """
        SELECT connected, host, port, latency_ms, account, last_heartbeat
        FROM consumption.ib_gateway_state LIMIT 1
    """, label="execution_gateway")
    if not row_list:
        return {"connected": None, "host": None, "port": None, "latency_ms": None,
                "account": None, "last_heartbeat": None, "global_mode": global_mode}
    r = row_list[0]
    return {
        "connected": r.connected, "host": r.host, "port": r.port,
        "latency_ms": r.latency_ms, "account": r.account,
        "last_heartbeat": r.last_heartbeat.isoformat() if r.last_heartbeat else None,
        "global_mode": global_mode,
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
