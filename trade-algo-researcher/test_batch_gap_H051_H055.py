#!/usr/bin/env python3
"""
BATCH: Gap Fill, Opening Range Breakout Strategies
H051-H055
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
print('H051: SPY Gap Fill (Down gap → buy)')
print('='*90)

cursor.execute('''SELECT date, open::float, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['prev_close'] = spy['close'].shift(1)
spy['gap_pct'] = (spy['open'] - spy['prev_close']) / spy['prev_close'] * 100

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_gap_fill(period_df):
    trades = []
    for i in range(1, len(period_df) - 1):
        # Down gap > 1%
        if period_df['gap_pct'].iloc[i] < -1.0:
            entry = period_df['open'].iloc[i]
            exit_p = period_df['close'].iloc[i]  # Same day close
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_gap_fill(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

# NVDA Trend with RSI filter
print('\n' + '='*90)
print('H052: NVDA Trend (Price > SMA20) + RSI > 50')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['sma20'] = nvda['close'].rolling(20).mean()

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

nvda['rsi'] = rsi(nvda['close'])

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_nvda_trend_rsi(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['sma20'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] > 50):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_nvda_trend_rsi(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_nvda_trend_rsi(test)
v_res = test_nvda_trend_rsi(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H052', 'NVDA Trend+RSI', verdict, t_res['win_rate'], v_res['win_rate']))

# QQQ Momentum with volume
print('\n' + '='*90)
print('H053: QQQ Momentum + Volume > 1.3x')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['sma20'] = qqq['close'].rolling(20).mean()
qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
qqq['vol_ratio'] = qqq['volume'] / qqq['vol_avg']

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_qqq_vol(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['sma20'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.3):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_qqq_vol(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_qqq_vol(test)
v_res = test_qqq_vol(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H053', 'QQQ Momentum+Vol', verdict, t_res['win_rate'], v_res['win_rate']))

# SPY 50-day MA bounce
print('\n' + '='*90)
print('H054: SPY Pullback to SMA50')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy2['date'] = pd.to_datetime(spy2['date'])
spy2['sma50'] = spy2['close'].rolling(50).mean()
spy2['rsi'] = rsi(spy2['close'])

test = spy2[(spy2['date'] >= '2023-01-01') & (spy2['date'] <= '2024-12-31')]
validate = spy2[(spy2['date'] >= '2025-01-01') & (spy2['date'] <= '2026-02-20')]

def test_spy_sma50(period_df):
    trades = []
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i] * 0.98 and  # Near SMA50
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
    res = test_spy_sma50(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_spy_sma50(test)
v_res = test_spy_sma50(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H054', 'SPY SMA50 Bounce', verdict, t_res['win_rate'], v_res['win_rate']))

# AAPL 20-day high
print('\n' + '='*90)
print('H055: AAPL New 20-Day High')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
aapl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
aapl['date'] = pd.to_datetime(aapl['date'])
aapl['high20'] = aapl['close'].rolling(20).max()

test = aapl[(aapl['date'] >= '2023-01-01') & (aapl['date'] <= '2024-12-31')]
validate = aapl[(aapl['date'] >= '2025-01-01') & (aapl['date'] <= '2026-02-20')]

def test_aapl_high(period_df):
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
    res = test_aapl_high(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_aapl_high(test)
v_res = test_aapl_high(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H055', 'AAPL 20D High', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
