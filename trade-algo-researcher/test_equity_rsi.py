#!/usr/bin/env python3
"""
TEST: RSI Mean Reversion on Equity Universe
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
print("TEST: RSI Mean Reversion on EQUITY Universe")
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
SELECT date, ticker, close
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

all_data = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    ticker_df['rsi_14'] = calculate_rsi(ticker_df['close'])
    all_data.append(ticker_df)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi_14'])

print(f"After RSI calc: {len(df)} records")

# Test different RSI thresholds
print("\n📊 RESULTS: RSI Mean Reversion on EQUITY")
print(f"{'RSI':<8} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*50)

for rsi_thresh in [30, 25, 20, 15, 10]:
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        
        for i in range(25, len(ticker_df) - 15):
            rsi_val = ticker_df['rsi_14'].iloc[i]
            
            if pd.isna(rsi_val) or rsi_val >= rsi_thresh:
                continue
            
            entry_price = ticker_df['close'].iloc[i]
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
    
    if len(trades) < 20:
        print(f"{rsi_thresh:<8} {len(trades):<10} INSUFFICIENT")
        continue
    
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    status = "✅" if win_rate >= 65 else "🧪" if win_rate >= 55 else "❌"
    print(f"{status} {rsi_thresh:<6} {len(trades):<10} {win_rate:<10.1f} {sharpe:<10.2f}")

print("="*70)
