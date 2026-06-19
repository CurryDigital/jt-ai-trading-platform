"""
Automated Trading Service - TWS API Primary

Path 2 Implementation: Uses TWS API (ib_insync) for automated execution
Web API is fallback only for emergency/manual trading via dashboard
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, ConsumptionStock, GlobalState, Trade, Inventory
from app.services.ib_service import ib_quant_service
from app.services.ib_web_service import ib_web_service
import logging
import datetime

logger = logging.getLogger(__name__)

class AutomatedTradeService:
    """
    Automated trading with TWS API as primary execution venue.
    
    Architecture:
    - Primary: TWS API (socket-based, persistent, for automation)
    - Fallback: Web API (cookie-based, for emergency/manual)
    - Simulation: Paper trading mode
    """
    
    def __init__(self, db: Session = None):
        self._db = db
        self._session = None
        self.execution_mode = "TWS_API"  # TWS_API | WEB_API | SIMULATION

    @property
    def db(self):
        if self._db is not None:
            return self._db
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    def get_automation_policy(self):
        """
        Retrieves trading thresholds from GlobalState.
        """
        min_score = self.db.query(GlobalState).filter(GlobalState.key == "auto_trade_min_score").first()
        is_enabled = self.db.query(GlobalState).filter(GlobalState.key == "auto_trade_enabled").first()
        
        return {
            "min_score": float(min_score.value) if min_score else 0.85,
            "enabled": (is_enabled.value.lower() == "true") if is_enabled else False,
        }

    async def ensure_ib_connection(self):
        """
        Ensure TWS API is connected. Try to reconnect if not.
        """
        if ib_quant_service.is_connected:
            return True
        
        logger.info("Auto-Trade: TWS API not connected, attempting reconnect...")
        result = await ib_quant_service.connect()
        
        if result['status'] == 'Connected':
            logger.info(f"Auto-Trade: TWS API connected on port {result.get('port')}")
            return True
        else:
            logger.warning(f"Auto-Trade: TWS API connection failed: {result.get('reason')}")
            return False

    async def execute_trade(self, ticker, action, quantity, asset_class="STOCK"):
        """
        Execute trade using best available method.
        
        Priority:
        1. TWS API (if connected)
        2. Web API (if authenticated)
        3. Simulation (if neither available)
        """
        result = None
        method_used = None
        
        # Try 1: TWS API (Primary for automation)
        if await self.ensure_ib_connection():
            try:
                # Format pair for FX
                if asset_class == "FX":
                    pair = ticker.replace("=X", "")
                    result = await ib_quant_service.execute_quant_trade(pair, action, quantity)
                else:
                    # Stocks via TWS (would need Stock contract, not implemented yet)
                    logger.warning("Auto-Trade: Stock execution via TWS not implemented, trying Web API")
                    result = None
                
                if result and result.get("status") == "filled":
                    method_used = "TWS_API"
                    logger.info(f"Auto-Trade: Executed via TWS API - {ticker} {action} {quantity}")
            except Exception as e:
                logger.error(f"Auto-Trade: TWS API execution failed: {e}")
                result = None
        
        # Try 2: Web API (Fallback)
        if not result:
            account_id = self._get_account_id()
            if account_id and ib_web_service.check_auth():
                try:
                    result = ib_web_service.execute_order(account_id, ticker, action, quantity)
                    if result.get("status") == "success":
                        method_used = "WEB_API"
                        logger.info(f"Auto-Trade: Executed via Web API (fallback) - {ticker} {action} {quantity}")
                except Exception as e:
                    logger.error(f"Auto-Trade: Web API execution failed: {e}")
                    result = None
        
        # Try 3: Simulation (Last resort)
        if not result:
            result = {
                "status": "simulated",
                "orderId": f"SIM_{datetime.datetime.now().timestamp()}",
                "message": "Trade simulated - no live execution available"
            }
            method_used = "SIMULATION"
            logger.info(f"Auto-Trade: Simulated trade - {ticker} {action} {quantity}")
        
        return result, method_used

    def _get_account_id(self):
        """Get IB account ID from config"""
        account_row = self.db.query(GlobalState).filter(GlobalState.key == "ib_account_id").first()
        return account_row.value if account_row else None

    async def run_signal_execution(self):
        """
        Core loop: Analyzes current signals and triggers trades based on policy.
        """
        policy = self.get_automation_policy()
        if not policy["enabled"]:
            logger.info("Auto-Trade: Disabled in GlobalState. Skipping.")
            return

        # Check TWS API connection first
        tws_available = await self.ensure_ib_connection()
        
        # Also check Web API as backup
        web_available = ib_web_service.check_auth()
        
        if not tws_available and not web_available:
            logger.warning("Auto-Trade: No execution method available (TWS down, Web not auth). Skipping.")
            return
        
        logger.info(f"Auto-Trade: Execution methods - TWS: {tws_available}, Web: {web_available}")

        # 1. Fetch Latest High-Confidence Signals
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        signals = self.db.query(ConsumptionStock).filter(
            ConsumptionStock.final_score >= policy["min_score"],
            ConsumptionStock.timestamp >= cutoff
        ).all()

        logger.info(f"Auto-Trade: Found {len(signals)} candidate signals.")

        for sig in signals:
            try:
                # 2. Check if we already own this ticker
                existing = self.db.query(Inventory).filter(Inventory.ticker == sig.ticker).first()
                
                if not existing:
                    logger.info(f"Auto-Trade: [BUY] Triggered for {sig.ticker} (Score: {sig.final_score})")
                    
                    # Quantity calculation (simplified)
                    qty = 10 
                    
                    # Execute via best available method
                    result, method = await self.execute_trade(
                        sig.ticker, "BUY", qty, asset_class="STOCK"
                    )
                    
                    if result and result.get("status") in ["success", "filled", "simulated"]:
                        # Log to Audit Trail
                        new_trade = Trade(
                            ticker=sig.ticker, 
                            side="BUY", 
                            price=sig.close_price,
                            quantity=qty, 
                            total_value=(sig.close_price or 0) * qty,
                            strategy=f"AI_SWARM_AUTO ({method})",
                            pnl=0.0, 
                            timestamp=datetime.datetime.now()
                        )
                        self.db.add(new_trade)
                        
                        # Add to Inventory (optimistic)
                        new_inv = Inventory(
                            ticker=sig.ticker, 
                            asset_class="STOCK", 
                            quantity=qty,
                            buy_price=sig.close_price, 
                            current_price=sig.close_price,
                            status="held", 
                            win_loss="0.0%"
                        )
                        self.db.add(new_inv)
                        self.db.commit()
                        logger.info(f"Auto-Trade: SUCCESS for {sig.ticker} via {method}")
                    else:
                        logger.error(f"Auto-Trade: EXECUTION FAILED for {sig.ticker}: {result.get('message') if result else 'Unknown error'}")
                        
            except Exception as e:
                logger.error(f"Auto-Trade: Error processing {sig.ticker}: {e}")
                self.db.rollback()

    async def execute_fx_trade(self, pair, action, quantity):
        """
        Specialized FX trade execution.
        Uses TWS API directly for FX pairs.
        """
        pair_clean = pair.replace("=X", "").replace(".", "")
        
        result, method = await self.execute_trade(
            pair, action, quantity, asset_class="FX"
        )
        
        return result, method

trading_service = AutomatedTradeService()
