#!/usr/bin/env python3
"""
3-TIER TESTING: H003 - Sector Rotation Momentum (XLK vs XLF)
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*90)
print('H003: Sector Rotation Momentum (XLK vs XLF)')
print('Entry: XLK/XLF ratio > 20d SMA + XLK > SMA50')
print('Exit: 10 days')
print('='*90)

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

# Get XLK
cursor.execute('''
    SELECT date, close::float FROM bronze.yf_prices
    WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
xlk_data = cursor.fetchall()
xlk_df = pd.DataFrame(xlk_data, columns=['date', 'xlk'])
xlk_df['date'] = pd.to_datetime(xlk_df['date'])

# Get XLF
cursor.execute('''
    SELECT date, close::float FROM bronze.yf_prices
    WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
xlf_data = cursor.fetchall()
xlf_df = pd.DataFrame(xlf_data, columns=['date', 'xlf'])
xlf_df['date'] = pd.to_datetime(xlf_df['date'])

# Merge
df = pd.merge(xlk_df, xlf_df, on='date')
df['ratio'] = df['xlk'] / df['xlf']
df['ratio_sma20'] = df['ratio'].rolling(20).mean()
df['xlk_sma50'] = df['xlk'].rolling(50).mean()

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_strategy(period_df):
    trades = []
    
    for i in range(50, len(period_df) - 10):
        if (pd.notna(period_df['ratio_sma20'].iloc[i]) and
            period_df['ratio'].iloc[i] > period_df['ratio_sma20'].iloc[i] and
            pd.notna(period_df['xlk_sma50'].iloc[i]) and
            period_df['xlk'].iloc[i] > period_df['xlk_sma50'].iloc[i]):
            
            entry = period_df['xlk'].iloc[i]
            exit_p = period_df['xlk'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10:
        return None
    
    r = pd.Series(trades)
    wr = (r > 0).mean()
    avg_ret = r.mean()
    sharpe = r.mean() / r.std() * np.sqrt(252/10) if r.std() > 0 else 0
    
    n = len(trades)
    ci_low = max(0, wr - 1.96 * np.sqrt(wr * (1-wr) / n)) if n > 0 else 0
    ci_high = min(1, wr + 1.96 * np.sqrt(wr * (1-wr) / n)) if n > 0 else 1
    
    return {'trades': n, 'win_rate': wr * 100, 'avg_return': avg_ret, 'sharpe': sharpe, 'ci_low': ci_low * 100, 'ci_high': ci_high * 100}

for name, period in [('Train (2021-22)', train), ('Test (2023-24)', test), ('Validate (2025-26)', validate)]:
    print(f'\n{name}:')
    res = test_strategy(period)
    if res:
        print(f"  Trades: {res['trades']}, Win: {res['win_rate']:.1f}% [{res['ci_low']:.1f}%, {res['ci_high']:.1f}%]")
    else:
        print('  INSUFFICIENT TRADES')

conn.close()
