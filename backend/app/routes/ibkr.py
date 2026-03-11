"""IBKR endpoints — TWS/Web status, connect, place order, sync."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import time

from app.dependencies import get_db, logger
from app.services.ib_service import ib_quant_service
from app.services.ib_web_service import ib_web_service

router = APIRouter(prefix="/api", tags=["ibkr"])


# =============================================================================
# TWS API Status
# =============================================================================

@router.get("/ib/tws/status")
async def api_ib_tws_status():
    """Check TWS API (ib_insync) connection status."""
    try:
        return {
            "is_connected": ib_quant_service.is_connected,
            "host": ib_quant_service.host,
            "port": ib_quant_service.port,
            "client_id": ib_quant_service.client_id,
            "recommended": True,
        }
    except Exception as e:
        return {"error": str(e), "is_connected": False}


@router.post("/ib/tws/connect")
async def api_ib_tws_connect():
    """Manually trigger TWS API connection."""
    try:
        result = await ib_quant_service.connect()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/ib/web/status")
async def api_ib_web_status():
    """Check Web API (Client Portal) auth status."""
    try:
        is_auth = ib_web_service.check_auth()
        return {
            "is_authenticated": is_auth,
            "recommended": False,
            "note": "Use TWS API for automation. Web API for emergency only.",
        }
    except Exception as e:
        return {"error": str(e), "is_authenticated": False}


@router.post("/ib/place-order")
def place_ibkr_order(payload: dict, db: Session = Depends(get_db)):
    """Place an order through IBKR TWS API."""
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    symbol = payload.get("symbol", "AAPL")
    action = payload.get("action", "BUY")
    quantity = payload.get("quantity", 1)
    order_type = payload.get("order_type", "MKT")

    if current_mode == "SIMULATION":
        sim_capital = db.execute(text(
            "SELECT value FROM gold.platform_settings WHERE key = 'simulation_capital'"
        )).fetchone()
        sim_amount = float(sim_capital.value) if sim_capital else 100000

        sim_stats = db.execute(text(
            "SELECT COALESCE(SUM(capital), 0) as total_allocated FROM gold.paper_strategies WHERE status = 'ACTIVE'"
        )).fetchone()
        sim_used = float(sim_stats.total_allocated) if sim_stats else 0

        return {
            "success": True, "simulated": True,
            "message": f"SIMULATION: {action} {quantity} shares of {symbol} would be placed",
            "order_id": f"SIM_{int(time.time())}", "mode": current_mode,
            "simulation_balance": {"total": sim_amount, "used": sim_used, "available": sim_amount - sim_used},
        }

    try:
        order_result = ib_quant_service.place_order(
            symbol=symbol, action=action, quantity=int(quantity), order_type=order_type, account=None
        )
        if order_result and order_result.get("success"):
            return {
                "success": True, "order_id": order_result.get("order_id"),
                "status": order_result.get("status", "Submitted"), "mode": current_mode,
                "symbol": symbol, "action": action, "quantity": quantity,
                "message": f"{current_mode} order submitted: {action} {quantity} {symbol}",
            }
        else:
            raise HTTPException(status_code=500, detail=f"Order failed: {order_result.get('error', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error placing IBKR order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Velocity / Trading UI IBKR endpoints
# =============================================================================

@router.get("/velocity/ib/status")
async def get_ib_status():
    socket_ok = ib_quant_service.is_connected
    web_ok = ib_web_service.check_auth()
    return {
        "status": "Connected" if (socket_ok or web_ok) else "Disconnected",
        "socket": "Connected" if socket_ok else "Offline",
        "web": "Authenticated" if web_ok else "Unauthorized",
    }


@router.post("/velocity/ib/connect")
async def trigger_ib_connect():
    return await ib_quant_service.connect()


@router.post("/velocity/ib/sync-session")
async def sync_ib_session(request: Request):
    """Bridge browser IBKR session to backend."""
    cookies = request.cookies
    if cookies:
        ib_web_service.set_cookies(cookies)
        is_auth = ib_web_service.check_auth()
        return {"status": "Authenticated" if is_auth else "Unauthorized"}
    return {"status": "No Cookies Found"}


class TradeRequest(BaseModel):
    ticker: str
    action: str  # BUY, SELL
    quantity: float
    account_id: str


@router.post("/velocity/trade/execute")
async def api_execute_trade(trade: TradeRequest, db: Session = Depends(get_db)):
    """Manual execution via IBKR Web Service."""
    from app.db.session import Trade

    result = ib_web_service.execute_order(trade.account_id, trade.ticker, trade.action, trade.quantity)

    if result["status"] == "success":
        try:
            # Use DB price instead of yfinance
            price_row = db.execute(text("""
                SELECT close FROM silver.unified_prices
                WHERE ticker = :ticker ORDER BY date DESC LIMIT 1
            """), {"ticker": trade.ticker}).fetchone()
            price = float(price_row.close) if price_row else 0

            new_trade = Trade(
                ticker=trade.ticker, side=trade.action, price=price,
                quantity=trade.quantity, total_value=price * trade.quantity,
                strategy="MANUAL_OVERRIDE",
            )
            db.add(new_trade)
            db.commit()
        except Exception:
            pass
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])


# =============================================================================
# Sync positions to IBKR
# =============================================================================

@router.post("/positions/sync-to-ibkr")
def sync_positions_to_ibkr(payload: dict, db: Session = Depends(get_db)):
    """Sync paper positions to IBKR by placing real orders."""
    max_positions = payload.get("max_positions", 5)

    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    if current_mode == "SIMULATION":
        return {"success": False, "error": "Cannot sync in SIMULATION mode."}

    try:
        tws_status = ib_quant_service.get_status()
        if not tws_status.get("is_connected"):
            return {"success": False, "error": "IBKR not connected."}
    except Exception as e:
        return {"success": False, "error": f"Failed to check IBKR status: {e}"}

    result = db.execute(text("""
        SELECT id, strategy_id, ticker, capital, entry_price, execution_mode
        FROM gold.paper_strategies
        WHERE status = 'ACTIVE' AND invested_capital > 0
        AND (ibkr_order_id IS NULL OR ibkr_order_id = '')
        AND execution_mode = 'PAPER_TRADING'
        ORDER BY id LIMIT :limit
    """), {"limit": max_positions})

    positions = [{"id": r.id, "strategy_id": r.strategy_id, "ticker": r.ticker,
                  "capital": float(r.capital), "entry_price": float(r.entry_price) if r.entry_price else None}
                 for r in result]

    submitted, failed = [], []
    for pos in positions:
        ticker = pos["ticker"].replace("[", "").replace("]", "").replace('"', "").replace("'", "").strip()

        if "/" in ticker:
            failed.append({"ticker": ticker, "error": "FX pairs require special handling"})
            continue

        # Use DB price to calc quantity (no yfinance)
        if pos["entry_price"] and pos["entry_price"] > 0:
            quantity = int(pos["capital"] / pos["entry_price"])
        else:
            price_row = db.execute(text("""
                SELECT close FROM silver.unified_prices WHERE ticker = :t ORDER BY date DESC LIMIT 1
            """), {"t": ticker}).fetchone()
            current_price = float(price_row.close) if price_row else 100
            quantity = int(pos["capital"] / current_price)

        if quantity < 1:
            quantity = 1

        try:
            order_result = ib_quant_service.place_order(symbol=ticker, action="BUY", quantity=quantity, order_type="MKT", account=None)

            if order_result and order_result.get("success"):
                order_id = order_result.get("order_id", "UNKNOWN")
                fill_price = order_result.get("fill_price")
                entry_price = fill_price if fill_price else (pos["entry_price"] or 0)

                db.execute(text("""
                    UPDATE gold.paper_strategies
                    SET ibkr_order_id = :order_id, entry_price = :entry_price, current_price = :entry_price,
                        invested_capital = :capital, last_order_status = 'BUY_FILLED_IBKR', updated_at = NOW()
                    WHERE id = :id
                """), {"order_id": str(order_id), "id": pos["id"], "entry_price": entry_price, "capital": pos["capital"]})

                db.execute(text("""
                    INSERT INTO gold.trade_executions
                    (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, ibkr_order_id, executed_at)
                    VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'BUY', :qty, :price, 'FILLED_IBKR', :order_id, NOW())
                """), {"strategy_id": pos["strategy_id"], "ticker": ticker, "mode": current_mode,
                       "qty": quantity, "price": entry_price, "order_id": str(order_id)})

                submitted.append({"ticker": ticker, "quantity": quantity, "order_id": order_id,
                                  "fill_price": entry_price, "capital": pos["capital"]})
            else:
                failed.append({"ticker": ticker, "error": order_result.get("error", "Unknown") if order_result else "No result"})
        except Exception as e:
            failed.append({"ticker": ticker, "error": str(e)})

    db.commit()
    return {"success": True, "mode": current_mode, "total_pending": len(positions),
            "submitted": len(submitted), "failed": len(failed), "orders": submitted, "errors": failed}
