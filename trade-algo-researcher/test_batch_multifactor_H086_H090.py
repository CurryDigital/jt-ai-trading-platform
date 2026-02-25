#!/usr/bin/env python3
"""
BATCH: Multi-Factor Combinations
H086-H090
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

# QQQ RSI < 30 + SMA50 support
print('='*90)
print('H086: QQQ RSI < 30 + Price > SMA50')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['rsi'] = rsi(qqq['close'])
qqq['sma50'] = qqq['close'].rolling(50).mean()

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_combo(period_df):
    trades = []
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['sma50'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_combo(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_combo(test)
v_res = test_combo(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H086', 'QQQ RSI+SMA50', verdict, t_res['win_rate'], v_res['win_rate']))

# SPY RSI < 30 + Volume spike
print('\n' + '='*90)
print('H087: SPY RSI < 30 + Volume > 1.3x')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
spy['date'] = pd.to_datetime(spy['date'])
spy['rsi'] = rsi(spy['close'])
spy['vol_avg'] = spy['volume'].rolling(20).mean()
spy['vol_ratio'] = spy['volume'] / spy['vol_avg']

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_vol(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['vol_ratio'].iloc[i]) and period_df['vol_ratio'].iloc[i] > 1.3):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_vol(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_vol(test)
v_res = test_vol(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H087', 'SPY RSI+Vol', verdict, t_res['win_rate'], v_res['win_rate']))

# NVDA Trend + Volume
print('\n' + '='*90)
print('H088: NVDA Trend + Volume > 1.3x')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['sma20'] = nvda['close'].rolling(20).mean()
nvda['vol_avg'] = nvda['volume'].rolling(20).mean()
nvda['vol_ratio'] = nvda['volume'] / nvda['vol_avg']

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_nvda_vol(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            pd.notna(period_df['vol_ratio'].iloc[i]) and period_df['vol_ratio'].iloc[i] > 1.3):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_nvda_vol(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_nvda_vol(test)
v_res = test_nvda_vol(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H088', 'NVDA Trend+Vol', verdict, t_res['win_rate'], v_res['win_rate']))

# AAPL RSI + Trend
print('\n' + '='*90)
print('H089: AAPL RSI < 30 + Price > SMA20')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
aapl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
aapl['date'] = pd.to_datetime(aapl['date'])
aapl['rsi'] = rsi(aapl['close'])
aapl['sma20'] = aapl['close'].rolling(20).mean()

test = aapl[(aapl['date'] >= '2023-01-01') & (aapl['date'] <= '2024-12-31')]
validate = aapl[(aapl['date'] >= '2025-01-01') & (aapl['date'] <= '2026-02-20')]

def test_combo20(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_combo20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_combo20(test)
v_res = test_combo20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H089', 'AAPL RSI+SMA20', verdict, t_res['win_rate'], v_res['win_rate']))

# GOOGL RSI + Trend
print('\n' + '='*90)
print('H090: GOOGL RSI < 30 + Price > SMA20')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
googl['date'] = pd.to_datetime(googl['date'])
googl['rsi'] = rsi(googl['close'])
googl['sma20'] = googl['close'].rolling(20).mean()

test = googl[(googl['date'] >= '2023-01-01') & (googl['date'] <= '2024-12-31')]
validate = googl[(googl['date'] >= '2025-01-01') & (googl['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_combo20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_combo20(test)
v_res = test_combo20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H090', 'GOOGL RSI+SMA20', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
