"""Crypto endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger
import math

def clean_float(val):
    if val is None or (isinstance(val, float) and math.isnan(val)) or (isinstance(val, float) and math.isinf(val)):
        return None
    return val

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


@router.get("/all")
def get_all_crypto(db: Session = Depends(get_db)):
    """Get all crypto data from consumption layer."""
    try:
        cryptos = db.execute(text("""
            SELECT 
                ticker, close_price, volume_24h, market_cap_usd,
                btc_dominance, eth_gas_price_gwei, hash_rate_th_s,
                exchange_inflow_proxy, exchange_outflow_proxy,
                fear_greed_index, stablecoin_supply_ratio, funding_rate,
                open_interest_usd, liquidations_24h_usd,
                rsi_14, macd_histogram, bollinger_width, mvrv_z_score, nvt_ratio,
                prophet_forecast, lsd_divergence_score,
                candlestick_pattern, candlestick_sentiment,
                date
            FROM consumption.crypto
            ORDER BY market_cap_usd DESC NULLS LAST
        """)).fetchall()

        return [{
            "ticker": c.ticker,
            "price": clean_float(c.close_price),
            "volume_24h": clean_float(c.volume_24h),
            "market_cap_usd": clean_float(c.market_cap_usd),
            "btc_dominance": clean_float(c.btc_dominance),
            "eth_gas_price_gwei": clean_float(c.eth_gas_price_gwei),
            "hash_rate_th_s": clean_float(c.hash_rate_th_s),
            "exchange_inflow_proxy": clean_float(c.exchange_inflow_proxy),
            "exchange_outflow_proxy": clean_float(c.exchange_outflow_proxy),
            "fear_greed_index": clean_float(c.fear_greed_index),
            "stablecoin_supply_ratio": clean_float(c.stablecoin_supply_ratio),
            "funding_rate": clean_float(c.funding_rate),
            "open_interest_usd": clean_float(c.open_interest_usd),
            "liquidations_24h_usd": clean_float(c.liquidations_24h_usd),
            "rsi_14": clean_float(c.rsi_14),
            "macd_histogram": clean_float(c.macd_histogram),
            "bollinger_width": clean_float(c.bollinger_width),
            "mvrv_z_score": clean_float(c.mvrv_z_score),
            "nvt_ratio": clean_float(c.nvt_ratio),
            "prophet_forecast": clean_float(c.prophet_forecast),
            "lsd_divergence_score": clean_float(c.lsd_divergence_score),
            "candlestick_pattern": c.candlestick_pattern,
            "candlestick_sentiment": c.candlestick_sentiment,
            "date": c.date.isoformat() if c.date else None,
        } for c in cryptos]
    except Exception as e:
        logger.error(f"Crypto API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
