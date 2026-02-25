#!/usr/bin/env python3
"""
NEW BATCH: Volume-based, Multi-indicator Combinations
H039-H044
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
print('H039: TSLA Volume + Price Breakout')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'TSLA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
tsla = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
tsla['date'] = pd.to_datetime(tsla['date'])
tsla['vol_avg'] = tsla['volume'].rolling(20).mean()
tsla['vol_ratio'] = tsla['volume'] / tsla['vol_avg']
tsla['sma20'] = tsla['close'].rolling(20).mean()

def test_volume_breakout(period_df):
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

train = tsla[(tsla['date'] >= '2021-01-01') & (tsla['date'] <= '2022-12-31')]
test = tsla[(tsla['date'] >= '2023-01-01') & (tsla['date'] <= '2024-12-31')]
validate = tsla[(tsla['date'] >= '2025-01-01') & (tsla['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_volume_breakout(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_volume_breakout(test)
v_res = test_volume_breakout(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H039', 'TSLA Vol+Price BO', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H040: AMD Stochastic Oversold Bounce')
print('='*90)

cursor.execute('''SELECT date, close::float, low::float, high::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'low', 'high'])
amd['date'] = pd.to_datetime(amd['date'])

# Stochastic calculation
amd['lowest_14'] = amd['low'].rolling(14).min()
amd['highest_14'] = amd['high'].rolling(14).max()
amd['stoch_k'] = 100 * (amd['close'] - amd['lowest_14']) / (amd['highest_14'] - amd['lowest_14'])

def test_stoch(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['stoch_k'].iloc[i]) and period_df['stoch_k'].iloc[i] < 20:  # Oversold
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = amd[(amd['date'] >= '2021-01-01') & (amd['date'] <= '2022-12-31')]
test = amd[(amd['date'] >= '2023-01-01') & (amd['date'] <= '2024-12-31')]
validate = amd[(amd['date'] >= '2025-01-01') & (amd['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_stoch(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_stoch(test)
v_res = test_stoch(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H040', 'AMD Stoch <20', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H041: META Hammer Candlestick Pattern')
print('='*90)

cursor.execute('''SELECT date, open::float, high::float, low::float, close::float FROM silver.unified_prices WHERE ticker = 'META' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
meta = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'high', 'low', 'close'])
meta['date'] = pd.to_datetime(meta['date'])

def test_hammer(period_df):
    trades = []
    for i in range(1, len(period_df) - 5):
        curr = period_df.iloc[i]
        body = abs(curr['close'] - curr['open'])
        lower_shadow = min(curr['close'], curr['open']) - curr['low']
        upper_shadow = curr['high'] - max(curr['close'], curr['open'])
        
        # Hammer: small body, long lower shadow, little/no upper shadow
        is_hammer = (lower_shadow > 2 * body) and (upper_shadow < body) and (curr['close'] > curr['open'])
        
        if is_hammer:
            entry = curr['close']
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = meta[(meta['date'] >= '2021-01-01') & (meta['date'] <= '2022-12-31')]
test = meta[(meta['date'] >= '2023-01-01') & (meta['date'] <= '2024-12-31')]
validate = meta[(meta['date'] >= '2025-01-01') & (meta['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_hammer(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_hammer(test)
v_res = test_hammer(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H041', 'META Hammer', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H042: SPY Three White Soldiers')
print('='*90)

cursor.execute('''SELECT date, open::float, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
spy['date'] = pd.to_datetime(spy['date'])

def test_three_soldiers(period_df):
    trades = []
    for i in range(3, len(period_df) - 5):
        c1 = period_df.iloc[i-2]
        c2 = period_df.iloc[i-1]
        c3 = period_df.iloc[i]
        
        # Three consecutive green candles
        green1 = c1['close'] > c1['open']
        green2 = c2['close'] > c2['open']
        green3 = c3['close'] > c3['open']
        
        if green1 and green2 and green3:
            entry = c3['close']
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = spy[(spy['date'] >= '2021-01-01') & (spy['date'] <= '2022-12-31')]
test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_three_soldiers(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_three_soldiers(test)
v_res = test_three_soldiers(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H042', 'SPY 3 Soldiers', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('SUMMARY BATCH')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
