#!/usr/bin/env python3
"""
HYPOTHESIS 18: Doji Star Reversal
Small-bodied candle after trend = potential reversal
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
print("HYPOTHESIS 18: Doji Star Reversal")
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector IN ('Tech', 'Equity') LIMIT 30")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT date, ticker, open, high, low, close
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Doji = small body relative to range
trades = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    if len(ticker_df) < 20:
        continue
    
    ticker_df['body'] = abs(ticker_df['close'] - ticker_df['open'])
    ticker_df['range'] = ticker_df['high'] - ticker_df['low']
    ticker_df['doji'] = ticker_df['body'] <= (ticker_df['range'] * 0.1)  # Body < 10% of range
    ticker_df['prev_return'] = ticker_df['close'].pct_change()
    
    for i in range(5, len(ticker_df) - 5):
        # Doji after 3-day trend
        if ticker_df['doji'].iloc[i] and abs(ticker_df['prev_return'].iloc[i-1]) > 0.03:
            entry_price = ticker_df['close'].iloc[i]
            exit_price = ticker_df['close'].iloc[i + 5]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)

print(f"\n📊 RESULTS: Doji Star Reversal")
print(f"  Trades: {len(trades)}")

if len(trades) >= 30:
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    sharpe = returns.mean() / returns.std() * np.sqrt(50) if returns.std() > 0 else -999
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Sharpe: {sharpe:.2f}")
    print(f"  Status: {'✅ VALIDATED' if win_rate >= 55 and sharpe > 0.5 else '❌ REJECTED'}")
else:
    print(f"  ❌ INSUFFICIENT TRADES")

print("="*70)
