import yfinance as yf
import pandas as pd
from app.db.session import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_stock_data(tickers, period="1y"):
    for ticker in tickers:
        logger.info(f"Ingesting {ticker} into RDS...")
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty: continue
            
            # Prepare data for PostgreSQL
            df = df.reset_index()
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df['ticker'] = ticker
            
            # Insert using SQLAlchemy core for speed
            with engine.connect() as conn:
                for _, row in df.iterrows():
                    query = text("""
                        INSERT INTO aitrading_schema.raw_stock_data 
                        (ticker, date, open, high, low, close, volume)
                        VALUES (:ticker, :date, :open, :high, :low, :close, :volume)
                        ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                    """)
                    conn.execute(query, {
                        'ticker': row['ticker'],
                        'date': row['date'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': int(row['volume'])
                    })
                conn.commit()
            logger.info(f"Successfully ingested {len(df)} rows for {ticker}")
        except Exception as e:
            logger.error(f"Failed to ingest {ticker}: {e}")

if __name__ == "__main__":
    universe = [
        "0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK", 
        "AAPL", "NVDA", "TSLA", "BTC-USD", "GC=F"
    ]
    ingest_stock_data(universe)
