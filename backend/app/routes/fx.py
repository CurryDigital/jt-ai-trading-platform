"""FX endpoints — pairs, streaming, bars, alerts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger
import math

def clean_float(val):
    if val is None or (isinstance(val, float) and math.isnan(val)) or (isinstance(val, float) and math.isinf(val)):
        return None
    return val

router = APIRouter(prefix="/api/fx", tags=["fx"])


@router.get("/pairs")
def get_fx_pairs(db: Session = Depends(get_db)):
    """Get all FX pair data from consumption layer."""
    try:
        rows = db.execute(text("""
            SELECT
                ticker, close_price, log_return, interest_rate_diff,
                dxy_correlation, volatility_24h, rsi_14, macd_histogram,
                bollinger_width, prophet_forecast, market_regime,
                candlestick_pattern, candlestick_sentiment,
                stoch_k, stoch_d, stoch_oversold, stoch_overbought,
                adx, adx_plus_di, adx_minus_di, adx_trend_strength,
                psar, psar_direction, psar_flip,
                macd_line, macd_signal,
                open, high, low, atr_14, volatility_20d,
                sma_5, sma_20, sma_50,
                date
            FROM consumption.fx
            ORDER BY date DESC NULLS LAST
        """)).fetchall()
        return [{
            "ticker": r.ticker,
            "price": clean_float(r.close_price),
            "log_return": clean_float(r.log_return),
            "interest_rate_diff": clean_float(r.interest_rate_diff),
            "dxy_correlation": clean_float(r.dxy_correlation),
            "volatility_24h": clean_float(r.volatility_24h),
            "rsi_14": clean_float(r.rsi_14),
            "macd_histogram": clean_float(r.macd_histogram),
            "bollinger_width": clean_float(r.bollinger_width),
            "prophet_forecast": clean_float(r.prophet_forecast),
            "market_regime": r.market_regime,
            "candlestick_pattern": r.candlestick_pattern,
            "candlestick_sentiment": r.candlestick_sentiment,
            "stoch_k": clean_float(r.stoch_k),
            "stoch_d": clean_float(r.stoch_d),
            "stoch_oversold": r.stoch_oversold,
            "stoch_overbought": r.stoch_overbought,
            "adx": clean_float(r.adx),
            "adx_plus_di": clean_float(r.adx_plus_di),
            "adx_minus_di": clean_float(r.adx_minus_di),
            "adx_trend_strength": r.adx_trend_strength,
            "psar": clean_float(r.psar),
            "psar_direction": r.psar_direction,
            "psar_flip": r.psar_flip,
            "macd_line": clean_float(r.macd_line),
            "macd_signal": clean_float(r.macd_signal),
            "open": clean_float(r.open),
            "high": clean_float(r.high),
            "low": clean_float(r.low),
            "atr_14": clean_float(r.atr_14),
            "volatility_20d": clean_float(r.volatility_20d),
            "sma_5": clean_float(r.sma_5),
            "sma_20": clean_float(r.sma_20),
            "sma_50": clean_float(r.sma_50),
            "date": r.date.isoformat() if r.date else None,
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
                SELECT timestamp, ticker, open, high, low, close, volume
                FROM gold.fx_bars_5s WHERE ticker = :ticker
                ORDER BY timestamp DESC LIMIT :limit
            """), {"ticker": ticker, "limit": limit}).fetchall()
        else:
            bars = db.execute(text("""
                SELECT DISTINCT ON (ticker)
                    timestamp, ticker, open, high, low, close, volume
                FROM gold.fx_bars_5s
                WHERE ticker IN ('EURUSD', 'USDJPY', 'GBPUSD')
                ORDER BY ticker, timestamp DESC
            """)).fetchall()

        return [{
            "timestamp": b.timestamp.isoformat() if b.timestamp else None,
            "ticker": b.ticker, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
            "volume": b.volume,
        } for b in bars]
    except Exception as e:
        return {"error": str(e)}


@router.get("/streaming/alerts")
def get_fx_streaming_alerts(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent FX spread alerts."""
    try:
        alerts = db.execute(text("""
            SELECT timestamp, ticker, alert_type, severity, message, value, threshold, acknowledged
            FROM gold.fx_alerts ORDER BY timestamp DESC LIMIT :limit
        """), {"limit": limit}).fetchall()
        return [{
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "ticker": a.ticker, "type": a.alert_type, "severity": a.severity,
            "message": a.message, "value": a.value, "threshold": a.threshold,
            "acknowledged": a.acknowledged,
        } for a in alerts]
    except Exception as e:
        return {"error": str(e)}
