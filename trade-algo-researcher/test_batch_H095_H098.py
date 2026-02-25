#!/usr/bin/env python3
"""
CONTINUOUS TESTING: More combinations
H095-H100
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

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

results_summary = []

# H095: NVDA 20-Day High Breakout
print('='*90)
print('H095: NVDA 20-Day High Breakout')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['high20'] = nvda['close'].rolling(20).max()

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_high_breakout(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if period_df['close'].iloc[i] > period_df['high20'].iloc[i-1]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_high_breakout(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_high_breakout(test)
v_res = test_high_breakout(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H095', 'NVDA 20D High', verdict, t_res['win_rate'], v_res['win_rate']))

# H096: AMD Pullback to SMA50
print('\n' + '='*90)
print('H096: AMD Pullback to SMA50')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
amd['date'] = pd.to_datetime(amd['date'])
amd['sma50'] = amd['close'].rolling(50).mean()
amd['rsi'] = rsi(amd['close'])

test = amd[(amd['date'] >= '2023-01-01') & (amd['date'] <= '2024-12-31')]
validate = amd[(amd['date'] >= '2025-01-01') & (amd['date'] <= '2026-02-20')]

def test_pullback(period_df):
    trades = []
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i] * 0.98 and
            period_df['close'].iloc[i] < period_df['sma50'].iloc[i] * 1.02 and
            pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 45):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_pullback(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_pullback(test)
v_res = test_pullback(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H096', 'AMD SMA50 Pullback', verdict, t_res['win_rate'], v_res['win_rate']))

# H097: META Volume + Price
print('\n' + '='*90)
print('H097: META Volume + Price Breakout')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'META' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
meta = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
meta['date'] = pd.to_datetime(meta['date'])
meta['sma20'] = meta['close'].rolling(20).mean()
meta['vol_avg'] = meta['volume'].rolling(20).mean()
meta['vol_ratio'] = meta['volume'] / meta['vol_avg']

test = meta[(meta['date'] >= '2023-01-01') & (meta['date'] <= '2024-12-31')]
validate = meta[(meta['date'] >= '2025-01-01') & (meta['date'] <= '2026-02-20')]

def test_vol_breakout(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.5 and
            pd.notna(period_df['sma20'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_vol_breakout(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_vol_breakout(test)
v_res = test_vol_breakout(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H097', 'META Vol+Price', verdict, t_res['win_rate'], v_res['win_rate']))

# H098: TSLA RSI Divergence
print('\n' + '='*90)
print('H098: TSLA RSI Divergence (Price lower, RSI higher)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'TSLA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
tsla = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
tsla['date'] = pd.to_datetime(tsla['date'])
tsla['rsi'] = rsi(tsla['close'])

test = tsla[(tsla['date'] >= '2023-01-01') & (tsla['date'] <= '2024-12-31')]
validate = tsla[(tsla['date'] >= '2025-01-01') & (tsla['date'] <= '2026-02-20')]

def test_divergence(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (period_df['close'].iloc[i] < period_df['close'].iloc[i-5] and  # Price lower
            pd.notna(period_df['rsi'].iloc[i]) and
            pd.notna(period_df['rsi'].iloc[i-5]) and
            period_df['rsi'].iloc[i] > period_df['rsi'].iloc[i-5] + 5):  # RSI higher
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_divergence(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

print('\n' + '='*90)
print('SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
