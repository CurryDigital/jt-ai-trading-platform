#!/usr/bin/env python3
"""
FULL UNIVERSE TESTING: 418 tickers
Test S001-S012 on ALL available tickers
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

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

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_strategy(df, entry_func, exit_days=5):
    """Quick test - Test period only for screening"""
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    # Test period
    trades = []
    for i in range(50, len(test) - exit_days):
        if entry_func(test, i):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + exit_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 5:
        return 0, 0, 0
    
    r = pd.Series(trades)
    test_wr = (r > 0).mean() * 100
    
    # Validate period
    val_trades = []
    for i in range(50, len(validate) - exit_days):
        if entry_func(validate, i):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + exit_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    if len(val_trades) < 3:
        return test_wr, 0, len(trades)
    
    r_val = pd.Series(val_trades)
    val_wr = (r_val > 0).mean() * 100
    
    return test_wr, val_wr, len(trades)

# Get full universe
cursor.execute('''
    SELECT DISTINCT ticker FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
''')
all_tickers = [r[0] for r in cursor.fetchall()]

# Filter for stocks with sufficient data (min 500 records)
valid_tickers = []
for ticker in all_tickers:
    cursor.execute(f"SELECT COUNT(*) FROM silver.unified_prices WHERE ticker = '{ticker}' AND date >= '2021-01-01'")
    count = cursor.fetchone()[0]
    if count >= 500:
        valid_tickers.append(ticker)

print(f'Full Universe: {len(all_tickers)} tickers')
print(f'With sufficient data (500+ records): {len(valid_tickers)} tickers')
print(f'Testing S001 (RSI <30) on {len(valid_tickers)} tickers...\n')

# S001: RSI < 30 - Full Universe
def entry_rsi30(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30

s001_passing = []
count = 0

for ticker in valid_tickers:
    count += 1
    if count % 50 == 0:
        print(f'Progress: {count}/{len(valid_tickers)} tickers tested...')
    
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    
    if len(data) < 200:
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    test_wr, val_wr, n_trades = test_strategy(df, entry_rsi30, 10)
    
    if test_wr >= 60 and val_wr >= 55:
        s001_passing.append((ticker, test_wr, val_wr, n_trades))
        print(f'✅ {ticker}: Test {test_wr:.1f}%, Val {val_wr:.1f}%, Trades {n_trades}')

print(f'\n=== S001 RESULTS ===')
print(f'RSI <30 works on {len(s001_passing)}/{len(valid_tickers)} tickers')
print(f'\nTop performers:')
for t, tw, vw, n in sorted(s001_passing, key=lambda x: x[1], reverse=True)[:20]:
    print(f'  {t}: Test {tw:.1f}%, Val {vw:.1f}%, {n} trades')

conn.close()

print(f'\nFull analysis complete!')
