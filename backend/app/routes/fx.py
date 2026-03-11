"""FX endpoints — pairs, streaming, bars, alerts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/fx", tags=["fx"])


@router.get("/pairs")
def get_fx_pairs(db: Session = Depends(get_db)):
    """Get all FX pair data from consumption layer."""
    try:
        rows = db.execute(text("""
            SELECT * FROM consumption.fx ORDER BY total_confidence DESC
        """)).fetchall()
        return [{
            "ticker": r.ticker, "asset": r.asset_name, "price": r.close_price,
            "change": r.daily_change, "action": r.action,
            "total_confidence": r.total_confidence, "trad_confidence": r.trad_confidence,
            "swarm_confidence": r.swarm_confidence,
            "est_1d": r.est_1d, "est_7d": r.est_7d, "est_1m": r.est_1m,
            "win_rate": r.win_rate, "rec_score": r.rec_score,
            "candlestick_pattern": r.candlestick_pattern, "logic": r.logic,
            "sparkline": r.sparkline,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        } for r in rows]
    except Exception as e:
        logger.error(f"FX API Error: {e}")
        return []


@router.get("/streaming/status")
def get_fx_streaming_status():
    """Check FX streaming service status."""
    try:
        from app.services.fx_streaming_service import fx_streaming_service
        return {
            "is_connected": fx_streaming_service.is_connected,
            "pairs": fx_streaming_service.FX_PAIRS,
            "subscribed": list(fx_streaming_service.tickers.keys()) if fx_streaming_service.tickers else [],
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/bars/latest")
def get_fx_bars_latest(ticker: str = None, limit: int = 12, db: Session = Depends(get_db)):
    """Get latest 5-second FX bars."""
    try:
        if ticker:
            bars = db.execute(text("""
                SELECT bucket, ticker, open, high, low, close,
                       bid_close, ask_close, spread_avg_bps, tick_count
                FROM gold.fx_bars_5s WHERE ticker = :ticker
                ORDER BY bucket DESC LIMIT :limit
            """), {"ticker": ticker, "limit": limit}).fetchall()
        else:
            bars = db.execute(text("""
                SELECT DISTINCT ON (ticker)
                    bucket, ticker, open, high, low, close,
                    bid_close, ask_close, spread_avg_bps, tick_count
                FROM gold.fx_bars_5s
                WHERE ticker IN ('EURUSD', 'USDJPY', 'GBPUSD')
                ORDER BY ticker, bucket DESC
            """)).fetchall()

        return [{
            "bucket": b.bucket.isoformat() if b.bucket else None,
            "ticker": b.ticker, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
            "bid": b.bid_close, "ask": b.ask_close, "spread_bps": b.spread_avg_bps, "ticks": b.tick_count,
        } for b in bars]
    except Exception as e:
        return {"error": str(e)}


@router.get("/streaming/alerts")
def get_fx_streaming_alerts(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent FX spread alerts."""
    try:
        alerts = db.execute(text("""
            SELECT timestamp, ticker, alert_type, spread_bps, threshold_bps, message
            FROM gold.fx_alerts ORDER BY timestamp DESC LIMIT :limit
        """), {"limit": limit}).fetchall()
        return [{
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "ticker": a.ticker, "type": a.alert_type,
            "spread_bps": a.spread_bps, "threshold_bps": a.threshold_bps, "message": a.message,
        } for a in alerts]
    except Exception as e:
        return {"error": str(e)}
