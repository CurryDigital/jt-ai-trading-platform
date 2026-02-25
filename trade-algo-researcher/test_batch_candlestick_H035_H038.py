#!/usr/bin/env python3
"""
NEW BATCH: Candlesticks, MACD, RSI Combinations
H035-H040
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
print('H035: SPY Bullish Engulfing Candlestick')
print('='*90)

cursor.execute('''SELECT date, open::float, high::float, low::float, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'high', 'low', 'close'])
spy['date'] = pd.to_datetime(spy['date'])

def test_engulfing(period_df):
    trades = []
    for i in range(1, len(period_df) - 5):
        prev = period_df.iloc[i-1]
        curr = period_df.iloc[i]
        # Bullish engulfing: prev red, curr green, curr body engulfs prev body
        prev_red = prev['close'] < prev['open']
        curr_green = curr['close'] > curr['open']
        engulfs = (curr['close'] > prev['open']) and (curr['open'] < prev['close'])
        if prev_red and curr_green and engulfs:
            entry = curr['close']
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
    res = test_engulfing(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_engulfing(test)
v_res = test_engulfing(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H035', 'SPY Bullish Engulfing', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H036: QQQ MACD Golden Cross')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])

# Calculate MACD
exp1 = qqq['close'].ewm(span=12).mean()
exp2 = qqq['close'].ewm(span=26).mean()
qqq['macd'] = exp1 - exp2
qqq['signal'] = qqq['macd'].ewm(span=9).mean()

def test_macd(period_df):
    trades = []
    for i in range(26, len(period_df) - 5):
        if (period_df['macd'].iloc[i-1] < period_df['signal'].iloc[i-1] and
            period_df['macd'].iloc[i] > period_df['signal'].iloc[i]):  # Golden cross
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = qqq[(qqq['date'] >= '2021-01-01') & (qqq['date'] <= '2022-12-31')]
test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_macd(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_macd(test)
v_res = test_macd(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H036', 'QQQ MACD Golden Cross', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H037: NVDA RSI + MACD Combo')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])

# RSI
delta = nvda['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
nvda['rsi'] = 100 - (100 / (1 + gain/loss))

# MACD
exp1 = nvda['close'].ewm(span=12).mean()
exp2 = nvda['close'].ewm(span=26).mean()
nvda['macd'] = exp1 - exp2
nvda['signal'] = nvda['macd'].ewm(span=9).mean()

def test_combo(period_df):
    trades = []
    for i in range(26, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 40 and
            period_df['macd'].iloc[i] > period_df['signal'].iloc[i]):  # RSI oversold + MACD bullish
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = nvda[(nvda['date'] >= '2021-01-01') & (nvda['date'] <= '2022-12-31')]
test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
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
    results_summary.append(('H037', 'NVDA RSI+MACD Combo', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('H038: AAPL Bollinger Band Squeeze')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
aapl = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
aapl['date'] = pd.to_datetime(aapl['date'])
aapl['sma20'] = aapl['close'].rolling(20).mean()
aapl['std20'] = aapl['close'].rolling(20).std()
aapl['bb_width'] = (aapl['std20'] / aapl['sma20']) * 100
aapl['bb_width_pctile'] = aapl['bb_width'].rolling(120).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) >= 120 else np.nan, raw=False)

def test_bb_squeeze(period_df):
    trades = []
    for i in range(120, len(period_df) - 5):
        if pd.notna(period_df['bb_width_pctile'].iloc[i]) and period_df['bb_width_pctile'].iloc[i] < 0.10:  # Bottom 10% width
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train = aapl[(aapl['date'] >= '2021-01-01') & (aapl['date'] <= '2022-12-31')]
test = aapl[(aapl['date'] >= '2023-01-01') & (aapl['date'] <= '2024-12-31')]
validate = aapl[(aapl['date'] >= '2025-01-01') & (aapl['date'] <= '2026-02-20')]

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_bb_squeeze(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bb_squeeze(test)
v_res = test_bb_squeeze(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H038', 'AAPL BB Squeeze', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('SUMMARY BATCH')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
