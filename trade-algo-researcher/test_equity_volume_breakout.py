#!/usr/bin/env python3
"""
TEST: Volume Breakout on Equity Universe (149 tickers)
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
print("TEST: Volume Breakout on EQUITY Universe")
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

# Get Equity tickers
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector = 'Equity' LIMIT 50")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

print(f"Testing {len(tickers)} Equity tickers")

ticker_list = "','".join(tickers)
query = f"""
SELECT date, ticker, close, volume, high
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Test Volume Breakout config
vol_mult = 2.0
price_thresh = 0.04

trades = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    if len(ticker_df) < 50:
        continue
    
    ticker_df['vol_avg'] = ticker_df['volume'].rolling(20).mean()
    ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
    ticker_df['price_change'] = ticker_df['close'].pct_change()
    
    for i in range(20, len(ticker_df) - 10):
        if (ticker_df['vol_ratio'].iloc[i] > vol_mult and 
            ticker_df['price_change'].iloc[i] > price_thresh):
            
            entry_price = ticker_df['close'].iloc[i]
            target_price = entry_price * 1.05
            
            exit_price = None
            for j in range(i+1, min(i+11, len(ticker_df))):
                if ticker_df['high'].iloc[j] >= target_price:
                    exit_price = target_price
                    break
            if exit_price is None:
                exit_price = ticker_df['close'].iloc[min(i+10, len(ticker_df)-1)]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)

print(f"\n📊 RESULTS: Volume Breakout on EQUITY")
print(f"  Tickers: {df['ticker'].nunique()}")
print(f"  Trades: {len(trades)}")

if len(trades) >= 30:
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg Return: {avg_return:.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")
    
    if win_rate >= 65:
        print(f"\n✅ VALIDATED on Equity - Can include in universe")
    elif win_rate >= 55:
        print(f"\n🧪 MODERATE on Equity - Test more before including")
    else:
        print(f"\n❌ FAILED on Equity - Do not include in universe")
        print(f"  Equity sector may not respond to momentum signals")

print("="*70)
