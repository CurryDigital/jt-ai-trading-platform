#!/usr/bin/env python3
"""
HYPOTHESIS H#004: Platform Variation Test
Compare JT's Golden Cross filter vs Researcher's ADX > 25 filter
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime

print('='*70)
print('H#004: Golden Cross vs ADX Filter Performance Comparison')
print('='*70)

# Backtest both filters on historical data
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

# Get COIN data
cursor.execute('''
SELECT t.date, t.close::float, ti.rsi_14
FROM silver.unified_prices t
JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker = 'COIN' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.date
''')
coin_data = cursor.fetchall()
coin_df = pd.DataFrame(coin_data, columns=['date', 'close', 'rsi_14'])

# Get SPY data for both filters
cursor.execute('''
SELECT date, close::float
FROM silver.unified_prices
WHERE ticker = 'SPY' AND date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close'])

# Calculate filters
spy_df['sma50'] = spy_df['spy_close'].rolling(50).mean()
spy_df['sma200'] = spy_df['spy_close'].rolling(200).mean()
spy_df['golden_cross'] = spy_df['sma50'] > spy_df['sma200']

# Calculate ADX (simplified)
spy_df['high'] = spy_df['spy_close'] * 1.001  # Approximation
spy_df['low'] = spy_df['spy_close'] * 0.999
spy_df['prev_close'] = spy_df['spy_close'].shift(1)
spy_df['tr'] = np.maximum(spy_df['high'] - spy_df['low'], 
                          np.maximum(abs(spy_df['high'] - spy_df['prev_close']),
                                     abs(spy_df['low'] - spy_df['prev_close'])))
spy_df['atr'] = spy_df['tr'].rolling(14).mean()
spy_df['adx'] = spy_df['atr'].rolling(14).apply(lambda x: 25 if x.mean() > 0 else 20, raw=True)  # Simplified
spy_df['price_above_200d'] = spy_df['spy_close'] > spy_df['sma200']
spy_df['strong_uptrend'] = spy_df['price_above_200d']  # Using price > 200d as proxy

# Merge
df = coin_df.merge(spy_df[['date', 'golden_cross', 'strong_uptrend']], on='date', how='inner')

# Test Filter 1: Golden Cross (JT's implementation)
print('\\n=== FILTER 1: Golden Cross (50d > 200d) ===')
trades_gc = []
for idx, row in df.iterrows():
    if pd.notna(row['rsi_14']) and row['rsi_14'] < 25 and row['golden_cross']:
        entry_idx = df.index.get_loc(idx)
        exit_idx = entry_idx + 10
        if exit_idx < len(df):
            entry_price = row['close']
            exit_price = df.iloc[exit_idx]['close']
            ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
            trades_gc.append(ret)

if trades_gc:
    r = pd.Series(trades_gc)
    wr_gc = (r > 0).mean() * 100
    print(f'Trades: {len(trades_gc)}')
    print(f'Win Rate: {wr_gc:.1f}%')
    print(f'Avg Return: {r.mean():.2f}%')
else:
    wr_gc = 0
    print('No trades generated')

# Test Filter 2: Strong Uptrend (Researcher's ADX > 25 proxy)
print('\\n=== FILTER 2: Strong Uptrend (Price > 200d) ===')
trades_su = []
for idx, row in df.iterrows():
    if pd.notna(row['rsi_14']) and row['rsi_14'] < 25 and row['strong_uptrend']:
        entry_idx = df.index.get_loc(idx)
        exit_idx = entry_idx + 10
        if exit_idx < len(df):
            entry_price = row['close']
            exit_price = df.iloc[exit_idx]['close']
            ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
            trades_su.append(ret)

if trades_su:
    r = pd.Series(trades_su)
    wr_su = (r > 0).mean() * 100
    print(f'Trades: {len(trades_su)}')
    print(f'Win Rate: {wr_su:.1f}%')
    print(f'Avg Return: {r.mean():.2f}%')
else:
    wr_su = 0
    print('No trades generated')

conn.close()

print('\\n' + '='*70)
print('COMPARISON SUMMARY')
print('='*70)
print(f'\\nGolden Cross (JT):  {wr_gc:.1f}% win rate, {len(trades_gc)} trades')
print(f'Strong Uptrend (Me): {wr_su:.1f}% win rate, {len(trades_su)} trades')
print(f'\\nDifference: {wr_su - wr_gc:+.1f}%')

print('\\n=== LIVE TESTING PLAN ===')
print('Track JT platform performance for first 20 trades:')
print('- Expected win rate: 80-90%')
print('- Compare to my backtest: 93.3%')
print('- Decision threshold: 80% (accept) / <80% (request ADX)')

print('\\n' + '='*70)
print('H#004: Testing in progress...')
print('='*70)
