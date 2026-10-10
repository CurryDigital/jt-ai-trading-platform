"""
IBKR Service - Threaded Implementation
Isolates ib_insync event loop from FastAPI's async loop
"""
import threading
import asyncio
import logging
from queue import Queue

import os
from dotenv import load_dotenv

from app.services.order_guard import account_guard_error

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Lazy import of ib_insync to avoid asyncio event loop conflicts at import time
IB = None
Forex = None
Stock = None
MarketOrder = None

def _ensure_ib_insync():
    """Lazy-load ib_insync classes only when needed (inside a running thread)."""
    global IB, Forex, Stock, MarketOrder
    if IB is None:
        from ib_insync import IB, Forex, Stock, MarketOrder

class IBKRThreadedService:
    """
    Thread-safe IBKR service that runs in its own thread with isolated event loop.
    This avoids conflicts with FastAPI's asyncio loop.
    
    IB Gateway Ports:
    - 4001 = LIVE trading (real money)
    - 4002 = PAPER trading (simulated)
    """
    
    def __init__(self, host=None, port=None, client_id=None):
        self.host = host or os.getenv('IBKR_HOST', '52.74.14.181')
        self.port = int(port or os.getenv('IBKR_PORT', 4002))
        self.client_id = int(client_id or os.getenv('IBKR_CLIENT_ID', 1))
        self._ib = None
        self._connected = False
        self._thread = None
        self._loop = None
        self._queue = Queue()
        self._results = {}  # Store order results
        self._account = None  # Real managed account id, captured on connect
        self._last_connect_attempt = 0  # throttle for auto-reconnect

    def _try_connect(self):
        """(Re)connect to the gateway. MUST run inside the IB thread — ib_insync
        objects are bound to that thread's event loop. Safe to call repeatedly:
        a dead attempt just leaves _connected False."""
        import time
        self._last_connect_attempt = time.time()
        try:
            if self._ib is not None:
                try:
                    self._ib.disconnect()
                except Exception:
                    pass
            self._ib = IB()
            self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            self._connected = True
            try:
                accts = self._ib.managedAccounts()
                self._account = accts[0] if accts else None
            except Exception:
                self._account = None
            logger.info(f"IBKR Thread: Connected to {self.host}:{self.port} account={self._account}")
        except Exception as e:
            logger.error(f"IBKR Thread: Connection failed - {e}")
            self._connected = False

    def get_positions(self):
        """Real positions from the gateway session (reads the IB wrapper's
        cached portfolio state — no new requests, safe cross-thread read).
        Returns None when disconnected so callers can distinguish
        'no data' from 'genuinely flat'."""
        if not self._connected or self._ib is None:
            return None
        try:
            out = []
            for p in (self._ib.portfolio() or []):
                c = p.contract
                out.append({
                    "ticker": c.localSymbol or c.symbol,
                    "symbol": c.symbol,
                    "sec_type": c.secType,
                    "exchange": c.primaryExchange or c.exchange,
                    "currency": c.currency,
                    "qty": float(p.position),
                    "avg_cost": float(p.averageCost) if p.averageCost is not None else None,
                    "market_price": float(p.marketPrice) if p.marketPrice is not None else None,
                    "market_value": float(p.marketValue) if p.marketValue is not None else None,
                    "unrealized_pnl": float(p.unrealizedPNL) if p.unrealizedPNL is not None else None,
                    "realized_pnl": float(p.realizedPNL) if p.realizedPNL is not None else None,
                    "account": p.account,
                })
            return out
        except Exception as e:
            logger.error(f"IBKR get_positions failed: {e}")
            return None

    def get_open_trades(self):
        """Working (unfilled/cancellable) orders on THIS session's connection.
        Reads the IB wrapper's cached state — safe cross-thread read.
        Returns None when disconnected."""
        if not self._connected or self._ib is None:
            return None
        try:
            out = []
            for t in (self._ib.openTrades() or []):
                out.append({
                    "order_id": t.order.orderId,
                    "perm_id": t.order.permId,
                    "symbol": t.contract.symbol,
                    "local_symbol": t.contract.localSymbol,
                    "action": t.order.action,
                    "qty": float(t.order.totalQuantity),
                    "order_type": t.order.orderType,
                    "status": t.orderStatus.status if t.orderStatus else None,
                    "filled": float(t.orderStatus.filled) if t.orderStatus else 0,
                    "remaining": float(t.orderStatus.remaining) if t.orderStatus else None,
                })
            return out
        except Exception as e:
            logger.error(f"IBKR get_open_trades failed: {e}")
            return None

    def request_reconnect(self):
        """Ask the IB thread to (re)connect now (thread-safe, non-blocking)."""
        self._queue.put({'type': 'reconnect'})

    @property
    def account(self):
        """Real account id captured at connect time (None when never connected)."""
        return self._account
        
    def _run_in_thread(self):
        """Run the IBKR event loop in a separate thread"""
        # Set up event loop BEFORE importing ib_insync/eventkit so their
        # module-level loop detection succeeds on this non-main thread.
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        _ensure_ib_insync()
        import time
        
        try:
            self._ib = IB()
            # Try to connect
            try:
                self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
                self._connected = True
                try:
                    accts = self._ib.managedAccounts()
                    self._account = accts[0] if accts else None
                except Exception:
                    self._account = None
                logger.info(f"IBKR Thread: Connected to {self.host}:{self.port} account={self._account}")
            except Exception as e:
                logger.error(f"IBKR Thread: Connection failed - {e}")
                self._connected = False
            self._last_connect_attempt = time.time()

            # Keep thread alive processing events
            while True:
                try:
                    # Process any pending commands
                    stop_requested = False
                    while not self._queue.empty():
                        cmd = self._queue.get_nowait()
                        if cmd == 'stop':
                            stop_requested = True
                            break
                        elif isinstance(cmd, dict) and cmd.get('type') == 'order':
                            # Process order request
                            self._process_order_request(cmd)
                        elif isinstance(cmd, dict) and cmd.get('type') == 'cancel':
                            self._process_cancel_request(cmd)
                        elif isinstance(cmd, dict) and cmd.get('type') == 'reconnect':
                            if not self._connected:
                                logger.info("IBKR Thread: reconnect requested")
                                self._try_connect()

                    if stop_requested:
                        logger.info("IBKR Thread: stop requested - shutting down")
                        break

                    if self._ib and self._connected:
                        self._ib.sleep(0.1)  # Process IB events
                    else:
                        # Auto-heal: retry the connection every 10s so the session
                        # recovers on its own when the gateway/tunnel comes up later.
                        if time.time() - self._last_connect_attempt > 10:
                            self._try_connect()
                        import time as _t
                        _t.sleep(1)
                        
                except Exception as e:
                    logger.error(f"IBKR Thread Error: {e}")
                    import time
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"IBKR Thread Fatal Error: {e}")
        finally:
            if self._ib:
                try:
                    self._ib.disconnect()
                except:
                    pass
    
    def get_price(self, symbol):
        """Get current market price for a symbol from IBKR"""
        if not self._connected or not self._ib:
            return None
        
        try:
            # Determine contract type
            if '/' in symbol:
                pair = symbol.replace('/', '')
                contract = Forex(pair)
            elif symbol.endswith('.HK'):
                stock_symbol = symbol.replace('.HK', '')
                contract = Stock(stock_symbol, 'SEHK', 'HKD')
            elif symbol.endswith('.SI'):
                stock_symbol = symbol.replace('.SI', '')
                contract = Stock(stock_symbol, 'SGX', 'SGD')
            elif symbol.endswith('.SS'):
                stock_symbol = symbol.replace('.SS', '')
                contract = Stock(stock_symbol, 'SSE', 'CNY')
            elif symbol.endswith('.SZ'):
                stock_symbol = symbol.replace('.SZ', '')
                contract = Stock(stock_symbol, 'SZSE', 'CNY')
            elif symbol in ['BTC', 'ETH', 'SOL']:
                # Crypto not available on IBKR, return None to use fallback
                return None
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Request market data
            ticker = self._ib.reqMktData(contract, '', False, False)
            self._ib.sleep(0.5)  # Wait for data
            
            price = None
            if ticker.last:
                price = ticker.last
            elif ticker.close:
                price = ticker.close
            elif ticker.bid and ticker.ask:
                price = (ticker.bid + ticker.ask) / 2
            
            # Cancel market data subscription
            self._ib.cancelMktData(contract)
            
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def _process_cancel_request(self, cmd):
        """Cancel a working order in the IB thread. Only orders visible in this
        session's openTrades can be cancelled — no arbitrary order ids."""
        import time
        request_id = cmd.get('request_id')
        order_id = cmd.get('order_id')
        try:
            ib = self._ib
            if not ib:
                self._results[request_id] = {"success": False, "error": "IB not available"}
                return
            trade = next((t for t in (ib.openTrades() or []) if t.order.orderId == order_id), None)
            if not trade:
                self._results[request_id] = {"success": False,
                                             "error": f"Order {order_id} not found among working orders on this session"}
                return
            symbol = trade.contract.symbol
            ib.cancelOrder(trade.order)
            start = time.time()
            while time.time() - start < 10:
                ib.sleep(0.3)
                if trade.orderStatus.status in ('Cancelled', 'ApiCancelled', 'Inactive'):
                    break
            status = trade.orderStatus.status
            ok = status in ('Cancelled', 'ApiCancelled', 'Inactive')
            logger.info(f"Cancel order {order_id} ({symbol}): {status}")
            self._results[request_id] = {"success": ok, "order_id": order_id,
                                         "symbol": symbol, "status": status,
                                         **({} if ok else {"error": f"Cancel requested but status is {status}"})}
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            self._results[request_id] = {"success": False, "error": str(e)}

    def submit_cancel(self, order_id):
        """Queue a cancel for a working order and wait for the result."""
        import uuid
        import time
        if not self.is_connected:
            return {"success": False, "error": "Not connected to IBKR"}
        request_id = str(uuid.uuid4())
        self._queue.put({'type': 'cancel', 'request_id': request_id, 'order_id': int(order_id)})
        timeout = 15
        start_time = time.time()
        while time.time() - start_time < timeout:
            if request_id in self._results:
                return self._results.pop(request_id)
            time.sleep(0.1)
        return {"success": False, "error": "Cancel timeout - no response from IB thread"}

    def get_fills(self):
        """Today's real executions on THIS session (ib.fills() — cached wrapper
        state, safe cross-thread read). Returns None when disconnected.

        Each fill is annotated with `order_ref` (from the originating order's
        orderRef, e.g. "strat:<strategy_id>") so callers can attribute fills
        back to the firing strategy. None when the order carried no tag."""
        if not self._connected or self._ib is None:
            return None
        try:
            # orderId -> orderRef map from this session's trades
            ref_by_order = {}
            for t in (self._ib.trades() or []):
                try:
                    ref_by_order[t.order.orderId] = t.order.orderRef or None
                except Exception:
                    continue
            out = []
            for f in (self._ib.fills() or []):
                e = f.execution
                out.append({
                    "exec_id": e.execId,
                    "order_id": e.orderId,
                    "order_ref": ref_by_order.get(e.orderId),
                    "symbol": f.contract.symbol,
                    "local_symbol": f.contract.localSymbol,
                    "side": {"BOT": "BUY", "SLD": "SELL"}.get(e.side, e.side),
                    "qty": float(e.shares),
                    "price": float(e.price),
                    "time": e.time.isoformat() if e.time else None,
                    "account": e.acctNumber,
                })
            return out
        except Exception as e:
            logger.error(f"IBKR get_fills failed: {e}")
            return None

    def _process_order_request(self, cmd):
        """Process an order request in the IB thread"""
        from ib_insync import Stock, Forex, MarketOrder
        import time
        
        request_id = cmd.get('request_id')
        symbol = cmd.get('symbol')
        action = cmd.get('action')
        quantity = cmd.get('quantity')
        order_type = cmd.get('order_type', 'MKT')
        
        try:
            ib = self._ib
            if not ib:
                self._results[request_id] = {"success": False, "error": "IB not available"}
                return
            
            # Determine contract type
            if '/' in symbol:
                pair = symbol.replace('/', '')
                contract = Forex(pair)
            elif symbol.endswith('.HK'):
                stock_symbol = symbol.replace('.HK', '')
                contract = Stock(stock_symbol, 'SEHK', 'HKD')
            elif symbol.endswith('.SI'):
                stock_symbol = symbol.replace('.SI', '')
                contract = Stock(stock_symbol, 'SGX', 'SGD')
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            qualified_contracts = ib.qualifyContracts(contract)
            if not qualified_contracts:
                self._results[request_id] = {"success": False, "error": f"Could not qualify contract for {symbol}"}
                return
            
            contract = qualified_contracts[0]
            
            if order_type == "MKT":
                order = MarketOrder(action, quantity)
                order.tif = 'GTC'
            else:
                self._results[request_id] = {"success": False, "error": f"Order type {order_type} not implemented"}
                return

            # Strategy attribution tag — flows to TWS as orderRef and comes back
            # on fills, enabling fill→strategy attribution (strat:<strategy_id>).
            order_ref = cmd.get('order_ref')
            if order_ref:
                order.orderRef = str(order_ref)[:50]  # TWS orderRef is length-limited

            trade = ib.placeOrder(contract, order)

            if trade:
                logger.info(f"Order placed: {symbol} {action} {quantity} - Order ID: {trade.order.orderId}")

                # Wait for fill and get actual execution price (golden source)
                fill_price = None
                max_wait = 30  # Max 30 seconds to fill
                wait_start = time.time()

                while time.time() - wait_start < max_wait:
                    ib.sleep(0.5)  # Short sleep to process events

                    # Check if order is filled
                    if trade.orderStatus.status == 'Filled':
                        # Get the average fill price from executions
                        if trade.fills:
                            total_cost = 0
                            total_shares = 0
                            for fill in trade.fills:
                                exec_price = fill.execution.price
                                exec_shares = fill.execution.shares
                                total_cost += exec_price * exec_shares
                                total_shares += exec_shares
                            fill_price = total_cost / total_shares if total_shares > 0 else None
                            logger.info(f"Order filled: {symbol} at ${fill_price:.2f} (IBKR golden source)")
                        break

                    # Stop waiting on terminal non-fill states (rejected/cancelled)
                    if trade.orderStatus.status in ('Cancelled', 'Inactive', 'ApiCancelled'):
                        logger.error(f"Order {trade.order.orderId} ended as {trade.orderStatus.status}")
                        break

                    # NOTE: ib_insync Trade has .fills, NOT .executions — an
                    # attribute typo here previously crashed the wait loop AFTER
                    # the order was already live at the gateway, misreporting
                    # accepted orders as failures.

                status = trade.orderStatus.status if trade.orderStatus else "Pending"
                if status in ('Cancelled', 'Inactive', 'ApiCancelled'):
                    self._results[request_id] = {
                        "success": False,
                        "error": f"Order {status}",
                        "order_id": trade.order.orderId,
                        "status": status,
                    }
                else:
                    self._results[request_id] = {
                        "success": True,
                        "order_id": trade.order.orderId,
                        "status": status,  # PreSubmitted/Submitted = working, not yet filled
                        "fill_price": fill_price,  # IBKR golden source price (None while working)
                        "avg_fill_price": fill_price
                    }
            else:
                self._results[request_id] = {"success": False, "error": "Failed to place order"}
                
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            self._results[request_id] = {"success": False, "error": str(e)}
    
    def start(self):
        """Start the IBKR service thread"""
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
            self._thread.start()
            import time
            time.sleep(2)  # Give time to connect
            logger.info("IBKR Thread: Started")
    
    def stop(self):
        """Stop the IBKR service"""
        self._queue.put('stop')
        if self._thread:
            self._thread.join(timeout=5)
    
    @property
    def is_connected(self):
        """Check connection status (thread-safe) with proactive health validation"""
        if not self._connected or self._ib is None:
            return False
        
        try:
            # Check if IB thinks it's connected
            if not self._ib.isConnected():
                self._connected = False
                return False
            
            # Proactive health check: try to get managed accounts
            # This will fail if the connection is actually dead
            accounts = self._ib.managedAccounts()
            if accounts is None:
                logger.warning("IBKR health check: managedAccounts() returned None")
                self._connected = False
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"IBKR connection check failed: {e}")
            self._connected = False
            return False
    
    def submit_order(self, symbol, action, quantity, order_type="MKT", order_ref=None):
        """
        Submit an order to the IBKR queue and wait for result.
        Returns the order result.

        order_ref: optional strategy attribution tag (e.g. "strat:<strategy_id>")
        stamped onto order.orderRef so fills can be attributed back to the
        firing strategy via ib.fills()/trades().
        """
        import uuid
        import time

        if not self.is_connected:
            return {"success": False, "error": "Not connected to IBKR"}

        request_id = str(uuid.uuid4())

        # Create order request
        order_request = {
            'type': 'order',
            'request_id': request_id,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'order_type': order_type,
            'order_ref': order_ref,
        }
        
        # Submit to queue
        self._queue.put(order_request)
        
        # Wait for result (with timeout). Must exceed the in-thread fill wait
        # (max_wait=30s in _process_order_request) or a working order queued
        # outside market hours is misreported as a timeout failure.
        timeout = 35  # seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self._results:
                result = self._results.pop(request_id)
                return result
            time.sleep(0.1)
        
        return {"success": False, "error": "Order timeout - no response from IB thread"}
    
    def get_status(self):
        """Get current status with diagnostics"""
        status = {
            "is_connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "client_id": self.client_id,
            "account": self._account,
            "recommended": True,
            "diagnostics": {
                "thread_alive": self._thread.is_alive() if self._thread else False,
                "loop_running": self._loop is not None,
                "ib_initialized": self._ib is not None
            }
        }
        
        # Add helpful message
        if not self.is_connected:
            status["message"] = (
                "Gateway connection failed. Possible causes:\n"
                "1. Gateway not running on 13.214.84.37:4001\n"
                "2. Gateway in Read-Only mode (disable in Gateway settings)\n"
                "3. Firewall blocking port 4001\n"
                "4. Wrong IP/port configuration"
            )
        else:
            status["message"] = "Connected to IB Gateway"
            
        return status

# Lazy singleton instance - created on first access
_ib_threaded_service_instance = None

def get_ib_threaded_service():
    """Get or create the IBKR threaded service singleton (lazy initialization)"""
    global _ib_threaded_service_instance
    if _ib_threaded_service_instance is None:
        _ib_threaded_service_instance = IBKRThreadedService()
    return _ib_threaded_service_instance

# =============================================================================
# UAT session — IBKR paper-account session for the Execution UAT tab.
# Real gateway connection, real order firing, paper money.
# Separate TWS/Gateway port + client id from the primary session so the two
# API client sessions never collide on the gateway.
#
# Config (env):
#   IBKR_UAT_HOST       default: IBKR_HOST, else 127.0.0.1
#   IBKR_UAT_PORT       default: IBKR_PORT, else 14002  (paper tunnel)
#   IBKR_UAT_CLIENT_ID  default: 2  (primary session uses 1)
#
# HARD SAFETY: the UAT session must never point at a live-trading port.
# =============================================================================
LIVE_TRADING_PORTS = {4001, 14001, 7496}

_ib_uat_service_instance = None

def get_ib_uat_config():
    """Resolve (host, port, client_id) for the UAT session from env."""
    host = os.getenv('IBKR_UAT_HOST') or os.getenv('IBKR_HOST', '127.0.0.1')
    port = int(os.getenv('IBKR_UAT_PORT') or os.getenv('IBKR_PORT', 14002))
    client_id = int(os.getenv('IBKR_UAT_CLIENT_ID', 2))
    return host, port, client_id

def get_ib_uat_service():
    """Get or create the UAT threaded service singleton (lazy initialization).

    Raises RuntimeError if the resolved config points at a live-trading port —
    UAT orders must NEVER reach the live account.
    """
    global _ib_uat_service_instance
    if _ib_uat_service_instance is None:
        host, port, client_id = get_ib_uat_config()
        if port in LIVE_TRADING_PORTS:
            raise RuntimeError(
                f"UAT session misconfigured: port {port} is a LIVE trading port. "
                "Set IBKR_UAT_PORT to the paper gateway port (e.g. 14002/4002)."
            )
        _ib_uat_service_instance = IBKRThreadedService(host=host, port=port, client_id=client_id)
    return _ib_uat_service_instance

# Legacy compatibility
def _fetch_account_summary(threaded_svc):
    """Shared account-summary fetch against a threaded service's IB instance.

    Currency-audit fix (t_22dee93d, 2026-10-10): every value is extracted by
    explicit (tag, currency) match — no last-row-wins, no unlabeled values.
    Each figure carries a `*_currency` label, plus a `*_usd` conversion via
    the shared fx helper (app.services.fx) from the payload's own
    $LEDGER-ExchangeRate rows. Missing/undetectable rate -> fx=None +
    fx_error set + logger.error (alert); NEVER a default rate.
    """
    if not threaded_svc.is_connected:
        logger.warning("Cannot fetch account summary: IBKR not connected")
        return None
    try:
        ib = threaded_svc._ib
        if not ib:
            logger.warning("IB instance is None despite is_connected=True")
            return None
        if not ib.isConnected():
            logger.warning("IB isConnected() returned False during account fetch")
            threaded_svc._connected = False
            return None
        accounts = ib.managedAccounts()
        if not accounts:
            logger.warning("No managed accounts returned from IB")
            return None
        account = accounts[0]
        try:
            values = ib.accountValues(account)
            if values is None:
                logger.warning("accountValues() returned None")
                return None
        except Exception as av_err:
            logger.error(f"Error fetching account values: {av_err}")
            return None

        from app.services.fx import quote_from_account_values, FxRateUnavailable

        # FX first: the ExchangeRate rows also tell us the account's BASE
        # currency (the non-BASE row with rate == 1.0). No rate -> error +
        # alert, no silent USD default.
        fx_quote = None
        fx_error = None
        try:
            fx_quote = quote_from_account_values(values)
        except FxRateUnavailable as fx_err:
            fx_error = str(fx_err)
            logger.error(f"FX ALERT: account summary has no usable ExchangeRate payload: {fx_err}")

        # Bucket rows by (tag, currency) — explicit, no overwrite-by-iteration.
        by_pair = {}
        for v in values:
            if v.currency:
                by_pair[(v.tag, v.currency.upper())] = v.value

        def _pick(tag):
            """Return (value, currency) for a value tag: the BASE-currency row
            when known, else the sole currency row, else (None, None)."""
            rows = {c: val for (t, c), val in by_pair.items() if t == tag}
            if not rows:
                return None, None
            if fx_quote and fx_quote.base_currency in rows:
                c = fx_quote.base_currency
                return float(rows[c]), c
            if len(rows) == 1:
                c, val = next(iter(rows.items()))
                return float(val), c
            # Multiple currency rows and no detected base: refuse to guess.
            logger.error(f"FX ALERT: {tag} has rows in {sorted(rows)} but base currency is unknown")
            return None, None

        def _usd(value, currency):
            if value is None or currency is None or fx_quote is None:
                return None
            try:
                return fx_quote.to_usd(value, currency)
            except FxRateUnavailable:
                return None

        def _cash(ccy):
            val = by_pair.get(("$LEDGER-CashBalance", ccy))
            return float(val) if val is not None else None

        nl, nl_ccy = _pick("NetLiquidation")
        af, af_ccy = _pick("AvailableFunds")
        bp, bp_ccy = _pick("BuyingPower")
        el, el_ccy = _pick("ExcessLiquidity")
        cash_hkd = _cash("HKD")
        cash_usd = _cash("USD")
        cash_total_base = None
        if fx_quote and (cash_hkd is not None or cash_usd is not None):
            try:
                cash_total_base = sum(
                    fx_quote.convert(v, c, fx_quote.base_currency)
                    for c, v in (("HKD", cash_hkd), ("USD", cash_usd)) if v is not None
                )
            except FxRateUnavailable:
                cash_total_base = None

        result = {
            "account": account,
            # base currency detected from the payload's ExchangeRate rows;
            # None when undetectable (fx_error set) — never assumed.
            "base_currency": fx_quote.base_currency if fx_quote else None,
            "currency": fx_quote.base_currency if fx_quote else None,
            "net_liquidation": nl, "net_liquidation_currency": nl_ccy,
            "available_funds": af, "available_funds_currency": af_ccy,
            "buying_power": bp, "buying_power_currency": bp_ccy,
            "excess_liquidity": el, "excess_liquidity_currency": el_ccy,
            "cash_hkd": cash_hkd, "cash_usd": cash_usd,
            "cash_total": cash_total_base,
            "cash_total_currency": fx_quote.base_currency if fx_quote else None,
            "net_liquidation_usd": _usd(nl, nl_ccy),
            "available_funds_usd": _usd(af, af_ccy),
            "buying_power_usd": _usd(bp, bp_ccy),
            "excess_liquidity_usd": _usd(el, el_ccy),
            "cash_total_usd": _usd(cash_total_base, fx_quote.base_currency) if fx_quote else None,
            "fx": fx_quote.public_dict() if fx_quote else None,
            "fx_error": fx_error,
        }
        return result
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        threaded_svc._connected = False
        return None


class IBKRQuantService:
    """Legacy wrapper for compatibility"""
    # Default: read from IBKR_HOST / IBKR_PORT env vars, then fall back to paper gateway
    def __init__(self, host=None, port=None, client_id=None):
        self.host = host or os.getenv('IBKR_HOST', '52.74.14.181')
        self.port = int(port or os.getenv('IBKR_PORT', 4002))
        self.client_id = int(client_id or os.getenv('IBKR_CLIENT_ID', 1))
        # Lazy start - don't block startup, connect when first needed
        self._started = False
    
    def _ensure_started(self):
        """Start the service on first use"""
        if not self._started:
            get_ib_threaded_service().start()
            self._started = True
    
    @property
    def is_connected(self):
        return get_ib_threaded_service().is_connected

    @property
    def account(self):
        return get_ib_threaded_service().account
    
    def get_status(self):
        """Get connection status from threaded service"""
        return get_ib_threaded_service().get_status()
    
    def get_account_summary(self):
        """Get account summary - requires connected IB instance with health validation"""
        return _fetch_account_summary(get_ib_threaded_service())
    
    async def connect(self):
        """Connect - service starts on demand; request an in-thread reconnect
        (the IB thread may be alive from a failed earlier attempt) and wait."""
        self._ensure_started()
        svc = get_ib_threaded_service()
        if not svc.is_connected:
            svc.request_reconnect()
        import time
        deadline = time.time() + 12
        while time.time() < deadline:
            if svc.is_connected:
                break
            time.sleep(0.5)
        if svc.is_connected:
            return {"status": "Connected", "port": self.port, "account": svc.account}
        return {"status": "Failed", "reason": "Gateway not responding. Check if Gateway is running."}
    
    async def get_fx_realtime(self, pair='EURUSD'):
        """Get real-time FX data"""
        if not get_ib_threaded_service().is_connected:
            return None
        # This would need proper async bridge - simplified for now
        return {"bid": None, "ask": None, "last": None, "note": "Streaming not yet implemented in threaded mode"}
    
    async def execute_quant_trade(self, pair, action, quantity):
        """Execute trade - placeholder"""
        if not get_ib_threaded_service().is_connected:
            return {"status": "error", "message": "Not connected"}
        return {"status": "success", "message": "Trade execution requires full implementation"}
    
    def place_order(self, symbol, action, quantity, order_type="MKT", account=None, order_ref=None):
        """
        Place an order through IBKR TWS API.
        Uses the threaded service to ensure proper event loop handling.

        Args:
            symbol: Stock/FX symbol
            action: "BUY" or "SELL"
            quantity: Number of shares/contracts
            order_type: Order type (MKT, LMT, etc.)
            account: Account ID (None for default)
            order_ref: optional strategy attribution tag (strat:<strategy_id>)

        Returns:
            dict with success status and order_id
        """
        if not get_ib_threaded_service().is_connected:
            logger.error("Cannot place order: IBKR not connected")
            return {"success": False, "error": "Not connected to IBKR"}

        # Hard account guard (t_03f5687f): refuse any account other than the
        # allowed one unless the user set IBKR_LIVE_TRADING_ENABLE=true.
        guard_err = account_guard_error(
            connected_account=get_ib_threaded_service().account,
            requested_account=account,
        )
        if guard_err:
            logger.error(f"Order refused: {guard_err}")
            return {"success": False, "error": guard_err}

        # Use the threaded service's submit_order method
        return get_ib_threaded_service().submit_order(symbol, action, quantity, order_type, order_ref=order_ref)
    
    def get_price(self, symbol):
        """Get current market price for a symbol from IBKR"""
        return get_ib_threaded_service().get_price(symbol)

# Keep the old name for compatibility - lazy initialization
ib_quant_service = IBKRQuantService()


# =============================================================================
# UAT service wrapper — routes Execution UAT orders to the dedicated
# paper session (get_ib_uat_service), never the primary/live session.
# =============================================================================
class IBKRUatService:
    """UAT session facade mirroring IBKRQuantService's interface."""

    def __init__(self):
        self._started = False

    def _ensure_started(self):
        if not self._started:
            get_ib_uat_service().start()
            self._started = True

    @property
    def host(self):
        return get_ib_uat_config()[0]

    @property
    def port(self):
        return get_ib_uat_config()[1]

    @property
    def client_id(self):
        return get_ib_uat_config()[2]

    @property
    def is_connected(self):
        # No side effects: False until the session thread is started + connected.
        svc = get_ib_uat_service()
        return svc.is_connected

    @property
    def account(self):
        return get_ib_uat_service().account

    def get_positions(self):
        """Real positions in the UAT paper account (None when disconnected)."""
        return get_ib_uat_service().get_positions()

    def get_open_trades(self):
        """Working orders on the UAT session (None when disconnected)."""
        return get_ib_uat_service().get_open_trades()

    def get_fills(self):
        """Today's real executions on the UAT session (None when disconnected)."""
        return get_ib_uat_service().get_fills()

    def cancel_order(self, order_id):
        """Cancel a working order on the UAT session. Never touches the
        primary session — only orders visible in the UAT session's own
        openTrades can be cancelled."""
        svc = get_ib_uat_service()
        if not svc.is_connected:
            return {"success": False, "error": "Not connected to IBKR UAT paper session", "session": "uat"}
        result = svc.submit_cancel(order_id)
        result["session"] = "uat"
        return result

    def get_status(self):
        """Get UAT session status with diagnostics + config truth."""
        svc = get_ib_uat_service()
        status = svc.get_status()
        host, port, client_id = get_ib_uat_config()
        status.update({
            "session": "uat",
            "host": host,
            "port": port,
            "client_id": client_id,
            "account_type": "PAPER",
        })
        if not status["is_connected"]:
            status["message"] = (
                f"UAT paper session not connected ({host}:{port} client {client_id}). "
                "Start it with POST /api/ib/tws/uat/connect; requires the IBKR paper "
                "gateway to be reachable."
            )
        return status

    async def connect(self):
        """Start the UAT session thread and report status. If the thread is
        already alive but disconnected (e.g. it started before the gateway
        tunnel was up), request an in-thread reconnect and wait for it."""
        self._ensure_started()
        svc = get_ib_uat_service()
        if not svc.is_connected:
            svc.request_reconnect()
        import time
        deadline = time.time() + 12
        while time.time() < deadline:
            if svc.is_connected:
                break
            time.sleep(0.5)
        if svc.is_connected:
            return {"status": "Connected", "session": "uat",
                    "host": self.host, "port": self.port, "client_id": self.client_id,
                    "account": svc.account}
        return {"status": "Failed", "session": "uat",
                "reason": "Gateway not responding on the UAT endpoint. Check IBKR_UAT_HOST/IBKR_UAT_PORT and the paper gateway."}

    def get_account_summary(self):
        """Account summary from the UAT paper session."""
        return _fetch_account_summary(get_ib_uat_service())

    def place_order(self, symbol, action, quantity, order_type="MKT", account=None, order_ref=None):
        """Place an order on the UAT paper session. Never falls back to the
        primary session — a disconnected UAT session is a hard failure.

        order_ref: optional strategy attribution tag (strat:<strategy_id>)
        stamped onto order.orderRef for fill→strategy attribution."""
        svc = get_ib_uat_service()
        if not svc.is_connected:
            logger.error("Cannot place UAT order: UAT session not connected")
            return {"success": False,
                    "error": "Not connected to IBKR UAT paper session",
                    "session": "uat"}
        # Hard account guard (t_03f5687f): the UAT session must be bound to
        # the allowed account; any other account is refused.
        guard_err = account_guard_error(connected_account=svc.account,
                                        requested_account=account)
        if guard_err:
            logger.error(f"UAT order refused: {guard_err}")
            return {"success": False, "error": guard_err, "session": "uat"}
        result = svc.submit_order(symbol, action, quantity, order_type, order_ref=order_ref)
        result["session"] = "uat"
        return result


ib_uat_service = IBKRUatService()
