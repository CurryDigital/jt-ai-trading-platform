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
from app.services.order_guard import live_trading_enabled, requested_account_guard_error

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

    # Tag the close order for fill attribution (t_03f5687f): untagged fills
    # are the signature of the 08-25/09-23/09-28 incidents. Manual closes are
    # book-management ops, not strategy orders — they get an explicit
    # "manual:uat-close:<symbol>" ref instead of a strategy ref.
    result = ib_uat_service.place_order(symbol=symbol, action=action,
                                        quantity=int(abs(qty)), order_type="MKT", account=None,
                                        order_ref=f"manual:uat-close:{symbol}")
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

    HARDENED (kanban t_03f5687f, 2026-10-09) after three proven incidents of
    defaulted/untagged orders hitting the real UAT account DUP825942:

    - NO DEFAULTS: symbol, action, quantity, order_type, book and strategy_id
      are all REQUIRED; missing/empty/unknown -> 422, no order placed.
    - `book` is REQUIRED — the legacy fallback that silently routed by
      gold.platform_settings.global_execution_mode is removed.
    - strategy_id must name an ACTIVE sleeve in gold.strategy_registry
      (status='paper') whose execution_mode matches the book (uat ->
      PAPER_UAT) and whose universe covers the symbol. Legacy signal-agent
      ids (gold.strategy_signals smallint space) are OBSERVE-ONLY and are
      refused. `order_ref` is stamped as strat:<strategy_id>.
    - book='live' and any account other than DUP825942 are refused unless the
      user set IBKR_LIVE_TRADING_ENABLE=true in the backend environment.

    Per-book routing:
      uat/paper_uat -> dedicated UAT paper session (hard-fails 503 when
                       disconnected, NEVER falls back to the live account)
      live          -> primary session (requires the live-enable flag)
      sim/paper     -> virtual response only (paper strategies are fired by
                       the qr_etl rebalancer into the DB ledger, never via
                       IBKR here)
    """
    # ------------------------------------------------------------------
    # 1. Required fields — no defaults anywhere (t_03f5687f item 1).
    # ------------------------------------------------------------------
    symbol = (str(payload.get("symbol") or "")).strip().upper()
    action = (str(payload.get("action") or "")).strip().upper()
    order_type = (str(payload.get("order_type") or "")).strip().upper()
    book = (str(payload.get("book") or "")).strip().lower()
    # Legacy alias: pre-rename vocabulary spelled the UAT book "paper_uat".
    if book == "paper_uat":
        book = "uat"
    quantity = payload.get("quantity")
    limit_price = payload.get("limit_price")
    time_in_force = (str(payload.get("time_in_force") or payload.get("tif") or "")).strip().upper()
    outside_rth = payload.get("outside_rth")
    idempotency_key = (str(payload.get("idempotency_key") or "")).strip()

    missing = [name for name, val in (
        ("symbol", symbol), ("action", action), ("quantity", quantity),
        ("order_type", order_type), ("book", book),
    ) if val in (None, "")]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required field(s): {', '.join(missing)}. "
                   f"Order construction has NO defaults — symbol, action, "
                   f"quantity, order_type, book and strategy_id are all required.")

    if action not in ("BUY", "SELL"):
        raise HTTPException(status_code=422,
                            detail=f"Invalid action '{action}' — expected BUY|SELL")
    if order_type not in ("MKT", "LMT", "STP", "STP_LMT"):
        raise HTTPException(status_code=422,
                            detail=f"Invalid order_type '{order_type}' — expected MKT|LMT|STP|STP_LMT")
    try:
        qty_num = float(quantity)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422,
                            detail=f"quantity must be a positive number, got {quantity!r}")
    if qty_num <= 0 or qty_num != int(qty_num):
        raise HTTPException(status_code=422,
                            detail=f"quantity must be a positive whole number, got {quantity!r}")
    quantity = int(qty_num)
    if book not in ("sim", "paper", "uat", "live"):
        raise HTTPException(status_code=422,
                            detail=f"Invalid book '{book}' — expected sim|paper|uat|live")
    if order_type == "LMT":
        try:
            limit_price = float(limit_price)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422,
                                detail=f"LMT order requires numeric limit_price, got {limit_price!r}")
        if limit_price <= 0:
            raise HTTPException(status_code=422, detail="limit_price must be > 0 for LMT")
        if not time_in_force:
            raise HTTPException(status_code=422, detail="LMT order requires time_in_force (e.g. DAY)")
        if outside_rth is None:
            raise HTTPException(status_code=422, detail="LMT order requires outside_rth true/false")
        outside_rth = bool(outside_rth)
    elif limit_price is not None:
        raise HTTPException(status_code=422,
                            detail="limit_price is only valid for order_type='LMT'")

    # ------------------------------------------------------------------
    # 2. Strategy attribution — required, registry-validated (item 2).
    # ------------------------------------------------------------------
    strategy_id = payload.get("strategy_id")
    order_ref = payload.get("order_ref")
    explicit_order_ref = order_ref
    if not strategy_id and isinstance(order_ref, str) and order_ref.startswith("strat:"):
        strategy_id = order_ref[len("strat:"):]
    strategy_id = (str(strategy_id or "")).strip()
    if not strategy_id:
        raise HTTPException(
            status_code=422,
            detail="strategy_id is required — NULL-strategy orders are refused "
                   "(untagged orders created the 2026-08-25/09-23/09-28 incidents).")
    if strategy_id.isdigit():
        raise HTTPException(
            status_code=422,
            detail=f"strategy_id '{strategy_id}' is a legacy signal-agent id "
                   f"(gold.strategy_signals smallint space) — OBSERVE-ONLY, not "
                   f"order-attributable. Use a gold.strategy_registry sleeve id.")
    if not order_ref:
        order_ref = f"strat:{strategy_id}"

    if strategy_id == "OPS_RECON":
        # User-approved reconciliation covers (e.g. RECON_FLATTEN_t_*). These
        # are account-management orders owned by no sleeve; they still route
        # through the guarded UAT path, require an explicit RECON_FLATTEN ref,
        # a persisted idempotency key, and a marketable-limit order spec.
        if book != "uat":
            raise HTTPException(status_code=422,
                                detail="OPS_RECON may only route to book='uat'.")
        if not isinstance(explicit_order_ref, str) or not explicit_order_ref.startswith("RECON_FLATTEN_"):
            raise HTTPException(status_code=422,
                                detail="OPS_RECON requires explicit order_ref='RECON_FLATTEN_<task_id>'.")
        if not idempotency_key:
            raise HTTPException(status_code=422,
                                detail="OPS_RECON requires idempotency_key.")
        if order_type != "LMT":
            raise HTTPException(status_code=422,
                                detail="OPS_RECON reconciliation covers are LMT-only.")
    else:
        reg = db.execute(text(
            "SELECT strategy_id, status, execution_mode, universe_tickers "
            "FROM gold.strategy_registry WHERE strategy_id = :sid"
        ), {"sid": strategy_id}).fetchone()
        if not reg:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown strategy_id '{strategy_id}' — not registered in "
                       f"gold.strategy_registry; order refused.")
        if reg.status != "paper":
            raise HTTPException(
                status_code=422,
                detail=f"Strategy '{strategy_id}' is not active (status='{reg.status}'); "
                       f"only active (status='paper') sleeves may place orders.")
        if book == "uat" and reg.execution_mode != "PAPER_UAT":
            raise HTTPException(
                status_code=422,
                detail=f"Strategy '{strategy_id}' is execution_mode='{reg.execution_mode}', "
                       f"not PAPER_UAT — it may not fire orders to the UAT broker book.")
        universe = [str(t).upper() for t in (reg.universe_tickers or [])]
        if universe and symbol not in universe:
            raise HTTPException(
                status_code=422,
                detail=f"Strategy '{strategy_id}' is not allowed to trade {symbol} "
                       f"(not in its registered universe).")

    # ------------------------------------------------------------------
    # 3. Account guard (item 5): only DUP825942 unless the user's
    #    live-enable flag is set. book='live' requires the flag outright.
    # ------------------------------------------------------------------
    requested_account = payload.get("account")
    if book == "live" and not live_trading_enabled():
        raise HTTPException(
            status_code=403,
            detail="book='live' is refused: live trading is not enabled. The user "
                   "must set IBKR_LIVE_TRADING_ENABLE=true in backend/.env and "
                   "restart the backend.")
    guard_err = requested_account_guard_error(requested_account)
    if guard_err:
        raise HTTPException(status_code=403, detail=guard_err)

    # ------------------------------------------------------------------
    # 4. Routing. Virtual books never touch a broker session.
    # ------------------------------------------------------------------
    if book in ("sim", "paper"):
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
            "message": f"{book.upper()}: {action} {quantity} shares of {symbol} would be placed",
            "order_id": f"SIM_{int(time.time())}", "mode": "SIMULATION",
            "book": book, "order_ref": order_ref, "strategy_id": strategy_id,
            "simulation_balance": {"total": sim_amount, "used": sim_used, "available": sim_amount - sim_used},
        }

    #   uat  -> dedicated UAT paper session (never falls back to primary).
    #   live -> primary session (only reachable with the live-enable flag).
    if book == "uat":
        service = ib_uat_service
        session_name = "uat"
    else:
        service = ib_quant_service
        session_name = "primary"

    try:
        order_result = service.place_order(
            symbol=symbol, action=action, quantity=quantity, order_type=order_type,
            account=None, order_ref=order_ref,
            limit_price=limit_price,
            time_in_force=time_in_force or None,
            outside_rth=outside_rth,
            idempotency_key=idempotency_key or None,
        )
        if order_result and order_result.get("success"):
            return {
                "success": True, "order_id": order_result.get("order_id"),
                "status": order_result.get("status", "Submitted"), "mode": "BROKER",
                "session": session_name,
                "book": book,
                "order_ref": order_ref, "strategy_id": strategy_id,
                "symbol": symbol, "action": action, "quantity": quantity,
                "message": f"{book.upper()} order submitted via {session_name} session: {action} {quantity} {symbol}",
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
    """Sync paper positions to IBKR by placing real orders.

    HARDENED (t_03f5687f): fires real orders on the PRIMARY session, so the
    whole endpoint is refused unless the user enabled live trading
    (IBKR_LIVE_TRADING_ENABLE=true). Every order is tagged
    order_ref='strat:<strategy_id>' from the position row, and the dangerous
    current_price=100 fallback is removed — a position with no usable price
    is skipped, never ordered at a fabricated size."""
    if not live_trading_enabled():
        raise HTTPException(
            status_code=403,
            detail="sync-to-ibkr places real orders on the primary session and is "
                   "refused: live trading is not enabled (IBKR_LIVE_TRADING_ENABLE "
                   "is not set by the user).")

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

        # Use DB price to calc quantity (no yfinance). NO fabricated fallback
        # price (t_03f5687f): a position with no usable price is skipped,
        # never ordered at a made-up size.
        if pos["entry_price"] and pos["entry_price"] > 0:
            quantity = int(pos["capital"] / pos["entry_price"])
        else:
            price_row = db.execute(text("""
                SELECT close FROM silver.unified_prices WHERE ticker = :t ORDER BY date DESC LIMIT 1
            """), {"t": ticker}).fetchone()
            if not price_row or not price_row.close or float(price_row.close) <= 0:
                failed.append({"ticker": ticker, "error": "no usable price (no entry_price, no unified_prices close) — skipped"})
                continue
            quantity = int(pos["capital"] / float(price_row.close))

        if quantity < 1:
            failed.append({"ticker": ticker, "error": f"computed quantity {quantity} < 1 — skipped"})
            continue

        try:
            # Tag every order with its strategy for fill attribution (t_03f5687f).
            order_ref = f"strat:{pos['strategy_id']}" if pos.get("strategy_id") else None
            if not order_ref:
                failed.append({"ticker": ticker, "error": "position row has NULL strategy_id — refused (untagged orders are not allowed)"})
                continue
            order_result = ib_quant_service.place_order(symbol=ticker, action="BUY", quantity=quantity, order_type="MKT", account=None, order_ref=order_ref)

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
