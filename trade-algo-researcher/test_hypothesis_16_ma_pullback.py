#!/usr/bin/env python3
"""
HYPOTHESIS 16: Pullback to 20-Day MA
Buy when price pulls back to rising 20-day MA in uptrend
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
print("HYPOTHESIS 16: Pullback to 20-Day MA")
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector = 'Tech' LIMIT 20")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT date, ticker, close, low
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Calculate 20-day MA
def calculate_ma(prices, period):
    return prices.rolling(window=period).mean()

all_data = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    ticker_df['ma_20'] = calculate_ma(ticker_df['close'], 20)
    ticker_df['ma_slope'] = ticker_df['ma_20'].diff()
    all_data.append(ticker_df)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['ma_20'])

print(f"After MA calc: {len(df)} records")

# Test pullback to 20-day MA
trades = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date')
    
    for i in range(25, len(ticker_df) - 10):
        # Conditions:
        # 1. MA is rising (uptrend)
        # 2. Low touches or goes below MA
        # 3. Close is above MA (bounce)
        ma_rising = ticker_df['ma_slope'].iloc[i] > 0
        low_below_ma = ticker_df['low'].iloc[i] <= ticker_df['ma_20'].iloc[i] * 1.01
        close_above_ma = ticker_df['close'].iloc[i] > ticker_df['ma_20'].iloc[i]
        
        if ma_rising and low_below_ma and close_above_ma:
            entry_price = ticker_df['close'].iloc[i]
            exit_price = ticker_df['close'].iloc[i + 5]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)

if len(trades) < 50:
    print(f"\n❌ INSUFFICIENT TRADES: {len(trades)}")
else:
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(50) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    print(f"\n📊 RESULTS:")
    print(f"  Trades:     {len(trades)}")
    print(f"  Win Rate:   {win_rate:.1f}%")
    print(f"  Avg Return: {avg_return:.2f}%")
    print(f"  Sharpe:     {sharpe:.2f}")
    print(f"  Max DD:     {max_dd:.2f}%")
    
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"\n✅ VALIDATED - Pullback strategy works")
    elif sharpe > 0.5:
        print(f"\n🧪 TESTING - Moderate edge")
    else:
        print(f"\n❌ REJECTED - Pullback not predictive")

print("="*70)
