"""
Telegram Alert Service for Trading Platform
Sends notifications for trades, drawdowns, and system events
"""

import logging
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, QuantStrategy, get_hkt_now

logger = logging.getLogger(__name__)


class TelegramAlertService:
    """Service for sending Telegram alerts"""
    
    def __init__(self, db: Session = None):
        self._db = db
        self._session = None
        self.bot_token = None
        self.chat_id = None
        self.enabled = False
        self._load_config()
    
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
    
    def _load_config(self):
        """Load Telegram configuration from database or environment"""
        try:
            # Try to load from GlobalState or environment
            import os
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if self.bot_token and self.chat_id:
                self.enabled = True
                logger.info(f"Telegram alerts enabled for chat {self.chat_id}")
            else:
                logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        except Exception as e:
            logger.error(f"Failed to load Telegram config: {e}")
    
    def configure(self, bot_token: str, chat_id: str) -> bool:
        """Configure Telegram alerts"""
        try:
            self.bot_token = bot_token
            self.chat_id = chat_id
            
            # Test the configuration
            if self._test_connection():
                self.enabled = True
                
                # Store in environment for persistence (optional)
                import os
                os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
                os.environ['TELEGRAM_CHAT_ID'] = chat_id
                
                logger.info("Telegram configuration saved and tested successfully")
                return True
            else:
                self.enabled = False
                return False
        except Exception as e:
            logger.error(f"Failed to configure Telegram: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test Telegram API connection"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data['result'].get('username', 'Unknown')
                    logger.info(f"Connected to Telegram bot: @{bot_name}")
                    return True
            
            logger.error(f"Telegram test failed: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def _send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram"""
        if not self.enabled or not self.bot_token or not self.chat_id:
            logger.debug("Telegram not enabled, skipping message")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200 and response.json().get('ok'):
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    # === TRADE ALERTS ===
    
    def alert_trade_executed(self, strategy_name: str, ticker: str, side: str, 
                             quantity: float, price: float, pnl: Optional[float] = None):
        """Alert when a trade is executed"""
        emoji = "🟢" if side == "BUY" else "🔴"
        pnl_text = f"\n💰 P&L: ${pnl:,.2f}" if pnl else ""
        
        message = f"""
{emoji} <b>TRADE EXECUTED</b>

📊 Strategy: <b>{strategy_name}</b>
💱 Ticker: {ticker}
📈 Side: <b>{side}</b>
🔢 Quantity: {quantity:,.0f}
💵 Price: ${price:,.4f}
💵 Value: ${quantity * price:,.2f}{pnl_text}

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    def alert_trade_signal(self, strategy_name: str, ticker: str, signal: str, 
                          confidence: float, price: float):
        """Alert when a trading signal is generated"""
        emoji = "🟢" if "BUY" in signal or "LONG" in signal else "🔴" if "SELL" in signal or "SHORT" in signal else "⚪"
        
        message = f"""
{emoji} <b>TRADE SIGNAL</b>

📊 Strategy: <b>{strategy_name}</b>
💱 Ticker: {ticker}
📈 Signal: <b>{signal}</b>
🎯 Confidence: {confidence*100:.1f}%
💵 Price: ${price:,.4f}

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    # === RISK ALERTS ===
    
    def alert_drawdown(self, strategy_name: str, drawdown_pct: float, 
                       current_pnl: float, allocated: float):
        """Alert on significant drawdown"""
        if drawdown_pct >= 15:
            level = "🔴 CRITICAL"
        elif drawdown_pct >= 10:
            level = "🟠 HIGH"
        elif drawdown_pct >= 5:
            level = "🟡 MEDIUM"
        else:
            return False  # Don't alert for small drawdowns
        
        message = f"""
{level} <b>DRAWDOWN ALERT</b>

📊 Strategy: <b>{strategy_name}</b>
📉 Drawdown: <b>{drawdown_pct:.1f}%</b>
💰 Current P&L: ${current_pnl:,.2f}
💵 Allocated: ${allocated:,.2f}

⚠️ Consider reviewing or stopping this strategy.

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    def alert_portfolio_drawdown(self, total_pnl: float, total_allocated: float, 
                                 drawdown_pct: float):
        """Alert on portfolio-level drawdown"""
        if drawdown_pct >= 10:
            level = "🔴 CRITICAL"
        elif drawdown_pct >= 7:
            level = "🟠 HIGH"
        elif drawdown_pct >= 5:
            level = "🟡 MEDIUM"
        else:
            return False
        
        message = f"""
{level} <b>PORTFOLIO DRAWDOWN</b>

📊 Total Portfolio
📉 Drawdown: <b>{drawdown_pct:.1f}%</b>
💰 Total P&L: ${total_pnl:,.2f}
💵 Total Allocated: ${total_allocated:,.2f}

⚠️ Review all strategies immediately.

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    # === SYSTEM ALERTS ===
    
    def alert_backend_restart(self, reason: str = ""):
        """Alert when backend restarts"""
        reason_text = f"\n📝 Reason: {reason}" if reason else ""
        
        message = f"""
🔄 <b>BACKEND RESTARTED</b>

✅ Trading backend has been restarted.{reason_text}

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    def alert_strategy_mode_change(self, strategy_name: str, old_mode: str, new_mode: str):
        """Alert when strategy execution mode changes"""
        emoji = "🟢" if new_mode == "LIVE" else "🟡" if new_mode == "PAPER" else "⚪"
        
        message = f"""
{emoji} <b>STRATEGY MODE CHANGED</b>

📊 Strategy: <b>{strategy_name}</b>
🔄 {old_mode} → <b>{new_mode}</b>

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    def alert_ibkr_disconnect(self):
        """Alert when IBKR connection is lost"""
        message = f"""
🔴 <b>IBKR DISCONNECTED</b>

⚠️ Connection to Interactive Brokers lost.
Trading execution may be affected.

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    # === DAILY SUMMARY ===
    
    def send_daily_summary(self, strategies: list, total_pnl: float, 
                          total_allocated: float, total_trades: int):
        """Send daily portfolio summary"""
        return_pct = (total_pnl / total_allocated * 100) if total_allocated else 0
        emoji = "🟢" if return_pct >= 0 else "🔴"
        
        # Top performers
        top_strategies = sorted(strategies, 
                               key=lambda s: s.get('current_pnl', 0) or 0, 
                               reverse=True)[:3]
        
        top_text = ""
        for s in top_strategies:
            pnl = s.get('current_pnl', 0) or 0
            top_text += f"\n  • {s['name']}: ${pnl:,.2f}"
        
        message = f"""
📊 <b>DAILY PORTFOLIO SUMMARY</b>

{emoji} Total Return: <b>{return_pct:+.2f}%</b>
💰 Total P&L: ${total_pnl:,.2f}
📈 Total Trades: {total_trades}
💵 Total Allocated: ${total_allocated:,.2f}

🏆 Top Strategies:{top_text}

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(message)
    
    def send_custom_alert(self, title: str, message: str, level: str = "INFO"):
        """Send a custom alert"""
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🔴",
            "SUCCESS": "✅"
        }
        emoji = emoji_map.get(level, "ℹ️")
        
        full_message = f"""
{emoji} <b>{title.upper()}</b>

{message}

⏰ {get_hkt_now().strftime('%Y-%m-%d %H:%M:%S')} HKT
"""
        return self._send_message(full_message)
    
    def get_status(self) -> Dict[str, Any]:
        """Get alert service status"""
        return {
            "enabled": self.enabled,
            "bot_token_configured": bool(self.bot_token),
            "chat_id_configured": bool(self.chat_id),
            "bot_token_preview": f"{self.bot_token[:10]}..." if self.bot_token else None,
            "chat_id": self.chat_id
        }


# Initialize global instance
telegram_alerts = TelegramAlertService()