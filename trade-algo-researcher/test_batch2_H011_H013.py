#!/usr/bin/env python3
"""
NEXT BATCH: 8 More Hypotheses (Lessons Applied)
Relaxed filters for sufficient trades, focus on regime detection and momentum
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
print('H011: QQQ RSI < 30 Mean Reversion (Relaxed Filter)')
print('='*90)

# Get QQQ
cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

qqq['rsi'] = rsi(qqq['close'])

train = qqq[(qqq['date'] >= '2021-01-01') & (qqq['date'] <= '2022-12-31')]
test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_rsi(period_df, threshold=30):
    trades = []
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < threshold:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100, 'avg_ret': r.mean()}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_rsi(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win, {res['avg_ret']:.2f}% avg")
    else:
        print(f"{name}: Insufficient trades")

# Classification
t_res = test_rsi(test)
v_res = test_rsi(validate)
if t_res and v_res:
    if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
        verdict = '✅ VALIDATED'
    else:
        verdict = '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H011', 'QQQ RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H012: SPY Golden Cross Trend Following')
print('='*90)

# Get SPY
cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['sma50'] = spy['close'].rolling(50).mean()
spy['sma200'] = spy['close'].rolling(200).mean()

train = spy[(spy['date'] >= '2021-01-01') & (spy['date'] <= '2022-12-31')]
test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_golden_cross(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['sma50'].iloc[i]) and pd.notna(period_df['sma200'].iloc[i]) and
            period_df['sma50'].iloc[i] > period_df['sma200'].iloc[i] and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100, 'avg_ret': r.mean()}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_golden_cross(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_golden_cross(test)
v_res = test_golden_cross(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H012', 'SPY Golden Cross', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H013: NVDA Pullback to SMA20')
print('='*90)

# Get NVDA
cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['sma20'] = nvda['close'].rolling(20).mean()

train = nvda[(nvda['date'] >= '2021-01-01') & (nvda['date'] <= '2022-12-31')]
test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_pullback(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        # Price pulls back to near SMA20 in uptrend
        if (pd.notna(period_df['sma20'].iloc[i]) and
            period_df['close'].iloc[i-1] > period_df['sma20'].iloc[i-1] and  # Uptrend
            period_df['close'].iloc[i] < period_df['sma20'].iloc[i] * 1.02 and  # Near SMA20
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i] * 0.98):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+5, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
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
    results_summary.append(('H013', 'NVDA Pullback SMA20', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('SUMMARY BATCH 2')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
