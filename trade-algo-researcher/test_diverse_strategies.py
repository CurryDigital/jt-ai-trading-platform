#!/usr/bin/env python3
"""
DIVERSE STRATEGY TESTING: S003-S010
Different logic types, full universe (US+HK+CN)
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

def test_3period(df, entry_func, exit_days=5):
    train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    results = {}
    for period_name, period_df in [('Train', train), ('Test', test), ('Validate', validate)]:
        trades = []
        for i in range(50, len(period_df) - exit_days):
            if entry_func(period_df, i):
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + exit_days]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        
        if len(trades) >= 5:
            r = pd.Series(trades)
            results[period_name] = {'win_rate': (r > 0).mean() * 100}
        else:
            results[period_name] = {'win_rate': 0}
    
    return results['Train']['win_rate'], results['Test']['win_rate'], results['Validate']['win_rate']

def classify(train_wr, test_wr, val_wr):
    if train_wr >= 55 and test_wr >= 60 and val_wr >= 55:
        return 'GOLDEN'
    elif test_wr >= 60 and val_wr >= 55:
        return 'VALIDATED'
    elif test_wr >= 55 and val_wr >= 50:
        return 'BORDERLINE'
    else:
        return 'FAILED'

# Universe
us_tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'NVDA']
hk_tickers = ['0700.HK', '9988.HK', '3690.HK', '1810.HK']
cn_tickers = ['000333.SZ', '000858.SZ']
all_tickers = us_tickers + hk_tickers + cn_tickers

results_summary = []

# S003: 3-Day Consecutive Down (Panic Selling)
print('='*90)
print('S003: 3-Day Consecutive Down (Panic Selling Reversal)')
print('='*90)

def entry_3down(df, i):
    return (df['close'].iloc[i] < df['close'].iloc[i-1] and
            df['close'].iloc[i-1] < df['close'].iloc[i-2] and
            df['close'].iloc[i-2] < df['close'].iloc[i-3])

passed = []
for ticker in all_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    
    train_wr, test_wr, val_wr = test_3period(df, entry_3down, 5)
    status = classify(train_wr, test_wr, val_wr)
    print(f"{ticker}: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")
    
    if status in ['GOLDEN', 'VALIDATED']:
        passed.append(ticker)

results_summary.append(('S003', '3-Day Panic Reversal', passed))
print(f"\nWorks on {len(passed)}/{len(all_tickers)} tickers: {passed}")

# S004: Gap Down Recovery
print('\n' + '='*90)
print('S004: Gap Down >2% (Opening Panic Buy)')
print('='*90)

def entry_gap(df, i):
    if i == 0: return False
    gap = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1] * 100
    return gap < -2.0

passed = []
for ticker in all_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    
    train_wr, test_wr, val_wr = test_3period(df, entry_gap, 3)
    status = classify(train_wr, test_wr, val_wr)
    print(f"{ticker}: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")
    
    if status in ['GOLDEN', 'VALIDATED']:
        passed.append(ticker)

results_summary.append(('S004', 'Gap Down Recovery', passed))
print(f"\nWorks on {len(passed)}/{len(all_tickers)} tickers: {passed}")

# S005: High Volume Breakout
print('\n' + '='*90)
print('S005: High Volume Breakout (Volume > 1.5x Avg + Price > SMA20)')
print('='*90)

def entry_vol_breakout(df, i):
    if 'vol_ratio' not in df.columns or 'sma20' not in df.columns:
        return False
    return (pd.notna(df['vol_ratio'].iloc[i]) and df['vol_ratio'].iloc[i] > 1.5 and
            pd.notna(df['sma20'].iloc[i]) and df['close'].iloc[i] > df['sma20'].iloc[i])

passed = []
for ticker in all_tickers:
    cursor.execute(f"SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    train_wr, test_wr, val_wr = test_3period(df, entry_vol_breakout, 5)
    status = classify(train_wr, test_wr, val_wr)
    print(f"{ticker}: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")
    
    if status in ['GOLDEN', 'VALIDATED']:
        passed.append(ticker)

results_summary.append(('S005', 'High Volume Breakout', passed))
print(f"\nWorks on {len(passed)}/{len(all_tickers)} tickers: {passed}")

# S006: Bollinger Band Squeeze
print('\n' + '='*90)
print('S006: Bollinger Band Squeeze (Low Volatility Expansion)')
print('='*90)

def entry_bb_squeeze(df, i):
    if 'bb_width' not in df.columns:
        return False
    if i < 60: return False
    width_pctile = df['bb_width'].iloc[i-60:i].quantile(0.2)
    return pd.notna(df['bb_width'].iloc[i]) and df['bb_width'].iloc[i] < width_pctile

passed = []
for ticker in all_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_width'] = df['std20'] / df['sma20'] * 100
    
    train_wr, test_wr, val_wr = test_3period(df, entry_bb_squeeze, 5)
    status = classify(train_wr, test_wr, val_wr)
    print(f"{ticker}: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")
    
    if status in ['GOLDEN', 'VALIDATED']:
        passed.append(ticker)

results_summary.append(('S006', 'BB Squeeze', passed))
print(f"\nWorks on {len(passed)}/{len(all_tickers)} tickers: {passed}")

# S007: Sector Rotation - Tech vs Financials
print('\n' + '='*90)
print('S007: Sector Rotation (Tech/Financial Ratio)')
print('='*90)

# Only test on US (need sector ETFs)
cursor.execute("SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
xlk_data = cursor.fetchall()
cursor.execute("SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
xlf_data = cursor.fetchall()

if xlk_data and xlf_data:
    xlk = pd.DataFrame(xlk_data, columns=['date', 'close'])
    xlf = pd.DataFrame(xlf_data, columns=['date', 'close'])
    xlk['date'] = pd.to_datetime(xlk['date'])
    xlf['date'] = pd.to_datetime(xlf['date'])
    
    df = pd.merge(xlk, xlf, on='date', suffixes=('_xlk', '_xlf'))
    df['ratio'] = df['close_xlk'] / df['close_xlf']
    df['ratio_sma20'] = df['ratio'].rolling(20).mean()
    df['close'] = df['close_xlk']
    
    def entry_rotation(df, i):
        return pd.notna(df['ratio_sma20'].iloc[i]) and df['ratio'].iloc[i] > df['ratio_sma20'].iloc[i]
    
    train_wr, test_wr, val_wr = test_3period(df, entry_rotation, 10)
    status = classify(train_wr, test_wr, val_wr)
    print(f"XLK/XLF: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")
    
    if status in ['GOLDEN', 'VALIDATED']:
        results_summary.append(('S007', 'Sector Rotation Tech/Fin', ['XLK/XLF']))
    else:
        results_summary.append(('S007', 'Sector Rotation Tech/Fin', []))

# Summary
print('\n' + '='*90)
print('DIVERSE STRATEGY SUMMARY')
print('='*90)
for sid, sname, passed in results_summary:
    status = '✅' if len(passed) > 0 else '❌'
    print(f"{sid}: {sname} - Works on {len(passed)} tickers {status}")

conn.close()

print(f"\nTOTAL UNIQUE STRATEGIES TESTED: 7")
print(f"STRATEGIES WITH PASSING TICKERS: {sum(1 for _, _, p in results_summary if len(p) > 0)}")
