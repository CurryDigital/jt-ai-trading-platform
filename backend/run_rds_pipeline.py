import logging
import asyncio
from app.core_logic.data.ingest_to_rds import ingest_stock_data
from app.core_logic.models.orchestrator import ModelOrchestrator
from app.db.session import SessionLocal, Signal as DBSignal
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def main():
    universe = [
        "0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK", 
        "NVDA", "AAPL", "BTC-USD", "GC=F"
    ]
    
    # 1. Ingest Raw Data into RDS
    logging.info("Starting Data Ingestion...")
    ingest_stock_data(universe)

    # 2. Run Analysis Orchestrator
    logging.info("Running Orchestrator Pipeline...")
    orchestrator = ModelOrchestrator()
    signals_df = orchestrator.run_full_pipeline(universe)
    
    # 3. Store Signals in RDS
    logging.info("Storing Signals in RDS...")
    db = SessionLocal()
    try:
        for _, row in signals_df.iterrows():
            sig = DBSignal(
                project_id=1,
                ticker=row['ticker'],
                ts_score=row['ts_signal'],
                sent_score=row['sent_signal'],
                alpha_score=row['alpha_signal'],
                final_score=row['final_score']
            )
            db.add(sig)
        db.commit()
        logging.info("Pipeline complete. RDS updated.")
    except Exception as e:
        logging.error(f"Failed to store signals: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
