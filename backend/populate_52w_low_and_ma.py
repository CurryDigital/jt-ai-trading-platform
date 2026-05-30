"""
Populate 52-week low data and moving average columns for consumption.markets_stocks_overview.

This script:
1. Fetches 52-week high/low data from yfinance for each stock
2. Computes distance_to_52w_low_pct
3. Fetches 1 year of historical price data
4. Computes 50-day and 200-day moving averages
5. Determines if price is above each MA
6. Updates the database

Run with:
    cd /home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend
    python populate_52w_low_and_ma.py
"""
import os
import sys
import time
import logging
from datetime import datetime

sys.path.insert(0, '/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend')
os.chdir('/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend')

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "aitrading")
DB_USER = os.getenv("DB_USER", "jtcml")
DB_PASSWORD = os.getenv("DB_PASSWORD", "jtcml_pass_2024")

connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)


def get_tickers_to_update():
    """Get all stocks that need 52w low and MA data."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ticker, market, price, distance_to_52w_high_pct
            FROM consumption.markets_stocks_overview
            WHERE market IN ('US', 'HK', 'CN')
              AND price > 0
            ORDER BY market, ticker
        """)).fetchall()
    return result


def fetch_stock_data(ticker):
    """Fetch 52-week data and historical prices from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get current price and 52-week data
        current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
        fifty_two_week_high = info.get('fiftyTwoWeekHigh')
        fifty_two_week_low = info.get('fiftyTwoWeekLow')
        
        # Get historical data for MAs
        hist = stock.history(period="1y")
        
        return {
            'current_price': current_price,
            'fifty_two_week_high': fifty_two_week_high,
            'fifty_two_week_low': fifty_two_week_low,
            'history': hist
        }
    except Exception as e:
        logger.warning(f"Failed to fetch data for {ticker}: {e}")
        return None


def to_native(val):
    """Convert numpy types to Python native types for SQLAlchemy."""
    if val is None:
        return None
    if hasattr(val, 'item'):  # numpy scalar
        return val.item()
    return val


def compute_metrics(data):
    """Compute distance_to_52w_low_pct, MAs, and above-MA booleans."""
    if not data:
        return None
    
    current_price = data['current_price']
    fifty_two_week_low = data['fifty_two_week_low']
    hist = data['history']
    
    metrics = {}
    
    # Compute distance_to_52w_low_pct
    if current_price and fifty_two_week_low and fifty_two_week_low > 0:
        metrics['distance_to_52w_low_pct'] = ((current_price - fifty_two_week_low) / fifty_two_week_low) * 100
    else:
        metrics['distance_to_52w_low_pct'] = None
    
    # Compute MAs
    if hist is not None and not hist.empty and len(hist) >= 50:
        metrics['ma_50d'] = float(hist['Close'].rolling(window=50).mean().iloc[-1])
        metrics['above_50d_ma'] = bool(current_price > metrics['ma_50d']) if current_price else None
    else:
        metrics['ma_50d'] = None
        metrics['above_50d_ma'] = None
    
    if hist is not None and not hist.empty and len(hist) >= 200:
        metrics['ma_200d'] = float(hist['Close'].rolling(window=200).mean().iloc[-1])
        metrics['above_200d_ma'] = bool(current_price > metrics['ma_200d']) if current_price else None
    else:
        metrics['ma_200d'] = None
        metrics['above_200d_ma'] = None
    
    # Convert all values to native Python types
    return {k: to_native(v) for k, v in metrics.items()}


def update_stock(ticker, metrics):
    """Update a single stock in the database."""
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE consumption.markets_stocks_overview
            SET 
                distance_to_52w_low_pct = :distance_to_52w_low_pct,
                ma_50d = :ma_50d,
                ma_200d = :ma_200d,
                above_50d_ma = :above_50d_ma,
                above_200d_ma = :above_200d_ma,
                updated_at = NOW()
            WHERE ticker = :ticker
        """), {
            'ticker': ticker,
            'distance_to_52w_low_pct': metrics.get('distance_to_52w_low_pct'),
            'ma_50d': metrics.get('ma_50d'),
            'ma_200d': metrics.get('ma_200d'),
            'above_50d_ma': metrics.get('above_50d_ma'),
            'above_200d_ma': metrics.get('above_200d_ma')
        })
        conn.commit()


def main():
    tickers = get_tickers_to_update()
    logger.info(f"Found {len(tickers)} stocks to update")
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for i, row in enumerate(tickers):
        ticker = row.ticker
        market = row.market
        
        # Skip non-stock tickers (commodities, fx, crypto)
        if ticker in ['BZ=F', 'GC=F', 'CL=F', 'SI=F'] or ticker.endswith('=X') or '-USD' in ticker:
            skip_count += 1
            continue
        
        logger.info(f"[{i+1}/{len(tickers)}] Processing {ticker} ({market})...")
        
        data = fetch_stock_data(ticker)
        if not data:
            error_count += 1
            continue
        
        metrics = compute_metrics(data)
        if not metrics:
            error_count += 1
            continue
        
        update_stock(ticker, metrics)
        success_count += 1
        
        # Rate limiting - be nice to yfinance
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {success_count} succeeded, {error_count} failed, {skip_count} skipped")
            time.sleep(1)
        else:
            time.sleep(0.3)
    
    logger.info("=" * 50)
    logger.info(f"Done! Success: {success_count}, Errors: {error_count}, Skipped: {skip_count}")
    logger.info("=" * 50)
    
    # Verify results
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                market,
                COUNT(*) as total,
                COUNT(distance_to_52w_low_pct) as has_low,
                COUNT(ma_50d) as has_ma50,
                COUNT(ma_200d) as has_ma200,
                COUNT(above_50d_ma) as has_above50,
                COUNT(above_200d_ma) as has_above200
            FROM consumption.markets_stocks_overview
            WHERE market IN ('US', 'HK', 'CN')
            GROUP BY market
            ORDER BY market
        """)).fetchall()
        
        logger.info("\nVerification:")
        for r in result:
            logger.info(f"  {r.market}: total={r.total}, has_low={r.has_low}, has_ma50={r.has_ma50}, has_ma200={r.has_ma200}, above50={r.has_above50}, above200={r.has_above200}")


if __name__ == "__main__":
    main()
