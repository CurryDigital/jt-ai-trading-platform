#!/usr/bin/env python3
"""
BATCH: China A-Shares, Different Timeframes
H111-H120
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

# China A-shares
print('='*90)
print('H111-H115: China A-Shares RSI < 30')
print('='*90)

china_stocks = [('000858.SZ', 'H111'), ('000333.SZ', 'H112'), ('000651.SZ', 'H113'), ('002142.SZ', 'H114'), ('000568.SZ', 'H115')]

for ticker, hid in china_stocks:
    print(f'\n--- {hid}: {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) < 100:
        print(f'  Insufficient data')
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
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
    
    t_res = test_rsi(test)
    v_res = test_rsi(validate)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}%")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}%")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
            results_summary.append((hid, f'{ticker} RSI<30', '✅', t_res['win_rate'], v_res['win_rate']))

# Different timeframes on QQQ
print('\n' + '='*90)
print('H116-H120: QQQ Different Hold Periods')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['rsi'] = rsi(qqq['close'])

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

hold_periods = [('H116', 3), ('H117', 7), ('H118', 10), ('H119', 15)]

for hid, hold in hold_periods:
    print(f'\n--- {hid}: QQQ RSI<30, {hold}D hold ---')
    
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
            results_summary.append((hid, f'QQQ RSI<30 {hold}D', '✅', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
