#!/usr/bin/env python3
"""
BATCH 6: H023-H025 (Final 4 to reach 10)
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
print('H023: SPY RSI < 30 Mean Reversion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

spy['rsi'] = rsi(spy['close'])

train = spy[(spy['date'] >= '2021-01-01') & (spy['date'] <= '2022-12-31')]
test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_spy(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_spy(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_spy(test)
v_res = test_spy(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H023', 'SPY RSI<30 MR', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H024: XLK Tech ETF Momentum')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk['sma20'] = xlk['close'].rolling(20).mean()

train = xlk[(xlk['date'] >= '2021-01-01') & (xlk['date'] <= '2022-12-31')]
test = xlk[(xlk['date'] >= '2023-01-01') & (xlk['date'] <= '2024-12-31')]
validate = xlk[(xlk['date'] >= '2025-01-01') & (xlk['date'] <= '2026-02-20')]

def test_xlk(period_df):
    trades = []
    for i in range(20, len(period_df) - 10):
        if pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_xlk(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_xlk(test)
v_res = test_xlk(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H024', 'XLK Momentum', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H025: XLF Financials ETF Mean Reversion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlf = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlf['date'] = pd.to_datetime(xlf['date'])
xlf['rsi'] = rsi(xlf['close'])

train = xlf[(xlf['date'] >= '2021-01-01') & (xlf['date'] <= '2022-12-31')]
test = xlf[(xlf['date'] >= '2023-01-01') & (xlf['date'] <= '2024-12-31')]
validate = xlf[(xlf['date'] >= '2025-01-01') & (xlf['date'] <= '2026-02-20')]

def test_xlf(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 35:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_xlf(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_xlf(test)
v_res = test_xlf(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H025', 'XLF RSI<35 MR', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BATCH 6 SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
