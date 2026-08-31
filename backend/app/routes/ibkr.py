"""IBKR endpoints — TWS/Web status, connect, place order, sync."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import time

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query_one
from app.services.ib_service import ib_quant_service, ib_uat_service
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


# =============================================================================
# UAT session endpoints — dedicated IBKR paper-account session
# =============================================================================

@router.get("/ib/tws/uat/status")
async def api_ib_tws_uat_status():
    """UAT paper session status (separate port + client from the primary session)."""
    try:
        return ib_uat_service.get_status()
    except Exception as e:
        return {"error": str(e), "is_connected": False, "session": "uat"}


@router.post("/ib/tws/uat/connect")
async def api_ib_tws_uat_connect():
    """Manually trigger the UAT paper session connection."""
    try:
        return await ib_uat_service.connect()
    except Exception as e:
        return {"status": "error", "session": "uat", "message": str(e)}


@router.get("/ib/tws/uat/positions")
async def api_ib_tws_uat_positions():
    """Real positions in the UAT paper account, straight from the gateway
    session (never the DB book). `connected=false` + `data=null` when the
    session is down so the UI can render a pending state instead of a
    misleading empty book."""
    from datetime import datetime, timezone
    try:
        positions = ib_uat_service.get_positions()
        connected = positions is not None
        return {
            "session": "uat",
            "connected": connected,
            "account": ib_uat_service.account,
            "account_type": "PAPER",
            "data": positions if connected else None,
            "count": len(positions) if connected else None,
            "as_of": datetime.now(timezone.utc).isoformat(),
            **({} if connected else {"message": "UAT paper session not connected — positions unavailable. Use POST /api/ib/tws/uat/connect."}),
        }
    except Exception as e:
        return {"session": "uat", "connected": False, "data": None, "error": str(e)}


@router.post("/ib/tws/uat/close-position")
def api_ib_tws_uat_close_position(payload: dict, db: Session = Depends(get_db)):
    """Close (flatten) one open position in the UAT paper account.

    Qty is resolved from the LIVE gateway portfolio — the client only names the
    symbol, so a stale UI can never over-close. Fires a real opposite-side MKT
    order on the UAT session ONLY (never falls back to primary/live) and books
    the fill into the uat blotter (gold.manual_orders — the designated
    platform write table).
    """
    symbol = (payload.get("symbol") or "").strip().upper()
    if not symbol:
        raise HTTPException(status_code=422, detail="symbol is required")

    if not ib_uat_service.is_connected:
        raise HTTPException(status_code=503,
                            detail="UAT paper session not connected — close has nowhere to fire. Use POST /api/ib/tws/uat/connect first.")

    positions = ib_uat_service.get_positions() or []
    pos = next((p for p in positions
                if (p.get("symbol") or "").upper() == symbol
                or (p.get("ticker") or "").upper() == symbol), None)
    if not pos or not pos.get("qty"):
        raise HTTPException(status_code=404,
                            detail=f"No open {symbol} position in the UAT paper account {ib_uat_service.account or ''}".strip())

    qty = float(pos["qty"])
    action = "SELL" if qty > 0 else "BUY"  # BUY covers a short position

    # Idempotency: if a working close order for this symbol already exists on
    # the UAT session (e.g. queued PreSubmitted outside market hours), do NOT
    # place a duplicate — a second SELL would overshoot into a short.
    for ot in (ib_uat_service.get_open_trades() or []):
        if (ot.get("symbol") or "").upper() == symbol and ot.get("action") == action \
                and ot.get("status") not in ("Cancelled", "Inactive", "ApiCancelled", "Filled"):
            return {
                "success": True, "already_working": True, "session": "uat",
                "account": ib_uat_service.account, "symbol": symbol, "action": action,
                "quantity": ot.get("qty"), "order_id": ot.get("order_id"),
                "status": ot.get("status"), "fill_price": None,
                "message": f"Close already working: {action} {ot.get('qty'):g} {symbol} order {ot.get('order_id')} "
                           f"({ot.get('status')}) — fills when the market opens; no duplicate placed.",
            }

    result = ib_uat_service.place_order(symbol=symbol, action=action,
                                        quantity=int(abs(qty)), order_type="MKT", account=None)
    if not result or not result.get("success"):
        err = (result or {}).get("error", "Unknown")
        raise HTTPException(status_code=500, detail=f"Close order failed on UAT session: {err}")

    status = result.get("status", "Submitted")
    filled = status == "Filled"
    fill = result.get("fill_price") or (pos.get("market_price") if filled else None) or (pos.get("avg_cost") if filled else None)
    market = "HK" if (pos.get("currency") == "HKD"
                      or (pos.get("exchange") or "").upper().startswith("SEHK")) else "US"

    # Book the close into the uat blotter — ONLY on an actual fill, so the
    # trade log never records an order that hasn't executed yet.
    if filled:
        try:
            safe_query_one(db, """
                INSERT INTO gold.manual_orders
                    (order_id, book, ticker, market, asset_class, side, qty, entry_price, limit_price, note, created_by)
                VALUES (:order_id, 'uat', :ticker, :market, 'STOCK', :side, :qty, :entry, NULL, :note, 'workspace')
                RETURNING order_id
            """, {
                "order_id": f"m{int(time.time() * 1000)}",
                "ticker": symbol, "market": market, "side": action,
                "qty": abs(qty), "entry": fill or 0,
                "note": f"IBKR UAT close · ib_order {result.get('order_id')} · acct {ib_uat_service.account}",
            }, label="uat_close_blotter_insert")
            db.commit()
        except Exception as blotter_err:
            db.rollback()
            logger.warning(f"UAT close filled but blotter insert failed: {blotter_err}")

    return {
        "success": True, "session": "uat", "account": ib_uat_service.account,
        "symbol": symbol, "action": action, "quantity": abs(qty),
        "order_id": result.get("order_id"), "status": status,
        "fill_price": result.get("fill_price"), "filled": filled,
        "message": (f"Closed {abs(qty):g} {symbol} on UAT paper account {ib_uat_service.account} ({action} @ MKT)"
                    if filled else
                    f"Close order {result.get('order_id')} working: {action} {abs(qty):g} {symbol} @ MKT "
                    f"({status}) — fills when the market opens"),
    }


@router.get("/ib/tws/uat/open-orders")
async def api_ib_tws_uat_open_orders():
    """Working (pending-execution) orders on the UAT session — queued orders
    waiting for market open show up here until they fill or are cancelled."""
    from datetime import datetime, timezone
    try:
        orders = ib_uat_service.get_open_trades()
        connected = orders is not None
        return {
            "session": "uat", "connected": connected,
            "account": ib_uat_service.account, "account_type": "PAPER",
            "data": orders if connected else None,
            "count": len(orders) if connected else None,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"session": "uat", "connected": False, "data": None, "error": str(e)}


@router.get("/ib/tws/uat/fills")
async def api_ib_tws_uat_fills():
    """Today's REAL executions on the UAT session (ib.fills()) — truthful even
    for orders placed outside the close-position endpoint. Each fill carries
    `order_ref` (strat:<strategy_id>) for fill→strategy attribution."""
    from datetime import datetime, timezone
    try:
        fills = ib_uat_service.get_fills()
        connected = fills is not None
        return {
            "session": "uat", "connected": connected,
            "account": ib_uat_service.account, "account_type": "PAPER",
            "data": fills if connected else None,
            "count": len(fills) if connected else None,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"session": "uat", "connected": False, "data": None, "error": str(e)}


@router.get("/ib/tws/uat/account")
async def api_ib_tws_uat_account():
    """Account summary (NetLiquidation, cash, buying power) from the UAT paper
    session — feeds the Execution UAT book header. connected=false + data=null
    when the session is down so the UI renders a pending state, never a fake $0."""
    from datetime import datetime, timezone
    try:
        summary = ib_uat_service.get_account_summary()
        connected = summary is not None
        return {
            "session": "uat", "connected": connected,
            "account": ib_uat_service.account, "account_type": "PAPER",
            "data": summary if connected else None,
            "as_of": datetime.now(timezone.utc).isoformat(),
            **({} if connected else {"message": "UAT paper session not connected — account summary unavailable. Use POST /api/ib/tws/uat/connect."}),
        }
    except Exception as e:
        return {"session": "uat", "connected": False, "data": None, "error": str(e)}


@router.post("/ib/tws/uat/cancel-order")
def api_ib_tws_uat_cancel_order(payload: dict):
    """Cancel a working order on the UAT session. The order must be visible in
    the UAT session's own openTrades — arbitrary/foreign order ids are refused
    and the primary session is never touched."""
    order_id = payload.get("order_id")
    if order_id is None:
        raise HTTPException(status_code=422, detail="order_id is required")
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="order_id must be an integer")

    if not ib_uat_service.is_connected:
        raise HTTPException(status_code=503,
                            detail="UAT paper session not connected — cannot cancel. Use POST /api/ib/tws/uat/connect first.")

    result = ib_uat_service.cancel_order(order_id)
    if not result or not result.get("success"):
        err = (result or {}).get("error", "Unknown")
        status_code = 404 if "not found" in str(err).lower() else 500
        raise HTTPException(status_code=status_code, detail=f"Cancel failed on UAT session: {err}")

    return {
        "success": True, "session": "uat", "account": ib_uat_service.account,
        "order_id": order_id, "symbol": result.get("symbol"), "status": result.get("status"),
        "message": f"Order {order_id} cancelled on UAT paper account {ib_uat_service.account}",
    }


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
    """Place an order through IBKR TWS API.

    Per-book routing (preferred): pass `book` in the payload —
      uat       -> dedicated UAT paper session (hard-fails 503 when
                   disconnected, NEVER falls back to the live account)
      live      -> primary session (manual live ticket, confirm-gated client-side)
      paper/sim -> virtual response only (paper strategies are fired by the
                   qr_etl rebalancer into the DB ledger, never via IBKR here)

    Legacy alias: `paper_uat` is accepted and normalized to `uat`.

    `strategy_id` (or explicit `order_ref`) tags the broker order with
    orderRef="strat:<strategy_id>" so fills are attributable to the strategy.

    Legacy fallback: when `book` is absent, routing follows
    gold.platform_settings.global_execution_mode (unchanged behaviour).
    """
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    symbol = payload.get("symbol", "AAPL")
    action = payload.get("action", "BUY")
    quantity = payload.get("quantity", 1)
    order_type = payload.get("order_type", "MKT")
    book = (payload.get("book") or "").strip().lower() or None
    # Legacy alias: pre-rename vocabulary spelled the UAT book "paper_uat".
    if book == "paper_uat":
        book = "uat"
    strategy_id = payload.get("strategy_id")
    order_ref = payload.get("order_ref") or (f"strat:{strategy_id}" if strategy_id else None)
    if book not in (None, "sim", "paper", "uat", "live"):
        raise HTTPException(status_code=422,
                            detail=f"Invalid book '{book}' — expected sim|paper|uat|live")

    # Virtual books never touch a broker session.
    if book in ("sim", "paper") or (book is None and current_mode == "SIMULATION"):
        sim_capital = db.execute(text(
            "SELECT value FROM gold.platform_settings WHERE key = 'simulation_capital'"
        )).fetchone()
        sim_amount = float(sim_capital.value) if sim_capital else 100000

        sim_stats = db.execute(text(
            "SELECT COALESCE(SUM(capital), 0) as total_allocated FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE'"
        )).fetchone()
        sim_used = float(sim_stats.total_allocated) if sim_stats else 0

        return {
            "success": True, "simulated": True,
            "message": f"{(book or 'sim').upper()}: {action} {quantity} shares of {symbol} would be placed",
            "order_id": f"SIM_{int(time.time())}", "mode": current_mode,
            "book": book or "sim", "order_ref": order_ref,
            "simulation_balance": {"total": sim_amount, "used": sim_used, "available": sim_amount - sim_used},
        }

    # Session routing:
    #   uat (book or legacy global mode) -> dedicated UAT paper session.
    #                    NEVER falls back to the primary session, so a UAT
    #                    order can never reach the live account.
    #   live / other legacy modes        -> primary session.
    if book == "uat" or (book is None and current_mode in ("PAPER_UAT", "UAT")):
        service = ib_uat_service
        session_name = "uat"
    else:
        service = ib_quant_service
        session_name = "primary"

    try:
        order_result = service.place_order(
            symbol=symbol, action=action, quantity=int(quantity), order_type=order_type,
            account=None, order_ref=order_ref,
        )
        if order_result and order_result.get("success"):
            return {
                "success": True, "order_id": order_result.get("order_id"),
                "status": order_result.get("status", "Submitted"), "mode": current_mode,
                "session": session_name,
                "book": book or ("uat" if current_mode in ("PAPER_UAT", "UAT") else "live"),
                "order_ref": order_ref, "strategy_id": strategy_id,
                "symbol": symbol, "action": action, "quantity": quantity,
                "message": f"{current_mode} order submitted via {session_name} session: {action} {quantity} {symbol}",
            }
        else:
            err = order_result.get('error', 'Unknown') if order_result else 'No result'
            is_uat = session_name == "uat"
            status_code = 503 if (is_uat and "not connected" in str(err).lower()) else 500
            raise HTTPException(status_code=status_code, detail=f"Order failed ({session_name} session): {err}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing IBKR order ({session_name} session): {e}")
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
        FROM consumption.portfolio_positions_current
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
                    UPDATE consumption.portfolio_positions_current
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
