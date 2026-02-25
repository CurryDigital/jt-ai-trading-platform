#!/usr/bin/env python3
"""
CALCULATE AND STORE Technical Indicators
Option 2: Calculate from existing price data and store in gold schema
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print("="*70)
print("CALCULATE & STORE: Technical Indicators")
print("Creating gold.technical_indicators_calculated table")
print("="*70)

session = boto3.Session(region_name='ap-southeast-1')
rds = session.client('rds')
token = rds.generate_db_auth_token(
    DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
    Port=5432, DBUsername='openclaw_user', Region='ap-southeast-1'
)
conn = psycopg2.connect(
    host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
    port=5432, database='aitrading', user='openclaw_user',
    password=token, sslmode='require'
)
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS gold.technical_indicators_calculated (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20),
    date DATE,
    rsi_14 DECIMAL(10,4),
    stoch_k DECIMAL(10,4),
    stoch_d DECIMAL(10,4),
    macd_line DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    macd_histogram DECIMAL(10,4),
    adx DECIMAL(10,4),
    adx_plus_di DECIMAL(10,4),
    adx_minus_di DECIMAL(10,4),
    vwap DECIMAL(10,4),
    vol_sma_20 DECIMAL(15,2),
    vol_ratio DECIMAL(10,4),
    bb_upper DECIMAL(10,4),
    bb_middle DECIMAL(10,4),
    bb_lower DECIMAL(10,4),
    atr_14 DECIMAL(10,4),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);
''')
conn.commit()

print("✅ Table created: gold.technical_indicators_calculated")
print()

# Get tickers to process
cursor.execute('''
SELECT DISTINCT ticker FROM silver.historical_stock_data 
WHERE date >= '2022-01-01'
ORDER BY ticker
''')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

print(f"Processing {len(tickers)} tickers...")
print()

batch_size = 50
processed = 0

for batch_start in range(0, len(tickers), batch_size):
    batch = tickers[batch_start:batch_start + batch_size]
    ticker_list = "','".join(batch)
    
    query = f"""
    SELECT date, ticker, open, high, low, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date >= '2022-01-01'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    
    # Calculate indicators for each ticker
    all_data = []
    for ticker in df['ticker'].unique():
        tdf = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(tdf) < 50:
            continue
        
        # RSI 14
        delta = tdf['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        tdf['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Stochastic (14, 3)
        lowest_low = tdf['low'].rolling(14).min()
        highest_high = tdf['high'].rolling(14).max()
        tdf['stoch_k'] = 100 * (tdf['close'] - lowest_low) / (highest_high - lowest_low)
        tdf['stoch_d'] = tdf['stoch_k'].rolling(3).mean()
        
        # MACD (12, 26, 9)
        ema_12 = tdf['close'].ewm(span=12, adjust=False).mean()
        ema_26 = tdf['close'].ewm(span=26, adjust=False).mean()
        tdf['macd_line'] = ema_12 - ema_26
        tdf['macd_signal'] = tdf['macd_line'].ewm(span=9, adjust=False).mean()
        tdf['macd_histogram'] = tdf['macd_line'] - tdf['macd_signal']
        
        # ADX (14)
        tr1 = tdf['high'] - tdf['low']
        tr2 = abs(tdf['high'] - tdf['close'].shift(1))
        tr3 = abs(tdf['low'] - tdf['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        plus_dm = tdf['high'].diff()
        minus_dm = -tdf['low'].diff()
        plus_dm = plus_dm.where(plus_dm > 0, 0)
        minus_dm = minus_dm.where(minus_dm > 0, 0)
        
        atr = tr.rolling(14).mean()
        plus_di = 100 * plus_dm.rolling(14).mean() / atr
        minus_di = 100 * minus_dm.rolling(14).mean() / atr
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        tdf['adx'] = dx.rolling(14).mean()
        tdf['adx_plus_di'] = plus_di
        tdf['adx_minus_di'] = minus_di
        
        # VWAP
        typical = (tdf['high'] + tdf['low'] + tdf['close']) / 3
        tdf['vwap'] = (typical * tdf['volume']).cumsum() / tdf['volume'].cumsum()
        
        # Volume
        tdf['vol_sma_20'] = tdf['volume'].rolling(20).mean()
        tdf['vol_ratio'] = tdf['volume'] / tdf['vol_sma_20']
        
        # Bollinger Bands
        tdf['bb_middle'] = tdf['close'].rolling(20).mean()
        bb_std = tdf['close'].rolling(20).std()
        tdf['bb_upper'] = tdf['bb_middle'] + 2 * bb_std
        tdf['bb_lower'] = tdf['bb_middle'] - 2 * bb_std
        
        # ATR 14
        tdf['atr_14'] = atr
        
        all_data.append(tdf)
    
    if all_data:
        df_calc = pd.concat(all_data, ignore_index=True)
        df_calc = df_calc.dropna()
        
        # Insert into database
        cursor = conn.cursor()
        for _, row in df_calc.iterrows():
            cursor.execute('''
            INSERT INTO gold.technical_indicators_calculated 
            (ticker, date, rsi_14, stoch_k, stoch_d, macd_line, macd_signal, macd_histogram,
             adx, adx_plus_di, adx_minus_di, vwap, vol_sma_20, vol_ratio, 
             bb_upper, bb_middle, bb_lower, atr_14)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
            rsi_14 = EXCLUDED.rsi_14,
            stoch_k = EXCLUDED.stoch_k,
            stoch_d = EXCLUDED.stoch_d,
            macd_line = EXCLUDED.macd_line,
            macd_signal = EXCLUDED.macd_signal,
            macd_histogram = EXCLUDED.macd_histogram,
            adx = EXCLUDED.adx,
            adx_plus_di = EXCLUDED.adx_plus_di,
            adx_minus_di = EXCLUDED.adx_minus_di,
            vwap = EXCLUDED.vwap,
            vol_sma_20 = EXCLUDED.vol_sma_20,
            vol_ratio = EXCLUDED.vol_ratio,
            bb_upper = EXCLUDED.bb_upper,
            bb_middle = EXCLUDED.bb_middle,
            bb_lower = EXCLUDED.bb_lower,
            atr_14 = EXCLUDED.atr_14,
            calculated_at = CURRENT_TIMESTAMP
            ''', (
                row['ticker'], row['date'], row['rsi_14'], row['stoch_k'], row['stoch_d'],
                row['macd_line'], row['macd_signal'], row['macd_histogram'],
                row['adx'], row['adx_plus_di'], row['adx_minus_di'], row['vwap'],
                row['vol_sma_20'], row['vol_ratio'], row['bb_upper'], row['bb_middle'],
                row['bb_lower'], row['atr_14']
            ))
        
        conn.commit()
        cursor.close()
        processed += len(df_calc)
        print(f"Batch {batch_start//batch_size + 1}: {len(df_calc)} records inserted")

print()
print("="*70)
print(f"✅ COMPLETE: {processed} records inserted")
print("="*70)
print()
print("Table: gold.technical_indicators_calculated")
print("Ready for hypothesis testing!")

conn.close()
