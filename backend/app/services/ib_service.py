import asyncio
from ib_insync import IB, Forex, MarketOrder
import logging

logger = logging.getLogger(__name__)

class IBKRQuantService:
    def __init__(self, host='127.0.0.1', port=4001, client_id=1):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.is_connected = False

    async def connect(self):
        # Iteration 28: Improved error reporting and port detection
        ports = [4001, 7497, 4002, 7496] # Common IB Gateway/TWS ports
        for port in ports:
            try:
                logger.info(f"IBKR: Attempting handshake on port {port}...")
                await self.ib.connectAsync(self.host, port, clientId=self.client_id, timeout=5)
                self.port = port
                self.is_connected = True
                logger.info(f"IBKR Service SUCCESSFULLY connected on port {port}")
                return {"status": "Connected", "port": port}
            except Exception as e:
                logger.warning(f"IBKR: Port {port} refused connection.")
        
        self.is_connected = False
        return {"status": "Failed", "reason": "No local IB Gateway found. Ensure IB Gateway is running on the server."}

    async def get_fx_realtime(self, pair='EURUSD'):
        if not self.is_connected: return None
        contract = Forex(pair)
        self.ib.qualifyContracts(contract)
        ticker = self.ib.reqMktData(contract)
        await asyncio.sleep(1) # Wait for tick
        return {
            "bid": ticker.bid,
            "ask": ticker.ask,
            "last": ticker.last
        }

    async def execute_quant_trade(self, pair, action, quantity):
        """
        Executes an order on IBKR. 
        Action: 'BUY' or 'SELL'
        """
        if not self.is_connected: return {"status": "error", "message": "Not connected to IBKR"}
        
        contract = Forex(pair)
        order = MarketOrder(action, quantity)
        trade = self.ib.placeOrder(contract, order)
        
        # Async wait for fill
        while not trade.isDone():
            await asyncio.sleep(0.5)
            
        return {
            "status": "filled",
            "avgFillPrice": trade.orderStatus.avgFillPrice,
            "orderId": trade.order.orderId
        }

ib_quant_service = IBKRQuantService()
