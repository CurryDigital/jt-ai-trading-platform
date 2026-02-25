#!/usr/bin/env python3
"""
NEW BATCH: Pairs Trading, Relative Value
H043-H048
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
print('H043: NVDA vs AMD Pair (Long NVDA when outperforms)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'nvda'])
nvda['date'] = pd.to_datetime(nvda['date'])

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'amd'])
amd['date'] = pd.to_datetime(amd['date'])

df = pd.merge(nvda, amd, on='date')
df['ratio'] = df['nvda'] / df['amd']
df['ratio_sma20'] = df['ratio'].rolling(20).mean()

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_pair(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if pd.notna(period_df['ratio_sma20'].iloc[i]) and period_df['ratio'].iloc[i] > period_df['ratio_sma20'].iloc[i]:
            entry = period_df['nvda'].iloc[i]
            exit_p = period_df['nvda'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_pair(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_pair(test)
v_res = test_pair(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H043', 'NVDA/AMD Pair', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H044: SPY vs QQQ Momentum Divergence')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'spy'])
spy['date'] = pd.to_datetime(spy['date'])

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'qqq'])
qqq['date'] = pd.to_datetime(qqq['date'])

df = pd.merge(spy, qqq, on='date')
df['spy_ret'] = df['spy'].pct_change(5)
df['qqq_ret'] = df['qqq'].pct_change(5)

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_divergence(period_df):
    trades = []
    for i in range(10, len(period_df) - 5):
        if (pd.notna(period_df['spy_ret'].iloc[i]) and pd.notna(period_df['qqq_ret'].iloc[i]) and
            period_df['spy_ret'].iloc[i] > 0.02 and  # SPY up 2%
            period_df['qqq_ret'].iloc[i] < 0.01):   # QQQ flat
            entry = period_df['qqq'].iloc[i]  # Buy QQQ expecting catch-up
            exit_p = period_df['qqq'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_divergence(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_divergence(test)
v_res = test_divergence(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H044', 'SPY/QQQ Divergence', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H045: GOOGL vs MSFT Pair')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'googl'])
googl['date'] = pd.to_datetime(googl['date'])

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'MSFT' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
msft = pd.DataFrame(cursor.fetchall(), columns=['date', 'msft'])
msft['date'] = pd.to_datetime(msft['date'])

df = pd.merge(googl, msft, on='date')
df['ratio'] = df['googl'] / df['msft']
df['ratio_sma20'] = df['ratio'].rolling(20).mean()

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_pair2(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if pd.notna(period_df['ratio_sma20'].iloc[i]) and period_df['ratio'].iloc[i] > period_df['ratio_sma20'].iloc[i]:
            entry = period_df['googl'].iloc[i]
            exit_p = period_df['googl'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_pair2(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_pair2(test)
v_res = test_pair2(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H045', 'GOOGL/MSFT Pair', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('SUMMARY BATCH')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
