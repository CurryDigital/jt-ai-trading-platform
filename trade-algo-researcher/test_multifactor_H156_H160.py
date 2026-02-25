#!/usr/bin/env python3
"""
MULTI-FACTOR COMBINATIONS: H156-H170
RSI + Trend + Volume combinations
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

# H156: RSI < 30 + Above SMA200 (Bull market mean reversion)
print('='*90)
print('H156: RSI < 30 + Above SMA200 (Bull market MR)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['rsi'] = rsi(qqq['close'])
qqq['sma200'] = qqq['close'].rolling(200).mean()

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_bull_mr(period_df):
    trades = []
    for i in range(200, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['sma200'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma200'].iloc[i]):  # Only in bull
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_bull_mr(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bull_mr(test)
v_res = test_bull_mr(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H156', 'QQQ RSI+SMA200', t_res['win_rate'], v_res['win_rate']))

# H157: RSI < 30 + High Volume (Capitulation)
print('\n' + '='*90)
print('H157: RSI < 30 + Volume > 1.5x (Capitulation)')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
spy['date'] = pd.to_datetime(spy['date'])
spy['rsi'] = rsi(spy['close'])
spy['vol_avg'] = spy['volume'].rolling(20).mean()
spy['vol_ratio'] = spy['volume'] / spy['vol_avg']

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_capitulation(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.5):  # High volume
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 5:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_capitulation(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_capitulation(test)
v_res = test_capitulation(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H157', 'SPY RSI+HighVol', t_res['win_rate'], v_res['win_rate']))

# H158: 3-Day Consecutive Down + RSI < 40
print('\n' + '='*90)
print('H158: 3-Day Consecutive Down + RSI < 40')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['rsi'] = rsi(nvda['close'])

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_3down(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if (period_df['close'].iloc[i] < period_df['close'].iloc[i-1] and
            period_df['close'].iloc[i-1] < period_df['close'].iloc[i-2] and
            period_df['close'].iloc[i-2] < period_df['close'].iloc[i-3] and
            pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 40):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_3down(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_3down(test)
v_res = test_3down(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H158', 'NVDA 3Down+RSI', t_res['win_rate'], v_res['win_rate']))

# H159: Gap Down + RSI < 35
print('\n' + '='*90)
print('H159: Gap Down > 2% + RSI < 35')
print('='*90)

cursor.execute('''SELECT date, open::float, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
qqq2['date'] = pd.to_datetime(qqq2['date'])
qqq2['prev_close'] = qqq2['close'].shift(1)
qqq2['gap'] = (qqq2['open'] - qqq2['prev_close']) / qqq2['prev_close'] * 100
qqq2['rsi'] = rsi(qqq2['close'])

test = qqq2[(qqq2['date'] >= '2023-01-01') & (qqq2['date'] <= '2024-12-31')]
validate = qqq2[(qqq2['date'] >= '2025-01-01') & (qqq2['date'] <= '2026-02-20')]

def test_gap_down(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if (period_df['gap'].iloc[i] < -2.0 and  # Gap down > 2%
            pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 35):
            entry = period_df['open'].iloc[i]  # Buy at open
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_gap_down(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_gap_down(test)
v_res = test_gap_down(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H159', 'QQQ GapDown+RSI', t_res['win_rate'], v_res['win_rate']))

# H160: Inside Day Breakout
print('\n' + '='*90)
print('H160: Inside Day + Next Day Breakout')
print('='*90)

cursor.execute('''SELECT date, high::float, low::float, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'high', 'low', 'close'])
spy2['date'] = pd.to_datetime(spy2['date'])
spy2['prev_high'] = spy2['high'].shift(1)
spy2['prev_low'] = spy2['low'].shift(1)

test = spy2[(spy2['date'] >= '2023-01-01') & (spy2['date'] <= '2024-12-31')]
validate = spy2[(spy2['date'] >= '2025-01-01') & (spy2['date'] <= '2026-02-20')]

def test_inside_day(period_df):
    trades = []
    for i in range(2, len(period_df) - 5):
        # Inside day: today's range inside yesterday's
        inside = (period_df['high'].iloc[i-1] < period_df['prev_high'].iloc[i-1] and
                  period_df['low'].iloc[i-1] > period_df['prev_low'].iloc[i-1])
        # Breakout next day
        breakout = period_df['close'].iloc[i] > period_df['prev_high'].iloc[i-1]
        if inside and breakout:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_inside_day(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_inside_day(test)
v_res = test_inside_day(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H160', 'SPY Inside Day BO', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('MULTI-FACTOR STRATEGIES - NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
