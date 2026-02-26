"""
IBKR Service - Improved Threaded Implementation with Persistent Connection
Maintains stable connection with automatic reconnection
"""
import threading
import asyncio
import logging
import time
import random
import nest_asyncio
from queue import Queue
from ib_insync import IB, Forex, Stock, MarketOrder

# Allow nested event loops
nest_asyncio.apply()

logger = logging.getLogger(__name__)

class IBKRThreadedService:
    """
    Thread-safe IBKR service with persistent connection and auto-reconnect
    Uses random client IDs to avoid conflicts
    """
    
    def __init__(self, host='52.74.14.181', port=4002, client_id=None):
        self.host = host
        self.port = port
        # Use random client ID if not specified (avoid conflicts)
        self.client_id = client_id or random.randint(1, 100)
        self._ib = None
        self._connected = False
        self._thread = None
        self._loop = None
        self._queue = Queue()
        self._results = {}
        self._last_price_update = {}
        self._running = False
        
    def _get_available_client_id(self):
        """Get an available client ID by trying random IDs"""
        for attempt in range(10):  # Try up to 10 times
            try:
                test_ib = IB()
                test_client_id = random.randint(1, 100)
                test_ib.connect(self.host, self.port, clientId=test_client_id, timeout=3)
                test_ib.disconnect()
                logger.info(f"Found available client ID: {test_client_id}")
                return test_client_id
            except:
                try:
                    test_ib.disconnect()
                except:
                    pass
                continue
        # Fallback to high random number
        return random.randint(100, 999)
        
    def _run_in_thread(self):
        """Run the IBKR event loop in a separate thread with persistent connection"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        while self._running:
            try:
                if not self._connected or not self._ib:
                    # Get available client ID to avoid conflicts
                    self.client_id = self._get_available_client_id()
                    
                    # Connect
                    self._ib = IB()
                    try:
                        self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
                        self._connected = True
                        logger.info(f"IBKR: Connected to {self.host}:{self.port} with client ID {self.client_id}")
                        
                        # Set up error handling
                        self._ib.errorEvent += self._on_error
                        
                    except Exception as e:
                        logger.error(f"IBKR: Connection failed - {e}")
                        self._connected = False
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Keep connection alive by processing events
                self._ib.sleep(1)
                
                # Process any queued requests
                while not self._queue.empty():
                    try:
                        request = self._queue.get_nowait()
                        self._process_request(request)
                    except Exception as e:
                        logger.error(f"IBKR: Error processing request - {e}")
                
                # Check if connection is still alive
                if not self._ib.isConnected():
                    logger.warning("IBKR: Connection lost, reconnecting...")
                    self._connected = False
                    continue
                    
            except Exception as e:
                logger.error(f"IBKR: Thread error - {e}")
                self._connected = False
                time.sleep(5)
    
    def _on_error(self, reqId, errorCode, errorString, contract):
        """Handle IB errors"""
        if errorCode == 1100:  # Connectivity lost
            logger.warning(f"IBKR: Connectivity lost - {errorString}")
            self._connected = False
        elif errorCode == 2104:  # Market data farm OK
            logger.info(f"IBKR: Market data connected")
        elif errorCode == 2106:  # HMDS OK
            logger.info(f"IBKR: Historical data connected")
        elif errorCode not in [2104, 2106, 2107, 2108]:  # Ignore info messages
            logger.warning(f"IBKR Error {errorCode}: {errorString}")
    
    def _process_request(self, request):
        """Process a request from the queue"""
        req_type = request.get('type')
        
        if req_type == 'price':
            symbol = request['symbol']
            price = self._fetch_price_sync(symbol)
            self._results[request['request_id']] = price
    
    def _fetch_price_sync(self, symbol):
        """Fetch price synchronously - uses delayed data if no subscription"""
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
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Request delayed market data (free instead of subscription-required)
            # 101 = delayed frozen, 102 = delayed
            self._ib.reqMarketDataType(3)  # 3 = delayed
            ticker = self._ib.reqMktData(contract, '', False, False)
            
            # Wait for data with timeout
            for _ in range(30):  # 3 seconds max
                self._ib.sleep(0.1)
                
                price = None
                if ticker.last and ticker.last > 0:
                    price = float(ticker.last)
                    break
                elif ticker.close and ticker.close > 0:
                    price = float(ticker.close)
                    break
                elif ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
                    price = float((ticker.bid + ticker.ask) / 2)
                    break
            
            # Cancel market data subscription
            self._ib.cancelMktData(contract)
            
            if price:
                self._last_price_update[symbol] = {
                    'price': price,
                    'timestamp': time.time()
                }
                return price
            
            # Return cached price if available
            if symbol in self._last_price_update:
                cached = self._last_price_update[symbol]
                if time.time() - cached['timestamp'] < 60:  # 1 minute cache
                    return cached['price']
            
            return None
            
        except Exception as e:
            logger.error(f"IBKR: Error fetching price for {symbol} - {e}")
            return None
    
    def start(self):
        """Start the IBKR service"""
        if self._thread is not None and self._thread.is_alive():
            logger.info("IBKR: Service already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()
        logger.info("IBKR: Service started")
        
        # Wait for initial connection
        for _ in range(30):  # 3 seconds max
            if self._connected:
                logger.info("IBKR: Initial connection established")
                break
            time.sleep(0.1)
    
    def stop(self):
        """Stop the IBKR service"""
        self._running = False
        if self._ib:
            try:
                self._ib.disconnect()
            except:
                pass
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("IBKR: Service stopped")
    
    @property
    def is_connected(self):
        """Check if IBKR is connected"""
        return self._connected and self._ib and self._ib.isConnected()
    
    def get_price(self, symbol):
        """Get current market price - uses cached data if available"""
        # Check cache first
        if symbol in self._last_price_update:
            cached = self._last_price_update[symbol]
            if time.time() - cached['timestamp'] < 5:  # 5 second cache
                return cached['price']
        
        if not self.is_connected:
            return None
        
        # Queue a request
        import uuid
        request_id = str(uuid.uuid4())
        request = {
            'type': 'price',
            'symbol': symbol,
            'request_id': request_id
        }
        
        self._results[request_id] = None
        self._queue.put(request)
        
        # Wait for result
        for _ in range(50):  # 5 seconds max
            if self._results[request_id] is not None:
                result = self._results[request_id]
                del self._results[request_id]
                return result
            time.sleep(0.1)
        
        # Timeout - check cache one more time
        if symbol in self._last_price_update:
            return self._last_price_update[symbol]['price']
        
        return None
    
    def get_status(self):
        """Get connection status"""
        return {
            "connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "client_id": self.client_id,
            "cached_prices": len(self._last_price_update)
        }

# Create singleton instance with client_id=20 (fresh after conflict)
ib_threaded_service = IBKRThreadedService(client_id=20)

# Legacy compatibility
class IBKRQuantService:
    """Legacy wrapper for compatibility"""
    def __init__(self, host='52.74.14.181', port=4002, client_id=20):
        self.host = host
        self.port = port
        self.client_id = client_id
        # Auto-start the threaded service
        ib_threaded_service.start()
    
    @property
    def is_connected(self):
        return ib_threaded_service.is_connected
    
    def get_status(self):
        return ib_threaded_service.get_status()
    
    def get_price(self, symbol):
        return ib_threaded_service.get_price(symbol)
    
    def get_live_price_for_execution(self, symbol):
        """Get current market price for trade execution - bypasses cache to get real-time price"""
        # Force a fresh price fetch by clearing cache for this symbol
        if symbol in ib_threaded_service._last_price_update:
            del ib_threaded_service._last_price_update[symbol]
        return ib_threaded_service.get_price(symbol)
    
    def get_account_summary(self):
        """Get account summary"""
        if not ib_threaded_service.is_connected:
            return None
        
        try:
            ib = ib_threaded_service._ib
            if not ib:
                return None
            
            accounts = ib.managedAccounts()
            if not accounts:
                return None
            
            account = accounts[0]
            values = ib.accountValues(account)
            
            result = {
                "account": account,
                "currency": "USD",
                "available_funds": 0,
                "net_liquidation": 0
            }
            
            for v in values:
                if v.tag == "AvailableFunds":
                    result["available_funds"] = float(v.value)
                elif v.tag == "NetLiquidation":
                    result["net_liquidation"] = float(v.value)
                    result["currency"] = v.currency
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return None

    async def connect(self):
        """Connect/reconnect to IBKR Gateway"""
        try:
            # Check if already connected
            if ib_threaded_service.is_connected:
                return {
                    "status": "connected",
                    "message": "Already connected to IBKR Gateway",
                    "host": self.host,
                    "port": self.port,
                    "client_id": ib_threaded_service.client_id
                }
            
            # Try to restart the service
            ib_threaded_service.stop()
            await asyncio.sleep(0.5)
            ib_threaded_service.start()
            
            # Wait for connection
            for _ in range(50):  # 5 seconds max
                if ib_threaded_service.is_connected:
                    return {
                        "status": "success",
                        "message": "Connected to IBKR Gateway",
                        "host": self.host,
                        "port": self.port,
                        "client_id": ib_threaded_service.client_id
                    }
                await asyncio.sleep(0.1)
            
            return {
                "status": "error",
                "message": "Failed to connect to IBKR Gateway within timeout",
                "host": self.host,
                "port": self.port
            }
            
        except Exception as e:
            logger.error(f"Error connecting to IBKR: {e}")
            return {
                "status": "error",
                "message": str(e),
                "host": self.host,
                "port": self.port
            }

    def place_order(self, symbol, action, quantity, order_type='MKT', account=None, strategy_id='manual', current_price=None):
        """Place an order through IBKR - creates fresh connection with collision handling"""
        import asyncio
        from ib_insync import IB, MarketOrder, Stock
        
        async def _place_with_retry(max_retries=3):
            for retry in range(max_retries):
                ib = IB()
                try:
                    # Connect with a unique client ID (random to avoid conflicts)
                    client_id = random.randint(30 + (retry * 50), 100 + (retry * 50))
                    await ib.connectAsync(self.host, self.port, clientId=client_id, timeout=10)
                    
                    # Get account
                    accounts = ib.managedAccounts()
                    if not accounts:
                        return {"success": False, "error": "No accounts available"}
                    acc = account or accounts[0]
                    
                    # Create and qualify contract based on ticker
                    # Handle HK stocks - remove leading zeros for IBKR
                    if symbol.endswith('.HK'):
                        stock_symbol = symbol.replace('.HK', '').lstrip('0') or '0'
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
                    else:
                        contract = Stock(symbol, 'SMART', 'USD')
                    
                    qualified = await ib.qualifyContractsAsync(contract)
                    if not qualified:
                        return {"success": False, "error": f"Could not qualify contract for {symbol}"}
                    
                    contract = qualified[0]
                    
                    # Create order with GTC
                    order = MarketOrder(action, quantity)
                    order.tif = 'GTC'
                    order.account = acc
                    
                    # Place order
                    trade = ib.placeOrder(contract, order)
                    
                    logger.info(f"✅ Order placed: {symbol} {action} x{quantity} - OrderID: {trade.order.orderId} (client {client_id})")
                    
                    return {
                        "success": True,
                        "order_id": trade.order.orderId,
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "status": trade.orderStatus.status if trade.orderStatus else "Pending",
                        "account": acc
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    if "client id" in error_msg.lower() or "already in use" in error_msg.lower():
                        logger.warning(f"Client ID conflict (attempt {retry+1}/{max_retries}), retrying with new ID...")
                        try:
                            ib.disconnect()
                        except:
                            pass
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        logger.error(f"❌ Error placing order: {e}")
                        return {"success": False, "error": str(e)}
                finally:
                    if ib.isConnected():
                        ib.disconnect()
            
            return {"success": False, "error": f"Failed after {max_retries} attempts"}
        
        # Use get_event_loop() instead of run() to handle nested loops
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(_place_with_retry())
            
            # Record order in database if successful
            if result.get('success'):
                self._record_order(result, strategy_id, current_price)
            
            return result
        except Exception as e:
            logger.error(f"❌ Failed to run order placement: {e}")
            return {"success": False, "error": str(e)}
    
    def _record_order(self, order_result, strategy_id='manual', price=None):
        """Record order in database for tracking"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com",
                port=5432,
                user="openclaw_user",
                password=self._get_db_auth_token(),
                database="aitrading",
                sslmode='require',
                options='-c search_path=gold'
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ibkr_orders (order_id, strategy_id, ticker, action, quantity, 
                                        order_type, status, filled, remaining, gtc, notes, price, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, NOW())
                ON CONFLICT (order_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    filled = EXCLUDED.filled,
                    remaining = EXCLUDED.remaining,
                    updated_at = NOW()
            """, (
                str(order_result.get('order_id')),
                strategy_id,
                order_result.get('symbol'),
                order_result.get('action'),
                order_result.get('quantity'),
                'MKT',
                order_result.get('status'),
                0,
                order_result.get('quantity'),
                order_result.get('account', ''),
                price
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"📊 Order recorded in DB: {order_result.get('symbol')} - {order_result.get('order_id')}")
        except Exception as e:
            logger.error(f"Failed to record order: {e}")
    
    def _get_db_auth_token(self):
        """Get RDS auth token"""
        try:
            import boto3
            client = boto3.client('rds', region_name='ap-southeast-1')
            return client.generate_db_auth_token(
                DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
                Port=5432,
                DBUsername='openclaw_user'
            )
        except:
            return None

# Keep the old name for compatibility
ib_quant_service = IBKRQuantService()
