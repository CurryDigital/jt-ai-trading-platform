#!/usr/bin/env python3
"""
COMPREHENSIVE BATCH: H131-H150
More tickers, thresholds, and combinations
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

# Test IWM (Russell 2000) - small caps
print('='*90)
print('H131: IWM (Small Cap) RSI < 30')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'IWM' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
iwm = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
iwm['date'] = pd.to_datetime(iwm['date'])
iwm['rsi'] = rsi(iwm['close'])

test = iwm[(iwm['date'] >= '2023-01-01') & (iwm['date'] <= '2024-12-31')]
validate = iwm[(iwm['date'] >= '2025-01-01') & (iwm['date'] <= '2026-02-20')]

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
    if verdict == '✅ VALIDATED':
        results_summary.append(('H131', 'IWM RSI<30', t_res['win_rate'], v_res['win_rate']))

# Test VIX proxy (not actual VIX, but using SPY RSI as fear gauge)
print('\n' + '='*90)
print('H132: SPY RSI < 20 (Extreme Fear)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['rsi'] = rsi(spy['close'])

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_rsi20(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 20:  # Extreme
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 5:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_rsi20(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi20(test)
v_res = test_rsi20(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H132', 'SPY RSI<20', t_res['win_rate'], v_res['win_rate']))

# Test XLK with 10D hold
print('\n' + '='*90)
print('H133: XLK RSI < 30 (10D Hold)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk['rsi'] = rsi(xlk['close'])

test = xlk[(xlk['date'] >= '2023-01-01') & (xlk['date'] <= '2024-12-31')]
validate = xlk[(xlk['date'] >= '2025-01-01') & (xlk['date'] <= '2026-02-20')]

def test_rsi_10d(period_df):
    trades = []
    for i in range(14, len(period_df) - 10):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_rsi_10d(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi_10d(test)
v_res = test_rsi_10d(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H133', 'XLK RSI<30 10D', t_res['win_rate'], v_res['win_rate']))

# Test GOOGL with volume filter
print('\n' + '='*90)
print('H134: GOOGL RSI < 30 + Volume > 1.2x')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
googl['date'] = pd.to_datetime(googl['date'])
googl['rsi'] = rsi(googl['close'])
googl['vol_avg'] = googl['volume'].rolling(20).mean()
googl['vol_ratio'] = googl['volume'] / googl['vol_avg']

test = googl[(googl['date'] >= '2023-01-01') & (googl['date'] <= '2024-12-31')]
validate = googl[(googl['date'] >= '2025-01-01') & (googl['date'] <= '2026-02-20')]

def test_rsi_vol(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 30 and
            pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.2):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 5:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_rsi_vol(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rsi_vol(test)
v_res = test_rsi_vol(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H134', 'GOOGL RSI+Vol', t_res['win_rate'], v_res['win_rate']))

# Test NVDA trend following
print('\n' + '='*90)
print('H135: NVDA Trend (Price > SMA20)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['sma20'] = nvda['close'].rolling(20).mean()

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_trend(period_df):
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
    if verdict == '✅ VALIDATED':
        results_summary.append(('H135', 'NVDA Trend', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED STRATEGIES')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
