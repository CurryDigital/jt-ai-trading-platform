import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import text
import logging
import datetime
import json
import random
from app.db.session import (
    SessionLocal, ConsumptionStock, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto, ConsumptionMarket, GlobalState
)
from app.core_logic.analysis.time_series.prophet_forecast import get_prophet_prediction
from app.core_logic.agents.research_swarm import research_swarm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def to_native(val):
    if val is None: return None
    if isinstance(val, (np.float64, np.float32)): return float(val)
    if isinstance(val, (np.int64, np.int32)): return int(val)
    if pd.isna(val): return None
    return val

def hkt_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

async def refresh_indices_and_mood():
    db = SessionLocal()
    now = hkt_now()
    
    # 1. Update Geopolitical Shock Radar (Paper 5 Implementation)
    news_headlines = "AI model efficiency debate causing US tech firm drop NVDA MSFT Google hardware cycle Peak AI"
    try:
        shock_analysis = await research_swarm.llm.ainvoke(f"Act as a macro analyst. Latest theme: {news_headlines}. Generate a 1-sentence Geopolitical Shock statement. Decided if risk is CRITICAL/CAUTION/NOMINAL.")
        shock_text = shock_analysis.content
        risk_level = "CAUTION"
        if "CRITICAL" in shock_text.upper(): risk_level = "CRITICAL"
        elif "NOMINAL" in shock_text.upper(): risk_level = "NOMINAL"

        db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES ('shock_monitor_text', :v, 'system', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, timestamp = EXCLUDED.timestamp"), {"v": shock_text, "ts": now})
        db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES ('system_risk_level', :v, 'system', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, timestamp = EXCLUDED.timestamp"), {"v": risk_level, "ts": now})
        db.commit()
    except Exception as e:
        logger.error(f"Shock Radar fail: {e}")
        db.rollback()

    # 2. Update Regional Narratives
    indices = { "DJI": "^DJI", "HSI": "^HSI", "STOXX50": "^STOXX50E", "SSE": "000001.SS", "STI": "^STI" }
    avg_7d = 0; valid = 0
    for label, sym in indices.items():
        try:
            stock = yf.Ticker(sym); df = stock.history(period="1mo")
            if df.empty: continue
            p_data = get_prophet_prediction(sym); p_7d = to_native(p_data['P_7d']) if p_data else 0.0
            avg_7d += p_7d; valid += 1
            rat = await research_swarm.llm.ainvoke(f"Analyze {label} Index. 7D forecast {p_7d:+.2f}%. Theme: {news_headlines}. 1-sentence summary.")
            
            # FIXED SQL SYNTAX
            sql = text("""
                INSERT INTO consumption.global_state (key, value, category, rationale, estimates, timestamp) 
                VALUES (:k, :v, 'index', :r, CAST(:est AS JSONB), :ts) 
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, rationale = EXCLUDED.rationale, estimates = EXCLUDED.estimates, timestamp = EXCLUDED.timestamp
            """)
            db.execute(sql, { 
                "k": f"index_rationale_{label}", "v": rat.content, "r": rat.content,
                "est": json.dumps({"1d": f"{p_7d/7:+.1f}%", "1w": f"{p_7d:+.1f}%", "1m": f"{p_7d*4:+.1f}%"}), 
                "ts": now 
            })
            db.commit()
        except Exception as e: 
            logger.error(f"Index {label} fail: {e}")
            db.rollback()
        
    # 3. Update Global Market Mood
    mood = "Neutral"
    if valid > 0:
        avg = avg_7d / valid
        if avg > 1.0: mood = "Bullish"
        elif avg < -1.0: mood = "Bearish"
    
    try:
        db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES ('market_mood_index', :v, 'market', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, timestamp = EXCLUDED.timestamp"), {"v": mood, "ts": now})
        db.commit()
    except Exception as e:
        logger.error(f"Market Mood fail: {e}")
        db.rollback()
    
    # 4. Populate Alpha Recommendations Grid
    try:
        db.execute(text("DELETE FROM consumption.market WHERE true"))
        top_picks = db.execute(text("SELECT ticker, market, final_score FROM consumption.stock ORDER BY final_score DESC LIMIT 4")).fetchall()
        for p in top_picks:
            db.add(ConsumptionMarket(
                timestamp=now, ticker=p.ticker, sector=p.market, name=p.ticker,
                edge_score=str(round(p.final_score * 100, 1)), est_1d="+0.5%", est_1m="+4.2%"
            ))
        db.commit()
    except Exception as e:
        logger.error(f"Alpha Recommendations fail: {e}")
        db.rollback()
        
    db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(refresh_indices_and_mood())
