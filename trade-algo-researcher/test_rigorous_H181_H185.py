#!/usr/bin/env python3
"""
FINAL RIGOROUS BATCH: H181-H190
Testing remaining candidate strategies with full 3-tier
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

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_strategy(df, entry_func, exit_days=5):
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
            win_rate = (r > 0).mean() * 100
            results[period_name] = {'trades': len(trades), 'win_rate': win_rate}
        else:
            results[period_name] = {'trades': 0, 'win_rate': 0}
    
    return results

def classify(train_wr, test_wr, val_wr):
    if train_wr >= 55 and test_wr >= 60 and val_wr >= 55:
        return '🏆 TRUE GOLDEN'
    elif test_wr >= 60 and val_wr >= 55:
        return '✅ VALIDATED'
    elif test_wr >= 55 and val_wr >= 50:
        return '🟡 BORDERLINE'
    else:
        return '❌ FAILED'

results_summary = []

# H181: QQQ Trend Following
print('='*90)
print('H181: QQQ Trend Following (Price > SMA50)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['sma50'] = qqq['close'].rolling(50).mean()

def entry_trend50(df, i):
    return pd.notna(df['sma50'].iloc[i]) and df['close'].iloc[i] > df['sma50'].iloc[i]

res = test_strategy(qqq, entry_trend50, 10)
train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H181', 'QQQ Trend', verdict, train_wr, test_wr, val_wr))

# H182: XLP RSI < 30
print('\n' + '='*90)
print('H182: XLP RSI < 30')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLP' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlp = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlp['date'] = pd.to_datetime(xlp['date'])
xlp['rsi'] = rsi(xlp['close'])

def entry_rsi30(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30

res = test_strategy(xlp, entry_rsi30, 5)
train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H182', 'XLP RSI<30', verdict, train_wr, test_wr, val_wr))

# H183: 0700.HK (Tencent) RSI < 25
print('\n' + '='*90)
print('H183: 0700.HK (Tencent) RSI < 25')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '0700.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
hk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
hk['date'] = pd.to_datetime(hk['date'])
hk['rsi'] = rsi(hk['close'])

def entry_rsi25(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 25

res = test_strategy(hk, entry_rsi25, 5)
train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H183', '0700.HK RSI<25', verdict, train_wr, test_wr, val_wr))

# H184: NVDA 20D High Breakout
print('\n' + '='*90)
print('H184: NVDA 20-Day High Breakout')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['high20'] = nvda['close'].rolling(20).max()

def entry_high20(df, i):
    return df['close'].iloc[i] > df['high20'].iloc[i-1]

res = test_strategy(nvda, entry_high20, 5)
train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H184', 'NVDA 20D High', verdict, train_wr, test_wr, val_wr))

# H185: China 000333.SZ RSI < 30
print('\n' + '='*90)
print('H185: China 000333.SZ (Midea) RSI < 30')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '000333.SZ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
cn = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
cn['date'] = pd.to_datetime(cn['date'])
cn['rsi'] = rsi(cn['close'])

res = test_strategy(cn, entry_rsi30, 5)
train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H185', '000333.SZ RSI<30', verdict, train_wr, test_wr, val_wr))

print('\n' + '='*90)
print('FINAL 3-TIER VALIDATION RESULTS')
print('='*90)
print(f"{'ID':<6} {'Strategy':<25} {'Verdict':<15} {'Train':<8} {'Test':<8} {'Val':<8}")
print('-'*90)
for r in results_summary:
    print(f"{r[0]:<6} {r[1]:<25} {r[2]:<15} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}%")

conn.close()
