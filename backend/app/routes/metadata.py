"""Metadata endpoints — formulas, thresholds, configs, signals."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger
import math

from decimal import Decimal

def clean_float(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/signals/1")
def get_signals_v1(db: Session = Depends(get_db)):
    """Get all asset signals from consumption layer — DB only.
    
    NOTE: Uses DISTINCT ON + LIMIT to avoid duplicate historical rows
    that bloat the response. ETL manager should deduplicate source tables.
    """
    try:
        stocks = db.execute(text("""
            SELECT DISTINCT ON (ticker)
                   ticker, name, price, change_pct, change_value, trend, rsi_14,
                   distance_to_52w_high_pct, distance_to_52w_low_pct,
                   market_cap, pe_ratio, forward_pe, pb_ratio, dividend_yield,
                   strategy_signals, top_strategy_score, signal, signal_strength,
                   updated_at
            FROM consumption.stock
            ORDER BY ticker, updated_at DESC NULLS LAST
        """)).fetchall()

        markets = db.execute(text("""
            SELECT DISTINCT ON (index_ticker)
                   region, index_name, index_ticker, current_value, change_pct,
                   change_value, trend, sentiment_score, volatility_index, updated_at
            FROM consumption.market
            WHERE index_ticker IS NOT NULL
            ORDER BY index_ticker, updated_at DESC NULLS LAST
        """)).fetchall()

        fx = db.execute(text("""
            SELECT DISTINCT ON (ticker)
                   ticker, close_price, log_return, interest_rate_diff,
                   dxy_correlation, volatility_24h, rsi_14, macd_histogram,
                   bollinger_width, prophet_forecast, market_regime,
                   candlestick_pattern, candlestick_sentiment, date
            FROM consumption.fx
            ORDER BY ticker, date DESC NULLS LAST
        """)).fetchall()

        commodities = db.execute(text("""
            SELECT DISTINCT ON (ticker)
                   *
            FROM consumption.commodity
            ORDER BY ticker, updated_at DESC NULLS LAST
        """)).fetchall()

        cryptos = db.execute(text("""
            SELECT DISTINCT ON (ticker)
                   ticker, close_price, volume_24h, market_cap_usd,
                   fear_greed_index, funding_rate, rsi_14, macd_histogram,
                   bollinger_width, mvrv_z_score, nvt_ratio,
                   candlestick_pattern, candlestick_sentiment, date
            FROM consumption.crypto
            ORDER BY ticker, date DESC NULLS LAST
        """)).fetchall()

        def fmt_stock(row):
            return {
                "ticker": row.ticker, "asset": row.name, "category": "stock",
                "price": clean_float(row.price), "change": clean_float(row.change_value),
                "change_pct": clean_float(row.change_pct),
                "action": row.signal, "total_confidence": clean_float(row.signal_strength),
                "trend": row.trend, "rsi_14": clean_float(row.rsi_14),
                "market_cap": clean_float(row.market_cap), "pe_ratio": clean_float(row.pe_ratio),
                "forward_pe": clean_float(row.forward_pe), "pb_ratio": clean_float(row.pb_ratio),
                "dividend_yield": clean_float(row.dividend_yield),
                "strategy_signals": row.strategy_signals,
                "top_strategy_score": clean_float(row.top_strategy_score),
                "timestamp": row.updated_at.isoformat() if row.updated_at else None,
            }

        def fmt_market(row):
            return {
                "ticker": row.index_ticker, "asset": row.index_name, "category": "market",
                "price": clean_float(row.current_value), "change": clean_float(row.change_value),
                "change_pct": clean_float(row.change_pct),
                "action": row.trend, "total_confidence": clean_float(row.sentiment_score),
                "region": row.region, "volatility_index": clean_float(row.volatility_index),
                "timestamp": row.updated_at.isoformat() if row.updated_at else None,
            }

        def fmt_fx(row):
            return {
                "ticker": row.ticker, "asset": row.ticker, "category": "fx",
                "price": clean_float(row.close_price), "change": clean_float(row.log_return),
                "action": row.market_regime, "total_confidence": clean_float(row.rsi_14),
                "rsi_14": clean_float(row.rsi_14), "macd_histogram": clean_float(row.macd_histogram),
                "bollinger_width": clean_float(row.bollinger_width),
                "prophet_forecast": clean_float(row.prophet_forecast),
                "candlestick_pattern": row.candlestick_pattern,
                "candlestick_sentiment": row.candlestick_sentiment,
                "timestamp": row.date.isoformat() if row.date else None,
            }

        def fmt_commodity(row):
            return {
                "ticker": getattr(row, 'ticker', None),
                "asset": getattr(row, 'asset_name', getattr(row, 'name', None)),
                "category": "commodity",
                "price": getattr(row, 'close_price', getattr(row, 'price', None)),
                "change": getattr(row, 'daily_change', getattr(row, 'change', None)),
                "action": getattr(row, 'action', None),
                "timestamp": getattr(row, 'timestamp', getattr(row, 'date', None)),
            }

        def fmt_crypto(row):
            return {
                "ticker": row.ticker, "asset": row.ticker, "category": "crypto",
                "price": clean_float(row.close_price), "change": None,
                "action": None, "total_confidence": clean_float(row.rsi_14),
                "rsi_14": clean_float(row.rsi_14), "macd_histogram": clean_float(row.macd_histogram),
                "bollinger_width": clean_float(row.bollinger_width),
                "mvrv_z_score": clean_float(row.mvrv_z_score), "nvt_ratio": clean_float(row.nvt_ratio),
                "fear_greed_index": clean_float(row.fear_greed_index),
                "funding_rate": clean_float(row.funding_rate),
                "candlestick_pattern": row.candlestick_pattern,
                "candlestick_sentiment": row.candlestick_sentiment,
                "timestamp": row.date.isoformat() if row.date else None,
            }

        return (
            [fmt_stock(s) for s in stocks] +
            [fmt_market(m) for m in markets] +
            [fmt_fx(f) for f in fx] +
            [fmt_commodity(c) for c in commodities] +
            [fmt_crypto(c) for c in cryptos]
        )
    except Exception as e:
        logger.error(f"Signals API Error: {e}")
        return []


@router.get("/commodities/all")
def get_all_commodities(db: Session = Depends(get_db)):
    """Get all commodity data from consumption layer."""
    try:
        commodities = db.execute(text("SELECT * FROM consumption.commodity")).fetchall()
        return [{
            "ticker": getattr(c, 'ticker', None),
            "asset": getattr(c, 'asset_name', getattr(c, 'name', None)),
            "price": getattr(c, 'close_price', getattr(c, 'price', None)),
            "change": getattr(c, 'daily_change', getattr(c, 'change', None)),
            "action": getattr(c, 'action', None),
            "timestamp": getattr(c, 'timestamp', getattr(c, 'date', None)),
        } for c in commodities]
    except Exception as e:
        logger.error(f"Commodity API Error: {e}")
        return []


@router.get("/metadata/formulas")
def get_formulas():
    return {
        "traditional_confidence": "Average of (RSI_signal, MACD_signal, BB_signal, Stoch_signal)",
        "swarm_confidence": "AI agent swarm consensus (1-10 scale, divided by 10)",
        "total_confidence": "70% × trad_confidence + 30% × swarm_confidence",
        "rec_score": "total_confidence × (win_rate / 100)",
    }


@router.get("/metadata/thresholds")
def get_thresholds():
    return {
        "RSI": {"overbought": 70, "oversold": 30},
        "Stochastic": {"overbought": 80, "oversold": 20},
        "MACD": "Histogram crossover",
        "Bollinger": "Touch lower band = bullish, upper = bearish",
        "Confidence": {"high": ">70%", "medium": "50-70%", "low": "<50%"},
    }


@router.get("/metadata/sync_schedules")
def get_sync_schedules(db: Session = Depends(get_db)):
    """Get current sync schedule config — read only (DE manages schedules)."""
    try:
        result = db.execute(text("SELECT component, frequency, last_run FROM gold.sync_schedules")).fetchall()
        return [{"component": r.component, "frequency": r.frequency,
                 "last_run": r.last_run.isoformat() if r.last_run else None} for r in result]
    except Exception as e:
        return {"error": str(e)}


@router.get("/metadata/strategy_configs")
def get_strategy_configs(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT * FROM gold.strategy_configs")).fetchall()
        return [dict(r._mapping) for r in result]
    except Exception as e:
        return {"error": str(e)}
