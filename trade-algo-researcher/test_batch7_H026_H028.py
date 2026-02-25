#!/usr/bin/env python3
"""
BATCH 7: H026-H028 (Final 3 to reach 10)
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
print('H026: NVDA Golden Cross')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['sma50'] = nvda['close'].rolling(50).mean()
nvda['sma200'] = nvda['close'].rolling(200).mean()

train = nvda[(nvda['date'] >= '2021-01-01') & (nvda['date'] <= '2022-12-31')]
test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_gc(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['sma50'].iloc[i]) and pd.notna(period_df['sma200'].iloc[i]) and
            period_df['sma50'].iloc[i] > period_df['sma200'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_gc(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_gc(test)
v_res = test_gc(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H026', 'NVDA Golden Cross', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H027: AAPL Trend Following')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
aapl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
aapl['date'] = pd.to_datetime(aapl['date'])
aapl['sma50'] = aapl['close'].rolling(50).mean()

train = aapl[(aapl['date'] >= '2021-01-01') & (aapl['date'] <= '2022-12-31')]
test = aapl[(aapl['date'] >= '2023-01-01') & (aapl['date'] <= '2024-12-31')]
validate = aapl[(aapl['date'] >= '2025-01-01') & (aapl['date'] <= '2026-02-20')]

def test_aapl(period_df):
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
    res = test_aapl(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_aapl(test)
v_res = test_aapl(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H027', 'AAPL Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H028: MSFT RSI < 30 Mean Reversion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'MSFT' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
msft = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
msft['date'] = pd.to_datetime(msft['date'])

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

msft['rsi'] = rsi(msft['close'])

train = msft[(msft['date'] >= '2021-01-01') & (msft['date'] <= '2022-12-31')]
test = msft[(msft['date'] >= '2023-01-01') & (msft['date'] <= '2024-12-31')]
validate = msft[(msft['date'] >= '2025-01-01') & (msft['date'] <= '2026-02-20')]

def test_msft(period_df):
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
    res = test_msft(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_msft(test)
v_res = test_msft(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H028', 'MSFT RSI<30 MR', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BATCH 7 SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
