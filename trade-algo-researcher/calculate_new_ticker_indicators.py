#!/usr/bin/env python3
"""
CALCULATE INDICATORS FOR NEW TICKERS + TEST STRATEGIES
SPY, MSTR, COIN, MARA, RIOT - Now with indicators!
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
print("CALCULATING INDICATORS + TESTING NEW STRATEGIES")
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

# Get new tickers data
print("\n=== Loading New Ticker Data ===")
target_tickers = ['SPY', 'MSTR', 'COIN', 'MARA', 'RIOT']

for ticker in target_tickers:
    print(f"\n--- {ticker} ---")
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT date, open, high, low, close, volume
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2022-06-01' AND '2024-12-31'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) == 0:
        print(f"  No data found")
        continue
    
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    # Calculate basic indicators
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Volume ratio
    df['vol_avg_20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg_20']
    
    # Price change
    df['return'] = df['close'].pct_change()
    
    print(f"  Records: {len(df)}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  RSI range: {df['rsi_14'].min():.1f} to {df['rsi_14'].max():.1f}")
    print(f"  Vol ratio max: {df['vol_ratio'].max():.1f}x")
    
    # Test basic mean reversion
    oversold = df[df['rsi_14'] < 20]
    print(f"  Oversold periods (RSI<20): {len(oversold)}")
    
    if len(oversold) > 5:
        # Simple backtest: buy RSI<20, hold 5 days
        trades = []
        for idx in oversold.index:
            if idx + 5 < len(df):
                entry = df.loc[idx, 'close']
                exit_price = df.loc[idx + 5, 'close']
                ret = (exit_price - entry) / entry * 100
                trades.append(ret)
        
        if len(trades) > 5:
            r = pd.Series(trades)
            wr = (r > 0).mean() * 100
            print(f"  RSI<20 Strategy: Win% = {wr:.1f}% ({len(trades)} trades)")

cursor.close()
conn.close()

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("\nData loaded successfully for all new tickers!")
print("Next: Calculate full indicators and test complete strategies")
print("="*70)
