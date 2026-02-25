#!/usr/bin/env python3
"""
MORE COMBINATIONS: H161-H175
Relaxed filters for more signals
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

# H161: RSI < 40 (Relaxed) + Above SMA50
print('='*90)
print('H161: RSI < 40 + Above SMA50 (QQQ)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['rsi'] = rsi(qqq['close'])
qqq['sma50'] = qqq['close'].rolling(50).mean()

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_relaxed(period_df):
    trades = []
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] < 40 and  # Relaxed from 30
            pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_relaxed(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_relaxed(test)
v_res = test_relaxed(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    if verdict == '✅ VALIDATED':
        results_summary.append(('H161', 'QQQ RSI40+SMA50', t_res['win_rate'], v_res['win_rate']))

# Test on multiple tickers with RSI < 35
print('\n' + '='*90)
print('H162-H166: RSI < 35 on Multiple Stocks')
print('='*90)

stocks = [('AAPL', 'H162'), ('MSFT', 'H163'), ('GOOGL', 'H164'), ('META', 'H165'), ('TSLA', 'H166')]

for ticker, hid in stocks:
    print(f'\n--- {hid}: {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    def test_rsi35(period_df):
        trades = []
        for i in range(14, len(period_df) - 5):
            if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 35:
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + 5]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        if len(trades) < 10:
            return None
        r = pd.Series(trades)
        return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
    
    t_res = test_rsi35(test)
    v_res = test_rsi35(validate)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}%")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}%")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
            results_summary.append((hid, f'{ticker} RSI<35', t_res['win_rate'], v_res['win_rate']))

# H167-H170: Different hold periods on SPY
print('\n' + '='*90)
print('H167-H170: SPY RSI<30 Different Hold Periods')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['rsi'] = rsi(spy['close'])

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

hold_periods = [(3, 'H167'), (7, 'H168'), (10, 'H169'), (15, 'H170')]

for hold, hid in hold_periods:
    print(f'\n--- {hid}: SPY RSI<30 {hold}D hold ---')
    
    def test_hold(period_df, h):
        trades = []
        for i in range(14, len(period_df) - h):
            if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 30:
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + h]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        if len(trades) < 10:
            return None
        r = pd.Series(trades)
        return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
    
    t_res = test_hold(test, hold)
    v_res = test_hold(validate, hold)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}%")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}%")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
            results_summary.append((hid, f'SPY RSI<30 {hold}D', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED STRATEGIES')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
