#!/usr/bin/env python3
"""
Historical Data Ingestion Pipeline
Populates bronze and silver schemas with 5-year OHLCV data

Usage:
    python data_ingestion.py --universe sp500_hk --start 2019-01-01 --end 2024-12-31
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import argparse
import logging
from tqdm import tqdm
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Pipeline for ingesting historical price data into bronze/silver schemas."""
    
    def __init__(self, db_host="openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com",
                 db_name="postgres", username=None, password=None):
        self.db_host = db_host
        self.db_name = db_name
        self.username = username
        self.password = password
        self.engine = None
        
    def connect(self):
        """Create database connection."""
        connection_string = f"postgresql://{self.username}:{self.password}@{self.db_host}:5432/{self.db_name}"
        self.engine = create_engine(connection_string)
        logger.info(f"Connected to {self.db_host}")
        return self.engine
    
    def get_universe(self):
        """Define S&P 500 + HK stock universe."""
        # S&P 500 subset (liquid names for backtest)
        sp500 = [
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'BRK-B', 'WMT',
            'JPM', 'V', 'MA', 'UNH', 'HD', 'PG', 'JNJ', 'LLY', 'MRK', 'ABBV',
            'COST', 'KO', 'PEP', 'TMO', 'ABT', 'MCD', 'CSCO', 'ACN', 'WFC', 'DHR',
            'VZ', 'ADBE', 'NKE', 'TXN', 'PM', 'CRM', 'BMY', 'NEE', 'RTX', 'HON',
            # Tech/AI focus for ARASO
            'ADSK', 'INTU', 'NOW', 'TEAM', 'SNOW', 'ZM', 'CRWD', 'DDOG', 'MDB', 'PLTR',
            'AMD', 'INTC', 'QCOM', 'AVGO', 'MU', 'LRCX', 'KLAC', 'AMAT', 'SNPS', 'CDNS',
            # GPU supply chain
            'VRT', 'FN', 'STX', 'WDC', 'NTAP', 'PSTG', 'SNOW',
        ]
        
        # HK stocks (Yahoo Finance tickers with .HK suffix)
        hk_stocks = [
            '0001.HK',  # CK Hutchison
            '0700.HK',  # Tencent
            '9988.HK',  # Alibaba
            '3690.HK',  # Meituan
            '2318.HK',  # Ping An
            '1299.HK',  # AIA
            '0883.HK',  # CNOOC
            '0941.HK',  # China Mobile
            '1398.HK',  # ICBC
            '0388.HK',  # HKEX
        ]
        
        return list(set(sp500 + hk_stocks))  # Remove duplicates
    
    def fetch_yfinance_data(self, ticker, start_date, end_date):
        """Fetch OHLCV data from Yahoo Finance."""
        try:
            # Add .SR for HK stocks if not present (some sources use different format)
            yf_ticker = ticker
            
            logger.info(f"Fetching {yf_ticker}...")
            stock = yf.Ticker(yf_ticker)
            
            # Get historical data
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"No data for {ticker}")
                return None
            
            # Standardize columns
            df = df.reset_index()
            df['ticker'] = ticker
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            
            # Rename columns to match schema
            column_map = {
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'ticker': 'ticker'
            }
            df = df.rename(columns=column_map)
            
            # Select only needed columns
            df = df[['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"  → {len(df)} rows fetched")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return None
    
    def insert_bronze(self, df):
        """Insert raw data into bronze schema."""
        if df is None or df.empty:
            return 0
        
        try:
            df.to_sql('raw_stock_data', self.engine, schema='bronze', 
                     if_exists='append', index=False, method='multi')
            return len(df)
        except Exception as e:
            logger.error(f"Error inserting to bronze: {e}")
            return 0
    
    def transform_to_silver(self, ticker, start_date, end_date):
        """Transform bronze data to silver (add returns, clean)."""
        query = """
        SELECT date, ticker, open, high, low, close, volume
        FROM bronze.raw_stock_data
        WHERE ticker = :ticker
        AND date BETWEEN :start AND :end
        ORDER BY date
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, 
                           params={'ticker': ticker, 'start': start_date, 'end': end_date})
        
        if df.empty:
            return None
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        return df
    
    def insert_silver(self, df):
        """Insert cleaned data into silver schema."""
        if df is None or df.empty:
            return 0
        
        try:
            df.to_sql('historical_stock_data', self.engine, schema='silver',
                     if_exists='append', index=False, method='multi')
            return len(df)
        except Exception as e:
            logger.error(f"Error inserting to silver: {e}")
            return 0
    
    def run_ingestion(self, start_date, end_date, tickers=None):
        """Run full ingestion pipeline."""
        if tickers is None:
            tickers = self.get_universe()
        
        logger.info(f"Starting ingestion for {len(tickers)} tickers")
        logger.info(f"Period: {start_date} to {end_date}")
        
        stats = {'bronze': 0, 'silver': 0, 'failed': []}
        
        for ticker in tqdm(tickers, desc="Fetching data"):
            # Fetch from yfinance
            df = self.fetch_yfinance_data(ticker, start_date, end_date)
            
            if df is None:
                stats['failed'].append(ticker)
                continue
            
            # Insert to bronze
            rows = self.insert_bronze(df)
            stats['bronze'] += rows
            
            # Transform and insert to silver
            silver_df = self.transform_to_silver(ticker, start_date, end_date)
            if silver_df is not None:
                rows = self.insert_silver(silver_df)
                stats['silver'] += rows
            
            # Rate limiting
            time.sleep(0.5)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info(f"  Bronze rows: {stats['bronze']:,}")
        logger.info(f"  Silver rows: {stats['silver']:,}")
        logger.info(f"  Failed tickers: {len(stats['failed'])}")
        if stats['failed']:
            logger.info(f"    {', '.join(stats['failed'][:10])}")
        
        return stats


def main():
    parser = argparse.ArgumentParser(description='Historical Data Ingestion')
    parser.add_argument('--start', type=str, default='2019-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--username', type=str, required=True,
                       help='Database username')
    parser.add_argument('--password', type=str, required=True,
                       help='Database password')
    parser.add_argument('--tickers', type=str, nargs='+',
                       help='Specific tickers (optional)')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DataIngestionPipeline(
        username=args.username,
        password=args.password
    )
    pipeline.connect()
    
    # Run ingestion
    stats = pipeline.run_ingestion(
        start_date=args.start,
        end_date=args.end,
        tickers=args.tickers
    )
    
    print("\n✅ Data ingestion complete!")
    print(f"Ready for ARASO backtest with {stats['silver']:,} rows in silver schema")


if __name__ == '__main__':
    main()
