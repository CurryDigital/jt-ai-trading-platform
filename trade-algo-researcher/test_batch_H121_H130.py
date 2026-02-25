#!/usr/bin/env python3
"""
BATCH: Sector ETFs, Multi-factor
H121-H130
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

# Sector ETFs RSI < 30
print('='*90)
print('H121-H125: Sector ETFs RSI < 30')
print('='*90)

etfs = [('XLF', 'H121'), ('XLE', 'H122'), ('XLV', 'H123'), ('XLI', 'H124'), ('XLP', 'H125')]

for ticker, hid in etfs:
    print(f'\n--- {hid}: {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM bronze.yf_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
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

# Multi-factor: RSI + Volume
print('\n' + '='*90)
print('H126-H130: Multi-factor RSI + Volume')
print('='*90)

stocks = [('SPY', 'H126'), ('QQQ', 'H127'), ('NVDA', 'H128'), ('AAPL', 'H129'), ('MSFT', 'H130')]

for ticker, hid in stocks:
    print(f'\n--- {hid}: {ticker} RSI<30 + Vol>1.2x ---')
    cursor.execute(f'''
        SELECT date, close::float, volume::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    def test_multi(period_df):
        trades = []
        for i in range(20, len(period_df) - 5):
            if (pd.notna(period_df['rsi'].iloc[i]) and
                period_df['rsi'].iloc[i] < 30 and
                pd.notna(period_df['vol_ratio'].iloc[i]) and
                period_df['vol_ratio'].iloc[i] > 1.2):
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + 5]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        if len(trades) < 5:
            return None
        r = pd.Series(trades)
        return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
    
    t_res = test_multi(test)
    v_res = test_multi(validate)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}%")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}%")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55:
            results_summary.append((hid, f'{ticker} RSI+Vol', '✅', t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
