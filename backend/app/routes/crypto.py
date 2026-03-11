"""Crypto endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


@router.get("/all")
def get_all_crypto(db: Session = Depends(get_db)):
    """Get all crypto data from consumption layer."""
    try:
        cryptos = db.execute(text("""
            SELECT * FROM consumption.crypto ORDER BY total_confidence DESC
        """)).fetchall()

        return [{
            "ticker": c.ticker, "asset": c.asset_name, "price": c.close_price,
            "change": c.daily_change, "action": c.action,
            "total_confidence": c.total_confidence, "trad_confidence": c.trad_confidence,
            "swarm_confidence": c.swarm_confidence,
            "est_1d": c.est_1d, "est_7d": c.est_7d, "est_1m": c.est_1m,
            "win_rate": c.win_rate, "rec_score": c.rec_score,
            "mvrv_z_score": c.mvrv_z_score, "fear_greed_index": c.fear_greed_index,
            "funding_rate": c.funding_rate, "gas_price_gwei": c.gas_price_gwei,
            "candlestick_pattern": c.candlestick_pattern, "logic": c.logic,
            "sparkline": c.sparkline,
            "timestamp": c.timestamp.isoformat() if c.timestamp else None,
        } for c in cryptos]
    except Exception as e:
        logger.error(f"Crypto API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
