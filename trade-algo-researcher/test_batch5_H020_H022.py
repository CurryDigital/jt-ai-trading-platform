#!/usr/bin/env python3
"""
BATCH 5: H020-H022 (Final batch to reach 10)
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
print('H020: AMD Momentum (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
amd['date'] = pd.to_datetime(amd['date'])
amd['sma20'] = amd['close'].rolling(20).mean()

train = amd[(amd['date'] >= '2021-01-01') & (amd['date'] <= '2022-12-31')]
test = amd[(amd['date'] >= '2023-01-01') & (amd['date'] <= '2024-12-31')]
validate = amd[(amd['date'] >= '2025-01-01') & (amd['date'] <= '2026-02-20')]

def test_amd(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_amd(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_amd(test)
v_res = test_amd(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H020', 'AMD Momentum', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H021: GOOGL Trend Following')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
googl['date'] = pd.to_datetime(googl['date'])
googl['sma50'] = googl['close'].rolling(50).mean()

train = googl[(googl['date'] >= '2021-01-01') & (googl['date'] <= '2022-12-31')]
test = googl[(googl['date'] >= '2023-01-01') & (googl['date'] <= '2024-12-31')]
validate = googl[(googl['date'] >= '2025-01-01') & (googl['date'] <= '2026-02-20')]

def test_googl(period_df):
    trades = []
    for i in range(50, len(period_df) - 10):
        if pd.notna(period_df['sma50'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma50'].iloc[i]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_googl(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_googl(test)
v_res = test_googl(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H021', 'GOOGL Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H022: HK Tech Momentum (0700.HK)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '0700.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
hk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
hk['date'] = pd.to_datetime(hk['date'])
hk['sma20'] = hk['close'].rolling(20).mean()

train = hk[(hk['date'] >= '2021-01-01') & (hk['date'] <= '2022-12-31')]
test = hk[(hk['date'] >= '2023-01-01') & (hk['date'] <= '2024-12-31')]
validate = hk[(hk['date'] >= '2025-01-01') & (hk['date'] <= '2026-02-20')]

def test_hk(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_hk(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_hk(test)
v_res = test_hk(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H022', '0700.HK Momentum', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BATCH 5 SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
