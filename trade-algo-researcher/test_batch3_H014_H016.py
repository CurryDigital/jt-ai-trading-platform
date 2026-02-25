#!/usr/bin/env python3
"""
BATCH 3: H014-H016
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
print('H014: IWM Small Cap Momentum')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'IWM' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
iwm = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
iwm['date'] = pd.to_datetime(iwm['date'])
iwm['sma20'] = iwm['close'].rolling(20).mean()
iwm['vol_avg'] = iwm['volume'].rolling(20).mean()
iwm['vol_ratio'] = iwm['volume'] / iwm['vol_avg']

train = iwm[(iwm['date'] >= '2021-01-01') & (iwm['date'] <= '2022-12-31')]
test = iwm[(iwm['date'] >= '2023-01-01') & (iwm['date'] <= '2024-12-31')]
validate = iwm[(iwm['date'] >= '2025-01-01') & (iwm['date'] <= '2026-02-20')]

def test_momentum(period_df):
    trades = []
    for i in range(20, len(period_df) - 10):
        if (pd.notna(period_df['sma20'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.2):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_momentum(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_momentum(test)
v_res = test_momentum(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H014', 'IWM Momentum', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H015: MSFT Trend + Volume')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'MSFT' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
msft = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
msft['date'] = pd.to_datetime(msft['date'])
msft['sma50'] = msft['close'].rolling(50).mean()
msft['vol_avg'] = msft['volume'].rolling(20).mean()
msft['vol_ratio'] = msft['volume'] / msft['vol_avg']

train = msft[(msft['date'] >= '2021-01-01') & (msft['date'] <= '2022-12-31')]
test = msft[(msft['date'] >= '2023-01-01') & (msft['date'] <= '2024-12-31')]
validate = msft[(msft['date'] >= '2025-01-01') & (msft['date'] <= '2026-02-20')]

def test_msft(period_df):
    trades = []
    for i in range(50, len(period_df) - 10):
        if (pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i] and
            pd.notna(period_df['vol_ratio'].iloc[i]) and
            period_df['vol_ratio'].iloc[i] > 1.3):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_msft(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_msft(test)
v_res = test_msft(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H015', 'MSFT Trend+Vol', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H016: Tech vs Financials Rotation (XLK/XLF)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlf = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlf['date'] = pd.to_datetime(xlf['date'])

merged = pd.merge(xlk, xlf, on='date', suffixes=('_xlk', '_xlf'))
merged['ratio'] = merged['close_xlk'] / merged['close_xlf']
merged['ratio_sma20'] = merged['ratio'].rolling(20).mean()

train = merged[(merged['date'] >= '2021-01-01') & (merged['date'] <= '2022-12-31')]
test = merged[(merged['date'] >= '2023-01-01') & (merged['date'] <= '2024-12-31')]
validate = merged[(merged['date'] >= '2025-01-01') & (merged['date'] <= '2026-02-20')]

def test_rotation(period_df):
    trades = []
    for i in range(20, len(period_df) - 10):
        if pd.notna(period_df['ratio_sma20'].iloc[i]) and period_df['ratio'].iloc[i] > period_df['ratio_sma20'].iloc[i]:
            entry = period_df['close_xlk'].iloc[i]
            exit_p = period_df['close_xlk'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_rotation(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_rotation(test)
v_res = test_rotation(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H016', 'XLK/XLF Rotation', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BATCH 3 SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
