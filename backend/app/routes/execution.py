"""Execution mode endpoints — global mode, simulation reset."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/execution", tags=["execution"])

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
            FROM gold.paper_strategies WHERE status = 'ACTIVE'
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
        count = db.execute(text("SELECT COUNT(*) as cnt FROM gold.paper_strategies")).fetchone()
        trades = db.execute(text("SELECT COUNT(*) as cnt FROM gold.trade_executions")).fetchone()
        positions_count = count.cnt if count else 0
        trades_count = trades.cnt if trades else 0

        db.execute(text("DELETE FROM gold.paper_strategies"))
        db.execute(text("DELETE FROM gold.trade_executions"))
        try: db.execute(text("DELETE FROM consumption.Portfolio_Positions_Current"))
        except: pass
        try: db.execute(text("DELETE FROM consumption.Performance_Trades_History"))
        except: pass

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
