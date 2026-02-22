#!/usr/bin/env python3
"""
Indices Enrichment - Comprehensive market index data
Enriches daily data for major global indices with extended metrics
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from app.db.session import get_connection
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Major global indices with metadata
INDICES = {
    # US Markets
    '^GSPC': {'name': 'S\&P 500', 'market': 'US', 'region': 'North America', 'currency': 'USD', 'timezone': 'America/New_York'},
    '^DJI': {'name': 'Dow Jones Industrial Average', 'market': 'US', 'region': 'North America', 'currency': 'USD', 'timezone': 'America/New_York'},
    '^IXIC': {'name': 'Nasdaq Composite', 'market': 'US', 'region': 'North America', 'currency': 'USD', 'timezone': 'America/New_York'},
    '^RUT': {'name': 'Russell 2000', 'market': 'US', 'region': 'North America', 'currency': 'USD', 'timezone': 'America/New_York'},
    '^VIX': {'name': 'CBOE Volatility Index', 'market': 'US', 'region': 'North America', 'currency': 'USD', 'timezone': 'America/New_York', 'is_volatility': True},
    
    # Asian Markets
    '^HSI': {'name': 'Hang Seng Index', 'market': 'HK', 'region': 'Asia', 'currency': 'HKD', 'timezone': 'Asia/Hong_Kong'},
    '^N225': {'name': 'Nikkei 225', 'market': 'JP', 'region': 'Asia', 'currency': 'JPY', 'timezone': 'Asia/Tokyo'},
    '000001.SS': {'name': 'Shanghai Composite', 'market': 'CN', 'region': 'Asia', 'currency': 'CNY', 'timezone': 'Asia/Shanghai'},
    '^STI': {'name': 'Straits Times Index', 'market': 'SG', 'region': 'Asia', 'currency': 'SGD', 'timezone': 'Asia/Singapore'},
    '^AXJO': {'name': 'ASX 200', 'market': 'AU', 'region': 'Asia', 'currency': 'AUD', 'timezone': 'Australia/Sydney'},
    
    # European Markets
    '^FTSE': {'name': 'FTSE 100', 'market': 'UK', 'region': 'Europe', 'currency': 'GBP', 'timezone': 'Europe/London'},
    '^GDAXI': {'name': 'DAX', 'market': 'DE', 'region': 'Europe', 'currency': 'EUR', 'timezone': 'Europe/Berlin'},
    '^FCHI': {'name': 'CAC 40', 'market': 'FR', 'region': 'Europe', 'currency': 'EUR', 'timezone': 'Europe/Paris'},
    '^N100': {'name': 'Euronext 100', 'market': 'EU', 'region': 'Europe', 'currency': 'EUR', 'timezone': 'Europe/Paris'},
    
    # Other Global
    '^NSEI': {'name': 'Nifty 50', 'market': 'IN', 'region': 'Asia', 'currency': 'INR', 'timezone': 'Asia/Kolkata'},
}

def ensure_indices_table():
    """Create indices table if not exists"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS silver.market_indices (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            name VARCHAR(100),
            market VARCHAR(10),
            region VARCHAR(50),
            currency VARCHAR(5),
            date DATE NOT NULL,
            open DECIMAL(15, 4),
            high DECIMAL(15, 4),
            low DECIMAL(15, 4),
            close DECIMAL(15, 4),
            volume BIGINT,
            change_pct DECIMAL(8, 4),
            change_amount DECIMAL(15, 4),
            ytd_change DECIMAL(8, 4),
            _52_week_high DECIMAL(15, 4),
            _52_week_low DECIMAL(15, 4),
            _52_week_range_pct DECIMAL(8, 4),
            ma_50 DECIMAL(15, 4),
            ma_200 DECIMAL(15, 4),
            above_ma_50 BOOLEAN,
            above_ma_200 BOOLEAN,
            rsi_14 DECIMAL(5, 2),
            is_volatility_index BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(ticker, date)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_market_indices_ticker_date 
        ON silver.market_indices(ticker, date DESC)
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Indices table ensured")

def to_float(val):
    """Convert numpy/pandas types to Python float"""
    if val is None or pd.isna(val):
        return None
    return float(val)

def to_int(val):
    """Convert numpy/pandas types to Python int"""
    if val is None or pd.isna(val):
        return 0
    return int(val)

def fetch_index_data(ticker, metadata):
    """Fetch comprehensive data for a single index"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get 1 year of data for calculations
        df = stock.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 2:
            logger.warning(f"No data for {ticker}")
            return None
        
        # Get latest data
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Calculate basic metrics
        close = to_float(latest['Close'])
        prev_close = to_float(prev['Close'])
        change_amount = close - prev_close if close and prev_close else 0
        change_pct = (change_amount / prev_close * 100) if prev_close else 0
        
        # Calculate YTD change (first trading day of year vs latest)
        try:
            current_year = datetime.now().year
            ytd_start = to_float(df[df.index >= f"{current_year}-01-01"].iloc[0]['Close'])
            ytd_change = ((close - ytd_start) / ytd_start * 100) if ytd_start and close else None
        except:
            ytd_change = None
        
        # 52-week high/low
        _52_week_high = to_float(df['High'].max())
        _52_week_low = to_float(df['Low'].min())
        _52_week_range_pct = ((_52_week_high - _52_week_low) / _52_week_low * 100) if _52_week_high and _52_week_low else 0
        
        # Moving averages
        ma_50 = to_float(df['Close'].rolling(window=50).mean().iloc[-1]) if len(df) >= 50 else None
        ma_200 = to_float(df['Close'].rolling(window=200).mean().iloc[-1]) if len(df) >= 200 else None
        
        above_ma_50 = close > ma_50 if close and ma_50 else None
        above_ma_200 = close > ma_200 if close and ma_200 else None
        
        # RSI calculation
        rsi_14 = None
        try:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_14 = to_float(100 - (100 / (1 + rs)).iloc[-1])
        except:
            pass
        
        result = {
            'ticker': ticker,
            'name': metadata['name'],
            'market': metadata['market'],
            'region': metadata['region'],
            'currency': metadata['currency'],
            'date': latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else str(latest.name)[:10],
            'open': to_float(latest['Open']),
            'high': to_float(latest['High']),
            'low': to_float(latest['Low']),
            'close': close,
            'volume': to_int(latest['Volume']),
            'change_pct': change_pct,
            'change_amount': change_amount,
            'ytd_change': ytd_change,
            '_52_week_high': _52_week_high,
            '_52_week_low': _52_week_low,
            '_52_week_range_pct': _52_week_range_pct,
            'ma_50': ma_50,
            'ma_200': ma_200,
            'above_ma_50': above_ma_50,
            'above_ma_200': above_ma_200,
            'rsi_14': rsi_14,
            'is_volatility_index': metadata.get('is_volatility', False)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None

def store_index_data(data_list):
    """Store index data in database"""
    if not data_list:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    inserted = 0
    
    for data in data_list:
        if not data:
            continue
            
        try:
            cursor.execute("""
                INSERT INTO silver.market_indices (
                    ticker, name, market, region, currency, date,
                    open, high, low, close, volume,
                    change_pct, change_amount, ytd_change,
                    _52_week_high, _52_week_low, _52_week_range_pct,
                    ma_50, ma_200, above_ma_50, above_ma_200,
                    rsi_14, is_volatility_index, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, NOW()
                )
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    change_pct = EXCLUDED.change_pct,
                    change_amount = EXCLUDED.change_amount,
                    ytd_change = EXCLUDED.ytd_change,
                    _52_week_high = EXCLUDED._52_week_high,
                    _52_week_low = EXCLUDED._52_week_low,
                    _52_week_range_pct = EXCLUDED._52_week_range_pct,
                    ma_50 = EXCLUDED.ma_50,
                    ma_200 = EXCLUDED.ma_200,
                    above_ma_50 = EXCLUDED.above_ma_50,
                    above_ma_200 = EXCLUDED.above_ma_200,
                    rsi_14 = EXCLUDED.rsi_14,
                    updated_at = NOW()
            """, (
                data['ticker'], data['name'], data['market'], data['region'], data['currency'], data['date'],
                data['open'], data['high'], data['low'], data['close'], data['volume'],
                data['change_pct'], data['change_amount'], data['ytd_change'],
                data['_52_week_high'], data['_52_week_low'], data['_52_week_range_pct'],
                data['ma_50'], data['ma_200'], data['above_ma_50'], data['above_ma_200'],
                data['rsi_14'], data['is_volatility_index']
            ))
            inserted += 1
            
        except Exception as e:
            logger.error(f"Error storing {data['ticker']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return inserted

def create_market_summary_view():
    """Create/update consumption view for market summary"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create view for latest index data
        cursor.execute("""
            CREATE OR REPLACE VIEW consumption.Markets_Indices_Overview AS
            SELECT 
                ticker,
                name,
                market,
                region,
                currency,
                date,
                close as price,
                change_pct,
                change_amount,
                ytd_change,
                _52_week_high,
                _52_week_low,
                _52_week_range_pct,
                ma_50,
                ma_200,
                above_ma_50,
                above_ma_200,
                rsi_14,
                is_volatility_index,
                CASE 
                    WHEN change_pct > 0 THEN 'positive'
                    WHEN change_pct < 0 THEN 'negative'
                    ELSE 'neutral'
                END as trend_direction
            FROM silver.market_indices
            WHERE date = (SELECT MAX(date) FROM silver.market_indices)
            ORDER BY region, market, ticker
        """)
        
        conn.commit()
        logger.info("Market summary view created")
        
    except Exception as e:
        logger.warning(f"Could not create view: {e}")
    
    cursor.close()
    conn.close()

def run_indices_enrichment():
    """Main function to enrich index data"""
    logger.info("="*60)
    logger.info("INDICES ENRICHMENT - Starting")
    logger.info("="*60)
    
    # Ensure table exists
    ensure_indices_table()
    
    # Fetch data for all indices
    results = []
    
    logger.info(f"Fetching data for {len(INDICES)} indices...")
    
    for ticker, metadata in INDICES.items():
        logger.info(f"  Fetching {ticker} ({metadata['name']})...")
        result = fetch_index_data(ticker, metadata)
        if result:
            results.append(result)
            logger.info(f"    ✓ {ticker}: {result['close']:.2f} ({result['change_pct']:+.2f}%)")
        else:
            logger.warning(f"    ✗ {ticker}: Failed")
    
    logger.info(f"\nSuccessfully fetched {len(results)}/{len(INDICES)} indices")
    
    # Store data
    logger.info("\nStoring data in database...")
    inserted = store_index_data(results)
    logger.info(f"  Stored {inserted} records")
    
    # Create/update view
    create_market_summary_view()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("INDICES ENRICHMENT - Complete")
    logger.info("="*60)
    
    # Group by region
    by_region = {}
    for r in results:
        region = r['region']
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(r)
    
    logger.info("\nBy Region:")
    for region, indices in sorted(by_region.items()):
        logger.info(f"  {region}: {len(indices)} indices")
    
    return {
        'total': len(INDICES),
        'successful': len(results),
        'failed': len(INDICES) - len(results),
        'stored': inserted
    }

if __name__ == "__main__":
    summary = run_indices_enrichment()
    
    if summary['successful'] < summary['total'] * 0.5:
        logger.error(f"Success rate below 50% ({summary['successful']}/{summary['total']})")
        sys.exit(1)
    
    sys.exit(0)
