#!/usr/bin/env python3
"""
3-TIER TESTING: H006 - USD/JPY Trend Following
H008 - XLE Energy Momentum
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

print('='*90)
print('H006: USD/JPY Trend Following')
print('='*90)

cursor.execute('''
    SELECT timestamp::date as date, close::float 
    FROM bronze.fx_prices 
    WHERE pair = 'USDJPY' AND timestamp BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY timestamp
''')
fx_data = cursor.fetchall()
fx_df = pd.DataFrame(fx_data, columns=['date', 'close'])
fx_df['date'] = pd.to_datetime(fx_df['date'])
fx_df['sma20'] = fx_df['close'].rolling(20).mean()
fx_df['sma50'] = fx_df['close'].rolling(50).mean()

train = fx_df[(fx_df['date'] >= '2021-01-01') & (fx_df['date'] <= '2022-12-31')]
test = fx_df[(fx_df['date'] >= '2023-01-01') & (fx_df['date'] <= '2024-12-31')]
validate = fx_df[(fx_df['date'] >= '2025-01-01') & (fx_df['date'] <= '2026-02-20')]

def test_fx(period_df):
    trades = []
    for i in range(50, len(period_df) - 10):
        if (pd.notna(period_df['sma20'].iloc[i]) and pd.notna(period_df['sma50'].iloc[i]) and
            period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            period_df['sma20'].iloc[i] > period_df['sma50'].iloc[i]):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+10, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_fx(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

print('\n' + '='*90)
print('H008: XLE Energy Momentum')
print('='*90)

cursor.execute('''
    SELECT date, close::float, volume::float FROM bronze.yf_prices
    WHERE ticker = 'XLE' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
xle_data = cursor.fetchall()
xle_df = pd.DataFrame(xle_data, columns=['date', 'close', 'volume'])
xle_df['date'] = pd.to_datetime(xle_df['date'])
xle_df['sma20'] = xle_df['close'].rolling(20).mean()
xle_df['vol_avg'] = xle_df['volume'].rolling(20).mean()
xle_df['vol_ratio'] = xle_df['volume'] / xle_df['vol_avg']

def test_xle_strategy(period_df):
    trades = []
    for i in range(20, len(period_df) - 7):
        if (pd.notna(period_df['sma20'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma20'].iloc[i] and
            pd.notna(period_df['vol_ratio'].iloc[i]) and period_df['vol_ratio'].iloc[i] > 1.5):
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[min(i+7, len(period_df)-1)]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

train_xle = xle_df[(xle_df['date'] >= '2021-01-01') & (xle_df['date'] <= '2022-12-31')]
test_xle_df = xle_df[(xle_df['date'] >= '2023-01-01') & (xle_df['date'] <= '2024-12-31')]
val_xle_df = xle_df[(xle_df['date'] >= '2025-01-01') & (xle_df['date'] <= '2026-02-20')]

for name, period in [('Train', train_xle), ('Test', test_xle_df), ('Validate', val_xle_df)]:
    res = test_xle_strategy(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

conn.close()
