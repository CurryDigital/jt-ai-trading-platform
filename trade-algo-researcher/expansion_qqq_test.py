#!/usr/bin/env python3
"""
EXPANSION CYCLE: Test SPY Regime Filter on QQQ (Nasdaq ETF)
Compare QQQ vs MSTR/COIN/RIOT behavior
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*70)
print('EXPANSION CYCLE: QQQ + SPY Regime Filter')
print('='*70)

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

# Get QQQ data from unified_prices
cursor.execute('''
SELECT t.date, t.close::float, ti.rsi_14
FROM silver.unified_prices t
JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker = 'QQQ' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.date
''')
qqq_data = cursor.fetchall()
qqq_df = pd.DataFrame(qqq_data, columns=['date', 'close', 'rsi_14'])

# Get SPY data
cursor.execute('''
SELECT t.date, t.close::float
FROM silver.unified_prices t
WHERE t.ticker = 'SPY' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close'])
spy_df['spy_sma200'] = spy_df['spy_close'].rolling(200, min_periods=200).mean()
spy_df['spy_above_200d'] = spy_df['spy_close'] > spy_df['spy_sma200']

# Merge
df = qqq_df.merge(spy_df, on='date', how='inner').dropna(subset=['spy_sma200'])

print(f'QQQ records: {len(qqq_df)}')
print(f'After SPY merge: {len(df)}')
print(f'Date range: {df["date"].min()} to {df["date"].max()}')
print(f'RSI range: {df["rsi_14"].min():.1f} to {df["rsi_14"].max():.1f}')

# Test variants
variants = [
    ('RSI<25 (no filter)', lambda r: r['rsi_14'] < 25),
    ('RSI<25 + SPY>200d', lambda r: r['rsi_14'] < 25 and r['spy_above_200d']),
]

results = []
print('\n--- QQQ Backtest Results ---')
for name, condition in variants:
    trades = []
    for idx, row in df.iterrows():
        if pd.notna(row['rsi_14']) and condition(row):
            entry_idx = df.index.get_loc(idx)
            exit_idx = entry_idx + 10
            if exit_idx < len(df):
                entry_price = row['close']
                exit_price = df.iloc[exit_idx]['close']
                ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 5:
        win_rate = (pd.Series(trades) > 0).mean() * 100
        avg_ret = pd.Series(trades).mean()
        results.append((name, len(trades), win_rate, avg_ret))
        status = '✅' if win_rate >= 55 else '❌'
        print(f'{status} {name}: {len(trades)} trades, {win_rate:.1f}% win, {avg_ret:.2f}% avg')

# Compare to crypto
print('\n' + '='*70)
print('COMPARISON: QQQ vs Crypto Assets')
print('='*70)
print('\nAsset        | Baseline | With SPY Filter | Improvement')
print('-'*70)
print('MSTR         | 63.2%    | 81.2%           | +18.0% ⭐')
print('COIN         | 85.7%    | 85.7%           | +0.0%')
print('RIOT         | 59.8%    | 68.4%           | +8.6%')

if len(results) >= 1:
    baseline = results[0][2] if 'no filter' in results[0][0] else 0
    if len(results) >= 2:
        with_filter = results[1][2]
        improvement = with_filter - baseline
        print(f'QQQ          | {baseline:.1f}%    | {with_filter:.1f}%           | {improvement:+.1f}%')
    else:
        print(f'QQQ          | {baseline:.1f}%    | N/A             | N/A')

print('\n' + '='*70)
print('INSIGHT:')
print('='*70)
print('If QQQ shows similar improvement to MSTR (+15-20%), then SPY filter')
print('is a universal alpha factor for mean reversion.')
print('If QQQ shows no improvement like COIN, then effect is asset-specific.')
print('='*70)

conn.close()
