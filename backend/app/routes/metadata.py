"""Metadata endpoints — formulas, thresholds, configs, signals."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger
from app.db.session import ConsumptionStock, ConsumptionMarket, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/signals/1")
def get_signals_v1(db: Session = Depends(get_db)):
    """Get all asset signals from consumption layer — DB only."""
    try:
        stocks = db.query(ConsumptionStock).all()
        markets = db.query(ConsumptionMarket).all()
        fx = db.query(ConsumptionFx).all()
        commodities = db.query(ConsumptionCommodity).all()
        cryptos = db.query(ConsumptionCrypto).all()

        def fmt(row, category):
            return {
                "ticker": row.ticker, "asset": row.asset_name, "category": category,
                "price": row.close_price, "change": row.daily_change,
                "action": row.action, "total_confidence": row.total_confidence,
                "trad_confidence": row.trad_confidence, "swarm_confidence": row.swarm_confidence,
                "est_1d": row.est_1d, "est_7d": row.est_7d, "est_1m": row.est_1m,
                "win_rate": row.win_rate, "rec_score": row.rec_score,
                "candlestick_pattern": row.candlestick_pattern, "logic": row.logic,
                "sparkline": row.sparkline,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            }

        return (
            [fmt(s, "stock") for s in stocks] +
            [fmt(m, "market") for m in markets] +
            [fmt(f, "fx") for f in fx] +
            [fmt(c, "commodity") for c in commodities] +
            [fmt(c, "crypto") for c in cryptos]
        )
    except Exception as e:
        logger.error(f"Signals API Error: {e}")
        return []


@router.get("/commodities/all")
def get_all_commodities(db: Session = Depends(get_db)):
    """Get all commodity data from consumption layer."""
    try:
        commodities = db.execute(text("SELECT * FROM consumption.commodity ORDER BY total_confidence DESC")).fetchall()
        return [{
            "ticker": c.ticker, "asset": c.asset_name, "price": c.close_price,
            "change": c.daily_change, "action": c.action,
            "total_confidence": c.total_confidence, "trad_confidence": c.trad_confidence,
            "swarm_confidence": c.swarm_confidence,
            "est_1d": c.est_1d, "est_7d": c.est_7d, "est_1m": c.est_1m,
            "win_rate": c.win_rate, "rec_score": c.rec_score,
            "candlestick_pattern": c.candlestick_pattern, "logic": c.logic,
            "sparkline": c.sparkline,
            "timestamp": c.timestamp.isoformat() if c.timestamp else None,
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
