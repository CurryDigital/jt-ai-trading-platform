#!/usr/bin/env python3
"""
BATCH: More Sector ETFs, Hong Kong Tech
H136-H145
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

# More Sector ETFs
print('='*90)
print('H136-H140: More Sector ETFs RSI < 30')
print('='*90)

etfs = [('XLU', 'H136'), ('XLB', 'H137'), ('XLRE', 'H138')]

for ticker, hid in etfs:
    print(f'\n--- {hid}: {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM bronze.yf_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if not data:
        print(f'  No data')
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
            results_summary.append((hid, f'{ticker} RSI<30', t_res['win_rate'], v_res['win_rate']))

# Hong Kong Tech with different thresholds
print('\n' + '='*90)
print('H141-H145: Hong Kong Tech RSI < 25 (Tighter)')
print('='*90)

hk_stocks = [('0700.HK', 'H141'), ('9988.HK', 'H142'), ('3690.HK', 'H143'), ('1810.HK', 'H144'), ('9999.HK', 'H145')]

for ticker, hid in hk_stocks:
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
    
    def test_rsi25(period_df):
        trades = []
        for i in range(14, len(period_df) - 5):
            if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 25:
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + 5]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        if len(trades) < 5:
            return None
        r = pd.Series(trades)
        return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
    
    t_res = test_rsi25(test)
    v_res = test_rsi25(validate)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}%")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}%")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
            results_summary.append((hid, f'{ticker} RSI<25', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - Test: {r[2]:.1f}%, Val: {r[3]:.1f}%")

conn.close()
