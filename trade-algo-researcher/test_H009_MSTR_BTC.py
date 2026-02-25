#!/usr/bin/env python3
"""
3-TIER TESTING: H009 - MSTR-BTC Arbitrage
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
print('H009: MSTR-BTC Arbitrage')
print('Entry: BTC +2% prior day + MSTR flat/open lower')
print('Exit: 1 day')
print('='*90)

# Get BTC
cursor.execute('''
    SELECT date, close::float FROM bronze.yf_prices
    WHERE ticker = 'BTC-USD' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
btc_data = cursor.fetchall()
btc_df = pd.DataFrame(btc_data, columns=['date', 'btc'])
btc_df['date'] = pd.to_datetime(btc_df['date'])
btc_df['btc_return'] = btc_df['btc'].pct_change() * 100

# Get MSTR
cursor.execute('''
    SELECT date, close::float, open::float
    FROM silver.unified_prices
    WHERE ticker = 'MSTR' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
mstr_data = cursor.fetchall()
mstr_df = pd.DataFrame(mstr_data, columns=['date', 'mstr_close', 'mstr_open'])
mstr_df['date'] = pd.to_datetime(mstr_df['date'])

# Merge
df = pd.merge(btc_df, mstr_df, on='date')
df = df.sort_values('date').reset_index(drop=True)

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_arb(period_df):
    trades = []
    for i in range(1, len(period_df) - 1):
        # BTC > +2% yesterday
        if period_df['btc_return'].iloc[i] > 2.0:
            # Buy MSTR today, exit tomorrow
            entry = period_df['mstr_close'].iloc[i]
            exit_p = period_df['mstr_close'].iloc[i+1]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train (2021-22)', train), ('Test (2023-24)', test), ('Validate (2025-26)', validate)]:
    print(f'\n{name}:')
    res = test_arb(period)
    if res:
        print(f"  Trades: {res['trades']}, Win: {res['win_rate']:.1f}%")
    else:
        print('  INSUFFICIENT TRADES')

conn.close()
