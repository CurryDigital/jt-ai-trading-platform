#!/usr/bin/env python3
"""
BATCH: HK Stocks Testing
H076-H080
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

# 0700.HK Trend
print('='*90)
print('H076: 0700.HK (Tencent) Trend')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '0700.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
hk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
hk['date'] = pd.to_datetime(hk['date'])
hk['sma20'] = hk['close'].rolling(20).mean()

test = hk[(hk['date'] >= '2023-01-01') & (hk['date'] <= '2024-12-31')]
validate = hk[(hk['date'] >= '2025-01-01') & (hk['date'] <= '2026-02-20')]

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
    results_summary.append(('H076', '0700.HK Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# 0700.HK RSI < 30
print('\n' + '='*90)
print('H077: 0700.HK RSI < 30 Mean Reversion')
print('='*90)

hk2 = hk.copy()
hk2['rsi'] = rsi(hk2['close'])

test = hk2[(hk2['date'] >= '2023-01-01') & (hk2['date'] <= '2024-12-31')]
validate = hk2[(hk2['date'] >= '2025-01-01') & (hk2['date'] <= '2026-02-20')]

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
    results_summary.append(('H077', '0700.HK RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

# 9988.HK (Alibaba) Trend
print('\n' + '='*90)
print('H078: 9988.HK (Alibaba) Trend')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '9988.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
baba = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
baba['date'] = pd.to_datetime(baba['date'])
baba['sma20'] = baba['close'].rolling(20).mean()

test = baba[(baba['date'] >= '2023-01-01') & (baba['date'] <= '2024-12-31')]
validate = baba[(baba['date'] >= '2025-01-01') & (baba['date'] <= '2026-02-20')]

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
    results_summary.append(('H078', '9988.HK Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# 9988.HK RSI < 30
print('\n' + '='*90)
print('H079: 9988.HK RSI < 30 Mean Reversion')
print('='*90)

baba2 = baba.copy()
baba2['rsi'] = rsi(baba2['close'])

test = baba2[(baba2['date'] >= '2023-01-01') & (baba2['date'] <= '2024-12-31')]
validate = baba2[(baba2['date'] >= '2025-01-01') & (baba2['date'] <= '2026-02-20')]

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
    results_summary.append(('H079', '9988.HK RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

# 3690.HK (Meituan) Trend
print('\n' + '='*90)
print('H080: 3690.HK (Meituan) Trend')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '3690.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
meituan = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
meituan['date'] = pd.to_datetime(meituan['date'])
meituan['sma20'] = meituan['close'].rolling(20).mean()

test = meituan[(meituan['date'] >= '2023-01-01') & (meituan['date'] <= '2024-12-31')]
validate = meituan[(meituan['date'] >= '2025-01-01') & (meituan['date'] <= '2026-02-20')]

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
    results_summary.append(('H080', '3690.HK Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
