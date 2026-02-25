#!/usr/bin/env python3
"""
ACADEMIC-BASED HYPOTHESES: Drawing from established quant research
H146-H160: Based on Jegadeesh & Titman, Fama-French, Calendar Effects
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

# H146: 52-Week High Effect (George & Hwang, 2004)
print('='*90)
print('H146: 52-Week High Effect (Momentum via price levels)')
print('Academic basis: George & Hwang (2004) - 52-week high as anchor')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['high_52w'] = qqq['close'].rolling(252).max()

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_52w_high(period_df):
    trades = []
    for i in range(252, len(period_df) - 10):
        # Price within 5% of 52-week high = momentum
        if period_df['close'].iloc[i] > period_df['high_52w'].iloc[i] * 0.95:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_52w_high(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_52w_high(test)
v_res = test_52w_high(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H146', 'QQQ 52W High', t_res['win_rate'], v_res['win_rate']))

# H147: Turn-of-Month Effect (Ariel, 1987)
print('\n' + '='*90)
print('H147: Turn-of-Month Effect (Days -1 to +3 of month)')
print('Academic basis: Ariel (1987) - Returns cluster at month end')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['day'] = spy['date'].dt.day
spy['rsi'] = rsi(spy['close'])

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_turn_month(period_df):
    trades = []
    for i in range(14, len(period_df) - 3):
        # Last day of month OR first 3 days of month
        day = period_df['day'].iloc[i]
        is_turn = (day >= 28) or (day <= 3)
        if is_turn and pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 40:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_turn_month(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_turn_month(test)
v_res = test_turn_month(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H147', 'SPY Turn-of-Month', t_res['win_rate'], v_res['win_rate']))

# H148: Monday Effect (Weekend effect)
print('\n' + '='*90)
print('H148: Monday Mean Reversion (Weekend effect)')
print('Academic basis: French (1980) - Monday returns lower')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq2['date'] = pd.to_datetime(qqq2['date'])
qqq2['weekday'] = qqq2['date'].dt.weekday  # 0=Monday
qqq2['rsi'] = rsi(qqq2['close'])

test = qqq2[(qqq2['date'] >= '2023-01-01') & (qqq2['date'] <= '2024-12-31')]
validate = qqq2[(qqq2['date'] >= '2025-01-01') & (qqq2['date'] <= '2026-02-20')]

def test_monday(period_df):
    trades = []
    for i in range(14, len(period_df) - 5):
        # Monday + Oversold = buy
        if period_df['weekday'].iloc[i] == 0 and pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 35:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_monday(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_monday(test)
v_res = test_monday(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H148', 'QQQ Monday MR', t_res['win_rate'], v_res['win_rate']))

# H149: Low Volatility Anomaly (Ang et al.)
print('\n' + '='*90)
print('H149: Low Volatility Anomaly (Low vol stocks outperform)')
print('Academic basis: Ang et al. (2006) - Low volatility anomaly')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'XLP' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlp = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlp['date'] = pd.to_datetime(xlp['date'])
xlp['ret'] = xlp['close'].pct_change()
xlp['volatility'] = xlp['ret'].rolling(20).std() * np.sqrt(252)  # Annualized vol

test = xlp[(xlp['date'] >= '2023-01-01') & (xlp['date'] <= '2024-12-31')]
validate = xlp[(xlp['date'] >= '2025-01-01') & (xlp['date'] <= '2026-02-20')]

def test_low_vol(period_df):
    trades = []
    for i in range(20, len(period_df) - 10):
        # Buy when volatility is low (bottom 30%)
        vol_pctile = period_df['volatility'].iloc[i-20:i].quantile(0.3)
        if pd.notna(period_df['volatility'].iloc[i]) and period_df['volatility'].iloc[i] < vol_pctile:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_low_vol(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_low_vol(test)
v_res = test_low_vol(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H149', 'XLP Low Vol', t_res['win_rate'], v_res['win_rate']))

# H150: VWAP Deviation (Mean reversion to VWAP)
print('\n' + '='*90)
print('H150: VWAP Deviation (Price far below VWAP = buy)')
print('Academic basis: Market microstructure - VWAP as fair value')
print('='*90)

cursor.execute('''SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy2 = pd.DataFrame(cursor.fetchall(), columns=['date', 'close', 'volume'])
spy2['date'] = pd.to_datetime(spy2['date'])
spy2['vwap'] = (spy2['close'] * spy2['volume']).rolling(20).sum() / spy2['volume'].rolling(20).sum()
spy2['deviation'] = (spy2['close'] - spy2['vwap']) / spy2['vwap'] * 100

test = spy2[(spy2['date'] >= '2023-01-01') & (spy2['date'] <= '2024-12-31')]
validate = spy2[(spy2['date'] >= '2025-01-01') & (spy2['date'] <= '2026-02-20')]

def test_vwap(period_df):
    trades = []
    for i in range(20, len(period_df) - 3):
        # Price > 1% below VWAP = buy
        if pd.notna(period_df['deviation'].iloc[i]) and period_df['deviation'].iloc[i] < -1.0:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_vwap(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_vwap(test)
v_res = test_vwap(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H150', 'SPY VWAP Dev', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('ACADEMIC-BASED STRATEGIES - NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
