#!/usr/bin/env python3
"""
BATCH: More US Stocks — MSTR, COIN, AMD, NVDA Variations
H081-H085
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

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

# MSTR Trend
print('='*90)
print('H081: MSTR Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'MSTR' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
mstr = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
mstr['date'] = pd.to_datetime(mstr['date'])
mstr['sma20'] = mstr['close'].rolling(20).mean()

test = mstr[(mstr['date'] >= '2023-01-01') & (mstr['date'] <= '2024-12-31')]
validate = mstr[(mstr['date'] >= '2025-01-01') & (mstr['date'] <= '2026-02-20')]

def test_trend20(period_df):
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

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_trend20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_trend20(test)
v_res = test_trend20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H081', 'MSTR Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# MSTR RSI < 30
print('\n' + '='*90)
print('H082: MSTR RSI < 30 Mean Reversion')
print('='*90)

mstr2 = mstr.copy()
mstr2['rsi'] = rsi(mstr2['close'])

test = mstr2[(mstr2['date'] >= '2023-01-01') & (mstr2['date'] <= '2024-12-31')]
validate = mstr2[(mstr2['date'] >= '2025-01-01') & (mstr2['date'] <= '2026-02-20')]

def test_rsi30(period_df):
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

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_rsi30(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi30(test)
v_res = test_rsi30(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H082', 'MSTR RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

# COIN Trend
print('\n' + '='*90)
print('H083: COIN Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'COIN' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
coin = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
coin['date'] = pd.to_datetime(coin['date'])
coin['sma20'] = coin['close'].rolling(20).mean()

test = coin[(coin['date'] >= '2023-01-01') & (coin['date'] <= '2024-12-31')]
validate = coin[(coin['date'] >= '2025-01-01') & (coin['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_trend20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_trend20(test)
v_res = test_trend20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H083', 'COIN Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# COIN RSI < 30
print('\n' + '='*90)
print('H084: COIN RSI < 30 Mean Reversion')
print('='*90)

coin2 = coin.copy()
coin2['rsi'] = rsi(coin2['close'])

test = coin2[(coin2['date'] >= '2023-01-01') & (coin2['date'] <= '2024-12-31')]
validate = coin2[(coin2['date'] >= '2025-01-01') & (coin2['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_rsi30(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi30(test)
v_res = test_rsi30(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H084', 'COIN RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

# AMD Trend
print('\n' + '='*90)
print('H085: AMD Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
amd['date'] = pd.to_datetime(amd['date'])
amd['sma20'] = amd['close'].rolling(20).mean()

test = amd[(amd['date'] >= '2023-01-01') & (amd['date'] <= '2024-12-31')]
validate = amd[(amd['date'] >= '2025-01-01') & (amd['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_trend20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_trend20(test)
v_res = test_trend20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H085', 'AMD Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
