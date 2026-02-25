#!/usr/bin/env python3
"""
MORE ACADEMIC HYPOTHESES: H151-H165
Post-Earnings Drift, Momentum, Seasonality
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

# H151: Golden Cross (SMA50 crosses above SMA200)
print('='*90)
print('H151: Golden Cross (SMA50 > SMA200)')
print('Academic basis: Technical analysis - golden cross as bullish signal')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['sma50'] = qqq['close'].rolling(50).mean()
qqq['sma200'] = qqq['close'].rolling(200).mean()

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_golden(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['sma50'].iloc[i]) and pd.notna(period_df['sma200'].iloc[i]) and
            period_df['sma50'].iloc[i] > period_df['sma200'].iloc[i] and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_golden(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_golden(test)
v_res = test_golden(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H151', 'QQQ Golden Cross', t_res['win_rate'], v_res['win_rate']))

# H152: RSI Divergence (Bullish)
print('\n' + '='*90)
print('H152: Bullish RSI Divergence (Price lower, RSI higher)')
print('Academic basis: Technical analysis - divergence signals trend change')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'NVDA' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
nvda = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
nvda['date'] = pd.to_datetime(nvda['date'])
nvda['rsi'] = rsi(nvda['close'])

test = nvda[(nvda['date'] >= '2023-01-01') & (nvda['date'] <= '2024-12-31')]
validate = nvda[(nvda['date'] >= '2025-01-01') & (nvda['date'] <= '2026-02-20')]

def test_divergence(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        # Price making lower lows, RSI making higher lows
        if (period_df['close'].iloc[i] < period_df['close'].iloc[i-10] and
            pd.notna(period_df['rsi'].iloc[i]) and
            pd.notna(period_df['rsi'].iloc[i-10]) and
            period_df['rsi'].iloc[i] > period_df['rsi'].iloc[i-10] + 5 and
            period_df['rsi'].iloc[i] < 40):  # Oversold area
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_divergence(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_divergence(test)
v_res = test_divergence(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H152', 'NVDA RSI Divergence', t_res['win_rate'], v_res['win_rate']))

# H153: Bollinger Band Squeeze
print('\n' + '='*90)
print('H153: Bollinger Band Squeeze + Breakout')
print('Academic basis: Volatility compression precedes expansion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['sma20'] = spy['close'].rolling(20).mean()
spy['std20'] = spy['close'].rolling(20).std()
spy['bb_width'] = spy['std20'] / spy['sma20'] * 100

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_bb_squeeze(period_df):
    trades = []
    for i in range(20, len(period_df) - 5):
        # BB width in bottom 20% of last 60 days = squeeze
        if i >= 60:
            width_pctile = period_df['bb_width'].iloc[i-60:i].quantile(0.2)
            if (pd.notna(period_df['bb_width'].iloc[i]) and 
                period_df['bb_width'].iloc[i] < width_pctile and
                period_df['close'].iloc[i] > period_df['sma20'].iloc[i]):  # Breakout up
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + 5]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
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
    if verdict == '✅ VALIDATED':
        results_summary.append(('H153', 'SPY BB Squeeze', t_res['win_rate'], v_res['win_rate']))

# H154: Rate of Change (ROC) Momentum
print('\n' + '='*90)
print('H154: Rate of Change Momentum (10-day ROC > 5%)')
print('Academic basis: Price momentum persists')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk['roc'] = (xlk['close'] / xlk['close'].shift(10) - 1) * 100

test = xlk[(xlk['date'] >= '2023-01-01') & (xlk['date'] <= '2024-12-31')]
validate = xlk[(xlk['date'] >= '2025-01-01') & (xlk['date'] <= '2026-02-20')]

def test_roc(period_df):
    trades = []
    for i in range(10, len(period_df) - 5):
        if pd.notna(period_df['roc'].iloc[i]) and period_df['roc'].iloc[i] > 5:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_roc(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_roc(test)
v_res = test_roc(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H154', 'XLK ROC Momentum', t_res['win_rate'], v_res['win_rate']))

# H155: Dual Momentum (Absolute + Relative)
print('\n' + '='*90)
print('H155: Dual Momentum (QQQ > SMA200 + QQQ > SPY)')
print('Academic basis: Gary Antonacci dual momentum strategy')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq2['date'] = pd.to_datetime(qqq2['date'])
qqq2.columns = ['date', 'qqq']

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy2['date'] = pd.to_datetime(spy2['date'])
spy2.columns = ['date', 'spy']

df = pd.merge(qqq2, spy2, on='date')
df['qqq_sma200'] = df['qqq'].rolling(200).mean()
df['qqq_ret'] = df['qqq'].pct_change(63)  # 3-month return
df['spy_ret'] = df['spy'].pct_change(63)

test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_dual(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['qqq_sma200'].iloc[i]) and
            period_df['qqq'].iloc[i] > period_df['qqq_sma200'].iloc[i] and  # Absolute momentum
            pd.notna(period_df['qqq_ret'].iloc[i]) and
            pd.notna(period_df['spy_ret'].iloc[i]) and
            period_df['qqq_ret'].iloc[i] > period_df['spy_ret'].iloc[i]):  # Relative momentum
            entry = period_df['qqq'].iloc[i]
            exit_p = period_df['qqq'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_dual(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_dual(test)
v_res = test_dual(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H155', 'QQQ Dual Momentum', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED FROM ACADEMIC RESEARCH')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
