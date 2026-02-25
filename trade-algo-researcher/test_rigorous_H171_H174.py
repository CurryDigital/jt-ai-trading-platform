#!/usr/bin/env python3
"""
RIGOROUS 3-TIER VALIDATION: H171-H180
Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-Feb 2026
No shortcuts, full period analysis
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
    """Test strategy with 3-tier validation"""
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
                ret = (exit_p - entry) / entry * 100 - 0.1  # Include transaction cost
                trades.append(ret)
        
        if len(trades) >= 5:
            r = pd.Series(trades)
            win_rate = (r > 0).mean() * 100
            results[period_name] = {
                'trades': len(trades),
                'win_rate': win_rate,
                'avg_return': r.mean(),
                'sharpe': r.mean() / r.std() * np.sqrt(252/exit_days) if r.std() > 0 else 0
            }
        else:
            results[period_name] = {'trades': 0, 'win_rate': 0, 'avg_return': 0, 'sharpe': 0}
    
    return results

results_summary = []

# H171: QQQ RSI < 30 with FULL 3-tier
print('='*90)
print('H171: QQQ RSI < 30 Mean Reversion (FULL 3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['rsi'] = rsi(qqq['close'])

def entry_rsi30(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30

res = test_strategy(qqq, entry_rsi30, 10)  # 10D hold

print(f"Train (2021-22):  {res['Train']['trades']} trades, {res['Train']['win_rate']:.1f}% win, Sharpe: {res['Train']['sharpe']:.2f}")
print(f"Test (2023-24):   {res['Test']['trades']} trades, {res['Test']['win_rate']:.1f}% win, Sharpe: {res['Test']['sharpe']:.2f}")
print(f"Validate (2025+): {res['Validate']['trades']} trades, {res['Validate']['win_rate']:.1f}% win, Sharpe: {res['Validate']['sharpe']:.2f}")

# Classification
train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']
decay_test = test_wr - train_wr
decay_val = val_wr - test_wr

print(f"\nDecay Train→Test: {decay_test:+.1f}%")
print(f"Decay Test→Validate: {decay_val:+.1f}%")

if train_wr >= 55 and test_wr >= 60 and val_wr >= 55 and abs(decay_val) < 20:
    verdict = '🏆 TRUE GOLDEN'
elif test_wr >= 60 and val_wr >= 55:
    verdict = '✅ VALIDATED'
elif test_wr >= 55 and val_wr >= 50:
    verdict = '🟡 BORDERLINE'
else:
    verdict = '❌ FAILED'

print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H171', 'QQQ RSI<30 10D', verdict, train_wr, test_wr, val_wr))

# H172: SPY RSI < 30 with FULL 3-tier
print('\n' + '='*90)
print('H172: SPY RSI < 30 Mean Reversion (FULL 3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['rsi'] = rsi(spy['close'])

res = test_strategy(spy, entry_rsi30, 10)

print(f"Train (2021-22):  {res['Train']['trades']} trades, {res['Train']['win_rate']:.1f}% win")
print(f"Test (2023-24):   {res['Test']['trades']} trades, {res['Test']['win_rate']:.1f}% win")
print(f"Validate (2025+): {res['Validate']['trades']} trades, {res['Validate']['win_rate']:.1f}% win")

train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']
decay_test = test_wr - train_wr
decay_val = val_wr - test_wr

print(f"\nDecay Train→Test: {decay_test:+.1f}%")
print(f"Decay Test→Validate: {decay_val:+.1f}%")

if train_wr >= 55 and test_wr >= 60 and val_wr >= 55 and abs(decay_val) < 20:
    verdict = '🏆 TRUE GOLDEN'
elif test_wr >= 60 and val_wr >= 55:
    verdict = '✅ VALIDATED'
elif test_wr >= 55 and val_wr >= 50:
    verdict = '🟡 BORDERLINE'
else:
    verdict = '❌ FAILED'

print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H172', 'SPY RSI<30 10D', verdict, train_wr, test_wr, val_wr))

# H173: NVDA RSI < 35 with FULL 3-tier
print('\n' + '='*90)
print('H173: NVDA RSI < 35 Mean Reversion (FULL 3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['rsi'] = rsi(nvda['close'])

def entry_rsi35(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 35

res = test_strategy(nvda, entry_rsi35, 5)

print(f"Train (2021-22):  {res['Train']['trades']} trades, {res['Train']['win_rate']:.1f}% win")
print(f"Test (2023-24):   {res['Test']['trades']} trades, {res['Test']['win_rate']:.1f}% win")
print(f"Validate (2025+): {res['Validate']['trades']} trades, {res['Validate']['win_rate']:.1f}% win")

train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']
decay_test = test_wr - train_wr
decay_val = val_wr - test_wr

print(f"\nDecay Train→Test: {decay_test:+.1f}%")
print(f"Decay Test→Validate: {decay_val:+.1f}%")

if train_wr >= 55 and test_wr >= 60 and val_wr >= 55 and abs(decay_val) < 20:
    verdict = '🏆 TRUE GOLDEN'
elif test_wr >= 60 and val_wr >= 55:
    verdict = '✅ VALIDATED'
elif test_wr >= 55 and val_wr >= 50:
    verdict = '🟡 BORDERLINE'
else:
    verdict = '❌ FAILED'

print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H173', 'NVDA RSI<35 5D', verdict, train_wr, test_wr, val_wr))

# H174: XLK/XLF Sector Rotation with FULL 3-tier
print('\n' + '='*90)
print('H174: XLK/XLF Sector Rotation (FULL 3-TIER VALIDATION)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk.columns = ['date', 'xlk']

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlf = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlf['date'] = pd.to_datetime(xlf['date'])
xlf.columns = ['date', 'xlf']

df = pd.merge(xlk, xlf, on='date')
df['ratio'] = df['xlk'] / df['xlf']
df['ratio_sma20'] = df['ratio'].rolling(20).mean()
df['close'] = df['xlk']  # For compatibility

def entry_rotation(df, i):
    return pd.notna(df['ratio_sma20'].iloc[i]) and df['ratio'].iloc[i] > df['ratio_sma20'].iloc[i]

res = test_strategy(df, entry_rotation, 10)

print(f"Train (2021-22):  {res['Train']['trades']} trades, {res['Train']['win_rate']:.1f}% win")
print(f"Test (2023-24):   {res['Test']['trades']} trades, {res['Test']['win_rate']:.1f}% win")
print(f"Validate (2025+): {res['Validate']['trades']} trades, {res['Validate']['win_rate']:.1f}% win")

train_wr = res['Train']['win_rate']
test_wr = res['Test']['win_rate']
val_wr = res['Validate']['win_rate']
decay_test = test_wr - train_wr
decay_val = val_wr - test_wr

print(f"\nDecay Train→Test: {decay_test:+.1f}%")
print(f"Decay Test→Validate: {decay_val:+.1f}%")

if train_wr >= 55 and test_wr >= 60 and val_wr >= 55 and abs(decay_val) < 20:
    verdict = '🏆 TRUE GOLDEN'
elif test_wr >= 60 and val_wr >= 55:
    verdict = '✅ VALIDATED'
elif test_wr >= 55 and val_wr >= 50:
    verdict = '🟡 BORDERLINE'
else:
    verdict = '❌ FAILED'

print(f"Verdict: {verdict}")
if verdict in ['🏆 TRUE GOLDEN', '✅ VALIDATED']:
    results_summary.append(('H174', 'XLK/XLF Rotation', verdict, train_wr, test_wr, val_wr))

print('\n' + '='*90)
print('RIGOROUS 3-TIER VALIDATION RESULTS')
print('='*90)
print(f"{'ID':<6} {'Strategy':<20} {'Verdict':<15} {'Train':<8} {'Test':<8} {'Val':<8}")
print('-'*90)
for r in results_summary:
    print(f"{r[0]:<6} {r[1]:<20} {r[2]:<15} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}%")

conn.close()
