#!/usr/bin/env python3
"""
MORE RIGOROUS 3-TIER TESTING: H175-H185
Full validation on remaining candidate strategies
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
    decay_test = test_wr - train_wr
    decay_val = val_wr - test_wr
    
    if train_wr >= 55 and test_wr >= 60 and val_wr >= 55 and abs(decay_val) < 20:
        return '🏆 TRUE GOLDEN'
    elif test_wr >= 60 and val_wr >= 55:
        return '✅ VALIDATED'
    elif test_wr >= 55 and val_wr >= 50:
        return '🟡 BORDERLINE'
    else:
        return '❌ FAILED'

results_summary = []

# H175: AMD RSI < 30
print('='*90)
print('H175: AMD RSI < 30 (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AMD' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
amd = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
amd['date'] = pd.to_datetime(amd['date'])
amd['rsi'] = rsi(amd['close'])

def entry_rsi30(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30

res = test_strategy(amd, entry_rsi30, 5)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H175', 'AMD RSI<30', verdict, train_wr, test_wr, val_wr))

# H176: XLK RSI < 30
print('\n' + '='*90)
print('H176: XLK RSI < 30 (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk['rsi'] = rsi(xlk['close'])

res = test_strategy(xlk, entry_rsi30, 10)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H176', 'XLK RSI<30', verdict, train_wr, test_wr, val_wr))

# H177: XLE RSI < 30
print('\n' + '='*90)
print('H177: XLE RSI < 30 (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLE' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xle = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xle['date'] = pd.to_datetime(xle['date'])
xle['rsi'] = rsi(xle['close'])

res = test_strategy(xle, entry_rsi30, 5)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H177', 'XLE RSI<30', verdict, train_wr, test_wr, val_wr))

# H178: GOOGL Trend Following
print('\n' + '='*90)
print('H178: GOOGL Trend Following (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'GOOGL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
googl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
googl['date'] = pd.to_datetime(googl['date'])
googl['sma20'] = googl['close'].rolling(20).mean()

def entry_trend(df, i):
    return pd.notna(df['sma20'].iloc[i]) and df['close'].iloc[i] > df['sma20'].iloc[i]

res = test_strategy(googl, entry_trend, 10)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H178', 'GOOGL Trend', verdict, train_wr, test_wr, val_wr))

# H179: AAPL Trend Following
print('\n' + '='*90)
print('H179: AAPL Trend Following (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
aapl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
aapl['date'] = pd.to_datetime(aapl['date'])
aapl['sma50'] = aapl['close'].rolling(50).mean()

def entry_trend50(df, i):
    return pd.notna(df['sma50'].iloc[i]) and df['close'].iloc[i] > df['sma50'].iloc[i]

res = test_strategy(aapl, entry_trend50, 10)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H179', 'AAPL Trend', verdict, train_wr, test_wr, val_wr))

# H180: XLU Defensive Flight
print('\n' + '='*90)
print('H180: XLU Defensive Flight (3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLU' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlu = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlu['date'] = pd.to_datetime(xlu['date'])
xlu['sma20'] = xlu['close'].rolling(20).mean()

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['sma50'] = spy['close'].rolling(50).mean()
spy.columns = ['date', 'spy', 'spy_sma50']

df = pd.merge(xlu, spy, on='date')
df['close'] = df['XLU'] = df['close']

def entry_defensive(df, i):
    return (pd.notna(df['spy_sma50'].iloc[i]) and
            df['spy'].iloc[i] < df['spy_sma50'].iloc[i] and  # SPY weak
            pd.notna(df['sma20'].iloc[i]) and
            df['XLU'].iloc[i] > df['sma20'].iloc[i])  # XLU strong

res = test_strategy(df, entry_defensive, 5)
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']

print(f"Train: {res['Train']['trades']} trades, {train_wr:.1f}%")
print(f"Test: {res['Test']['trades']} trades, {test_wr:.1f}%")
print(f"Validate: {res['Validate']['trades']} trades, {val_wr:.1f}%")
verdict = classify(train_wr, test_wr, val_wr)
print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H180', 'XLU Defensive', verdict, train_wr, test_wr, val_wr))

print('\n' + '='*90)
print('COMPLETE 3-TIER VALIDATION SUMMARY')
print('='*90)
print(f"{'ID':<6} {'Strategy':<20} {'Verdict':<15} {'Train':<8} {'Test':<8} {'Val':<8}")
print('-'*90)
for r in results_summary:
    print(f"{r[0]:<6} {r[1]:<20} {r[2]:<15} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}%")

conn.close()
