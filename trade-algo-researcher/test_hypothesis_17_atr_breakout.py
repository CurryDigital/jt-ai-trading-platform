#!/usr/bin/env python3
"""
HYPOTHESIS 17: Volatility Breakout (ATR Expansion)
Enter when volatility expands (ATR breaks above range)
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
print("HYPOTHESIS 17: Volatility Breakout (ATR Expansion)")
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
SELECT date, ticker, close, high, low
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Calculate ATR (Average True Range)
def calculate_atr(df, period=14):
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['prev_close'])
    df['tr3'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['true_range'].rolling(window=period).mean()
    return df

all_data = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    ticker_df = calculate_atr(ticker_df)
    ticker_df['atr_avg'] = ticker_df['atr'].rolling(20).mean()
    ticker_df['atr_ratio'] = ticker_df['atr'] / ticker_df['atr_avg']
    all_data.append(ticker_df)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['atr_ratio'])

print(f"After ATR calc: {len(df)} records")

# Test ATR expansion breakout
trades = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date')
    
    for i in range(50, len(ticker_df) - 10):
        # Signal: ATR expands significantly (> 1.5x average) + price up
        atr_expansion = ticker_df['atr_ratio'].iloc[i] > 1.5
        price_up = ticker_df['close'].iloc[i] > ticker_df['close'].iloc[i-1] * 1.02
        
        if atr_expansion and price_up:
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
        print(f"\n✅ VALIDATED - ATR expansion works")
    elif sharpe > 0.5:
        print(f"\n🧪 TESTING - Moderate edge")
    else:
        print(f"\n❌ REJECTED - ATR expansion not predictive")

print("="*70)
