#!/usr/bin/env python3
"""
BATCH: More Trend Following on Different Stocks
H056-H060
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

# Test MSFT Trend
print('='*90)
print('H056: MSFT Trend (Price > SMA50)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'MSFT' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
msft = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
msft['date'] = pd.to_datetime(msft['date'])
msft['sma50'] = msft['close'].rolling(50).mean()

test = msft[(msft['date'] >= '2023-01-01') & (msft['date'] <= '2024-12-31')]
validate = msft[(msft['date'] >= '2025-01-01') & (msft['date'] <= '2026-02-20')]

def test_trend(period_df):
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

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_trend(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_trend(test)
v_res = test_trend(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H056', 'MSFT Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# Test NVDA RSI < 30
print('\n' + '='*90)
print('H057: NVDA RSI < 30 Mean Reversion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['rsi'] = rsi(nvda['close'])

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_rsi(period_df):
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
    res = test_rsi(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi(test)
v_res = test_rsi(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H057', 'NVDA RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))

# Test GOOGL Trend
print('\n' + '='*90)
print('H058: GOOGL Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
googl['date'] = pd.to_datetime(googl['date'])
googl['sma20'] = googl['close'].rolling(20).mean()

def test_trend20(period_df):
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

test = googl[(googl['date'] >= '2023-01-01') & (googl['date'] <= '2024-12-31')]
validate = googl[(googl['date'] >= '2025-01-01') & (googl['date'] <= '2026-02-20')]

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
    results_summary.append(('H058', 'GOOGL Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# Test TSLA Trend
print('\n' + '='*90)
print('H059: TSLA Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'TSLA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
tsla = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
tsla['date'] = pd.to_datetime(tsla['date'])
tsla['sma20'] = tsla['close'].rolling(20).mean()

test = tsla[(tsla['date'] >= '2023-01-01') & (tsla['date'] <= '2024-12-31')]
validate = tsla[(tsla['date'] >= '2025-01-01') & (tsla['date'] <= '2026-02-20')]

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
    results_summary.append(('H059', 'TSLA Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# Test META Trend
print('\n' + '='*90)
print('H060: META Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'META' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
meta = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
meta['date'] = pd.to_datetime(meta['date'])
meta['sma20'] = meta['close'].rolling(20).mean()

test = meta[(meta['date'] >= '2023-01-01') & (meta['date'] <= '2024-12-31')]
validate = meta[(meta['date'] >= '2025-01-01') & (meta['date'] <= '2026-02-20')]

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
    results_summary.append(('H060', 'META Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
