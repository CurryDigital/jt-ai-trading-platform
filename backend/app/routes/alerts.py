"""Telegram alert endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/config")
def get_alert_config(db: Session = Depends(get_db)):
    """Get telegram alert configuration."""
    try:
        from app.services.telegram_alerts import TelegramAlerts
        ta = TelegramAlerts()
        return {"enabled": ta.enabled, "chat_id": ta.chat_id, "thresholds": ta.get_thresholds()}
    except Exception as e:
        return {"enabled": False, "error": str(e)}


@router.post("/config")
def update_alert_config(payload: dict, db: Session = Depends(get_db)):
    """Update telegram alert configuration."""
    try:
        from app.services.telegram_alerts import TelegramAlerts
        ta = TelegramAlerts()
        ta.update_thresholds(payload)
        return {"success": True, "thresholds": ta.get_thresholds()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/test")
def test_alert(db: Session = Depends(get_db)):
    """Send a test telegram alert."""
    try:
        from app.services.telegram_alerts import TelegramAlerts
        ta = TelegramAlerts()
        success = ta.send_test_message()
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/send-daily-summary")
def send_daily_summary(db: Session = Depends(get_db)):
    """Manually send a daily summary to Telegram."""
    try:
        from app.services.telegram_alerts import TelegramAlerts
        ta = TelegramAlerts()

        strategies = db.execute(text("""
            SELECT name, conviction_score as current_pnl FROM gold.strategy_registry WHERE status = 'ACTIVE' AND asset_class = 'quant'
        """)).fetchall()

        total_pnl = sum(s.current_pnl or 0 for s in strategies)
        strategy_list = [{"name": s.name, "current_pnl": s.current_pnl or 0} for s in strategies]

        success = ta.send_daily_summary(
            strategies=strategy_list, total_pnl=total_pnl,
            total_allocated=100000, total_trades=0,
        )
        return {"status": "sent" if success else "failed"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
