"""
IBKR Service - Threaded Implementation
Isolates ib_insync event loop from FastAPI's async loop
"""
import threading
import asyncio
import logging
from queue import Queue
from ib_insync import IB, Forex, Stock, MarketOrder

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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
        
    def _run_in_thread(self):
        """Run the IBKR event loop in a separate thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._ib = IB()
            # Try to connect
            try:
                self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=5)
                self._connected = True
                logger.info(f"IBKR Thread: Connected to {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"IBKR Thread: Connection failed - {e}")
                self._connected = False
            
            # Keep thread alive processing events
            while True:
                try:
                    # Process any pending commands
                    while not self._queue.empty():
                        cmd = self._queue.get_nowait()
                        if cmd == 'stop':
                            break
                        elif isinstance(cmd, dict) and cmd.get('type') == 'order':
                            # Process order request
                            self._process_order_request(cmd)
                    
                    if self._ib and self._connected:
                        self._ib.sleep(0.1)  # Process IB events
                    else:
                        import time
                        time.sleep(1)
                        
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
            else:
                self._results[request_id] = {"success": False, "error": f"Order type {order_type} not implemented"}
                return
            
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
                    
                    # Also check if we have any execution data
                    if trade.executions:
                        exec = trade.executions[0]
                        fill_price = exec.price
                        logger.info(f"Order executing: {symbol} at ${fill_price:.2f}")
                        break
                
                self._results[request_id] = {
                    "success": True,
                    "order_id": trade.order.orderId,
                    "status": trade.orderStatus.status if trade.orderStatus else "Pending",
                    "fill_price": fill_price,  # IBKR golden source price
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
    
    def submit_order(self, symbol, action, quantity, order_type="MKT"):
        """
        Submit an order to the IBKR queue and wait for result.
        Returns the order result.
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
            'order_type': order_type
        }
        
        # Submit to queue
        self._queue.put(order_request)
        
        # Wait for result (with timeout)
        timeout = 10  # seconds
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

# Legacy compatibility
class IBKRQuantService:
    """Legacy wrapper for compatibility"""
    # Default: 52.74.14.181:4002 (paper trading)
    def __init__(self, host='52.74.14.181', port=4002, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
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
    
    def get_status(self):
        """Get connection status from threaded service"""
        return get_ib_threaded_service().get_status()
    
    def get_account_summary(self):
        """Get account summary - requires connected IB instance with health validation"""
        # First check connection with health validation
        if not get_ib_threaded_service().is_connected:
            logger.warning("Cannot fetch account summary: IBKR not connected")
            return None
        
        try:
            # Access the IB instance from threaded service
            ib = get_ib_threaded_service()._ib
            if not ib:
                logger.warning("IB instance is None despite is_connected=True")
                return None
            
            # Double-check connection is alive before fetching
            if not ib.isConnected():
                logger.warning("IB isConnected() returned False during account fetch")
                get_ib_threaded_service()._connected = False
                return None
            
            # Get account summary
            accounts = ib.managedAccounts()
            if not accounts:
                logger.warning("No managed accounts returned from IB")
                return None
            
            account = accounts[0]
            
            # Get account values with timeout protection
            try:
                values = ib.accountValues(account)
                if values is None:
                    logger.warning("accountValues() returned None")
                    return None
            except Exception as av_err:
                logger.error(f"Error fetching account values: {av_err}")
                return None
            
            result = {
                "account": account,
                "currency": "USD",  # default
                "available_funds": 0,
                "available_funds_hkd": 0,
                "net_liquidation": 0,
                "net_liquidation_hkd": 0,
                "buying_power": 0,
                "buying_power_hkd": 0,
                "excess_liquidity": 0,
                "excess_liquidity_hkd": 0,
                "cash_hkd": 0
            }
            
            for v in values:
                if v.tag == "AvailableFunds":
                    result["available_funds"] = float(v.value)
                elif v.tag == "NetLiquidation":
                    result["net_liquidation"] = float(v.value)
                elif v.tag == "BuyingPower":
                    result["buying_power"] = float(v.value)
                elif v.tag == "ExcessLiquidity":
                    result["excess_liquidity"] = float(v.value)
                elif v.tag == "Currency":
                    result["currency"] = v.value
                
                # HKD specific values (for HK accounts)
                elif v.tag == "AvailableFunds" and v.currency == "HKD":
                    result["available_funds_hkd"] = float(v.value)
                elif v.tag == "NetLiquidation" and v.currency == "HKD":
                    result["net_liquidation_hkd"] = float(v.value)
                elif v.tag == "BuyingPower" and v.currency == "HKD":
                    result["buying_power_hkd"] = float(v.value)
                elif v.tag == "ExcessLiquidity" and v.currency == "HKD":
                    result["excess_liquidity_hkd"] = float(v.value)
                elif v.tag == "CashBalance" and v.currency == "HKD":
                    result["cash_hkd"] = float(v.value)
            
            # If we have HKD values, prioritize those for HK accounts
            # Otherwise use the base currency values
            if result["currency"] == "HKD" or result["cash_hkd"] > 0:
                result["currency"] = "HKD"
                if result["available_funds_hkd"] == 0 and result["available_funds"] > 0:
                    # Use base currency as HKD equivalent (approximate)
                    result["available_funds_hkd"] = result["available_funds"]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            # Mark connection as potentially broken
            get_ib_threaded_service()._connected = False
            return None
    
    async def connect(self):
        """Connect - service starts on demand, just return status"""
        self._ensure_started()
        import time
        time.sleep(1)
        if get_ib_threaded_service().is_connected:
            return {"status": "Connected", "port": self.port}
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
    
    def place_order(self, symbol, action, quantity, order_type="MKT", account=None):
        """
        Place an order through IBKR TWS API.
        Uses the threaded service to ensure proper event loop handling.
        
        Args:
            symbol: Stock/FX symbol
            action: "BUY" or "SELL"
            quantity: Number of shares/contracts
            order_type: Order type (MKT, LMT, etc.)
            account: Account ID (None for default)
            
        Returns:
            dict with success status and order_id
        """
        if not get_ib_threaded_service().is_connected:
            logger.error("Cannot place order: IBKR not connected")
            return {"success": False, "error": "Not connected to IBKR"}
        
        # Use the threaded service's submit_order method
        return get_ib_threaded_service().submit_order(symbol, action, quantity, order_type)
    
    def get_price(self, symbol):
        """Get current market price for a symbol from IBKR"""
        return get_ib_threaded_service().get_price(symbol)

# Keep the old name for compatibility - lazy initialization
ib_quant_service = IBKRQuantService()
