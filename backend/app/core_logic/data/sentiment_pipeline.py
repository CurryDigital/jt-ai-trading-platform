import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import text
import logging
import datetime
import json

# Internal Imports
from app.db.session import (
    SessionLocal, engine, 
    RawNews, HistoricalNews, SentimentMart, KeyEntitiesConfig
)
from app.core_logic.tools.search import search_tool
from app.core_logic.agents.research_swarm import research_swarm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_sentiment_pipeline():
    db = SessionLocal()
    
    # 1. Fetch Configured Entities (Trump, Xi, Elon, Markets)
    entities = db.query(KeyEntitiesConfig).filter(KeyEntitiesConfig.is_active == True).all()
    
    # 2. Purge Bronze News
    db.execute(text("TRUNCATE TABLE bronze.raw_news"))
    db.commit()

    today = datetime.datetime.utcnow().date()

    for ent in entities:
        logger.info(f"Analyzing Sentiment for: {ent.name} ({ent.category})")
        
        try:
            # A. Fetch News via Serper
            query = f"{ent.name} market news impact outlook"
            news_data = search_tool.search_market_news(query)
            
            # B. Ingest to Bronze
            db.add(RawNews(
                date=datetime.datetime.utcnow(),
                category=ent.category,
                entity_name=ent.name,
                headline=f"Top news for {ent.name}",
                raw_content=news_data
            ))
            
            # C. Swarm Logic (Multi-Agent Consensus)
            swarm_debate = research_swarm.llm.invoke(f"""
                Analyze the latest context for {ent.name}:
                Data: {news_data}
                
                Task:
                1. Provide a sentiment score from -1.0 (Very Bearish) to 1.0 (Very Bullish).
                2. List 3 Bullish points.
                3. List 3 Bearish points.
                4. Provide a 1-sentence macro impact summary.
                
                Return JSON format.
            """).content
            
            try:
                res = json.loads(swarm_debate)
                # D. Store in Gold Mart
                db.add(SentimentMart(
                    date=datetime.datetime.utcnow(),
                    perspective=ent.category,
                    entity_name=ent.name,
                    sentiment_score=float(res.get('sentiment_score', 0)),
                    bullish_reasons=res.get('bullish_points', []),
                    bearish_reasons=res.get('bearish_points', []),
                    swarm_summary=res.get('macro_impact', '')
                ))
            except:
                logger.warning(f"Swarm debate parse failed for {ent.name}")

            # E. Archive in Silver
            db.execute(text("""
                INSERT INTO silver.historical_news (date, category, entity_name, headline)
                VALUES (:date, :cat, :name, :head)
                ON CONFLICT DO NOTHING
            """), {'date': datetime.datetime.utcnow(), 'cat': ent.category, 'name': ent.name, 'head': f"Consensus summary: {ent.name}"})
            
            db.commit()
            logger.info(f"Sentiment Mart updated for {ent.name}")

        except Exception as e:
            logger.error(f"Failed sentiment pipeline for {ent.name}: {e}")
            db.rollback()
            
    db.close()

if __name__ == "__main__":
    run_sentiment_pipeline()
