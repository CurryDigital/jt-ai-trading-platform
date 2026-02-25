#!/usr/bin/env python3
"""
BATCH 4: H017-H019 (Final batch to reach 10)
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

results_summary = []

print('='*90)
print('H017: TSLA Mean Reversion (RSI < 35)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'TSLA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
tsla = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
tsla['date'] = pd.to_datetime(tsla['date'])

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

tsla['rsi'] = rsi(tsla['close'])
tsla['sma50'] = tsla['close'].rolling(50).mean()

train = tsla[(tsla['date'] >= '2021-01-01') & (tsla['date'] <= '2022-12-31')]
test = tsla[(tsla['date'] >= '2023-01-01') & (tsla['date'] <= '2024-12-31')]
validate = tsla[(tsla['date'] >= '2025-01-01') & (tsla['date'] <= '2026-02-20')]

def test_tsla(period_df):
    trades = []
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 35 and
            pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):  # Only in uptrend
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_tsla(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_tsla(test)
v_res = test_tsla(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H017', 'TSLA MR Uptrend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H018: META 20-Day High Breakout')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'META' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
meta = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
meta['date'] = pd.to_datetime(meta['date'])
meta['high20'] = meta['close'].rolling(20).max()

train = meta[(meta['date'] >= '2021-01-01') & (meta['date'] <= '2022-12-31')]
test = meta[(meta['date'] >= '2023-01-01') & (meta['date'] <= '2024-12-31')]
validate = meta[(meta['date'] >= '2025-01-01') & (meta['date'] <= '2026-02-20')]

def test_meta(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['high20'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['high20'].iloc[i-1]):  # New 20-day high
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_meta(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_meta(test)
v_res = test_meta(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H018', 'META 20D High BO', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H019: QQQ vs SPY Relative Strength')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])

merged = pd.merge(qqq, spy, on='date', suffixes=('_qqq', '_spy'))
merged['ratio'] = merged['close_qqq'] / merged['close_spy']
merged['ratio_sma20'] = merged['ratio'].rolling(20).mean()

train = merged[(merged['date'] >= '2021-01-01') & (merged['date'] <= '2022-12-31')]
test = merged[(merged['date'] >= '2023-01-01') & (merged['date'] <= '2024-12-31')]
validate = merged[(merged['date'] >= '2025-01-01') & (merged['date'] <= '2026-02-20')]

def test_relative(period_df):
    trades = []
    for i in range(20, len(period_df) - 10):
        if pd.notna(period_df['ratio_sma20'].iloc[i]) and period_df['ratio'].iloc[i] > period_df['ratio_sma20'].iloc[i]:
            entry = period_df['close_qqq'].iloc[i]
            exit_p = period_df['close_qqq'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_relative(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_relative(test)
v_res = test_relative(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H019', 'QQQ/SPY Rel Strength', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BATCH 4 SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
