#!/usr/bin/env python3
"""
Quick RSI Enhancement Test
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

# Get data
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

# Get tickers
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector = 'Tech' LIMIT 20")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

print(f"Testing RSI enhancements on {len(tickers)} Tech tickers")

# Get data
ticker_list = "','".join(tickers)
price_query = f"""
SELECT date, ticker, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
prices = pd.read_sql(price_query, conn)

rsi_query = f"""
SELECT date, ticker, rsi_14
FROM gold.stock_metrics
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
rsi = pd.read_sql(rsi_query, conn)
conn.close()

df = prices.merge(rsi, on=['date', 'ticker'], how='inner')
print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Test different configurations
configs = [
    (25, 'time'),
    (25, 'profit'),
    (20, 'time'),
    (20, 'profit'),
    (15, 'profit'),
]

print("\n" + "="*70)
print("RSI ENHANCEMENT RESULTS")
print("="*70)
print(f"{'RSI':<8} {'Exit':<12} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

for rsi_thresh, exit_type in configs:
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 50:
            continue
        
        for i in range(25, len(ticker_df) - 15):
            rsi = ticker_df['rsi_14'].iloc[i]
            
            if pd.isna(rsi) or rsi >= rsi_thresh:
                continue
            
            entry_price = ticker_df['close'].iloc[i]
            
            if exit_type == 'time':
                exit_price = ticker_df['close'].iloc[i + 10]
            else:  # profit target
                target = entry_price * 1.04
                exit_price = None
                for j in range(i+1, min(i+15, len(ticker_df))):
                    if ticker_df['close'].iloc[j] >= target:
                        exit_price = target
                        break
                if exit_price is None:
                    exit_price = ticker_df['close'].iloc[min(i+10, len(ticker_df)-1)]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)
    
    if len(trades) < 30:
        print(f"{rsi_thresh:<8} {exit_type:<12} INSUFFICIENT TRADES ({len(trades)})")
        continue
    
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    status = "✅" if win_rate >= 70 else "🧪" if win_rate >= 60 else "❌"
    print(f"{status} {rsi_thresh:<6} {exit_type:<12} {len(trades):<10} {win_rate:<10.1f} {sharpe:<10.2f}")

print("="*70)
