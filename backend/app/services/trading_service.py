from sqlalchemy.orm import Session
from app.db.session import SessionLocal, ConsumptionStock, GlobalState, Trade, Inventory
from app.services.ib_web_service import ib_web_service
import logging
import datetime

logger = logging.getLogger(__name__)

class AutomatedTradeService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def get_automation_policy(self):
        """
        Retrieves trading thresholds from GlobalState.
        """
        min_score = self.db.query(GlobalState).filter(GlobalState.key == "auto_trade_min_score").first()
        is_enabled = self.db.query(GlobalState).filter(GlobalState.key == "auto_trade_enabled").first()
        account_id = self.db.query(GlobalState).filter(GlobalState.key == "ib_account_id").first()
        
        return {
            "min_score": float(min_score.value) if min_score else 0.85,
            "enabled": (is_enabled.value.lower() == "true") if is_enabled else False,
            "account_id": account_id.value if account_id else None
        }

    async def run_signal_execution(self):
        """
        Core loop: Analyzes current signals and triggers trades based on policy.
        """
        policy = self.get_automation_policy()
        if not policy["enabled"]:
            logger.info("Auto-Trade: Disabled in GlobalState. Skipping.")
            return
        
        if not policy["account_id"]:
            logger.warning("Auto-Trade: IB Account ID not configured. Skipping.")
            return

        if not ib_web_service.check_auth():
            logger.warning("Auto-Trade: IBKR not authenticated. Please sync session via dashboard.")
            return

        # 1. Fetch Latest High-Confidence Signals
        # We look for signals generated in the last hour
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
                
                # Logic: If high score and NOT owned -> BUY
                # (Later we can add SELL logic based on 'decision' from analysis)
                if not existing:
                    logger.info(f"Auto-Trade: [BUY] Triggered for {sig.ticker} (Score: {sig.final_score})")
                    
                    # Quantity calculation (simplified: fixed 10 units or fractional value)
                    # This should ideally come from a risk management module
                    qty = 10 
                    
                    result = ib_web_service.execute_order(policy["account_id"], sig.ticker, "BUY", qty)
                    
                    if result["status"] == "success":
                        # Log to Audit Trail
                        new_trade = Trade(
                            ticker=sig.ticker, side="BUY", price=sig.close_price,
                            quantity=qty, total_value=(sig.close_price or 0) * qty,
                            strategy="AI_SWARM_AUTO",
                            pnl=0.0, timestamp=datetime.datetime.now()
                        )
                        self.db.add(new_trade)
                        
                        # Add to Inventory (optimistic, should wait for fill confirmation usually)
                        new_inv = Inventory(
                            ticker=sig.ticker, asset_class="STOCK", quantity=qty,
                            buy_price=sig.close_price, current_price=sig.close_price,
                            status="held", win_loss="0.0%"
                        )
                        self.db.add(new_inv)
                        self.db.commit()
                        logger.info(f"Auto-Trade: SUCCESS for {sig.ticker}")
                    else:
                        logger.error(f"Auto-Trade: EXECUTION FAILED for {sig.ticker}: {result.get('message')}")
                        
            except Exception as e:
                logger.error(f"Auto-Trade: Error processing {sig.ticker}: {e}")
                self.db.rollback()

trading_service = AutomatedTradeService()
