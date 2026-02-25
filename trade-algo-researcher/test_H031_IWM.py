#!/usr/bin/env python3
"""
FINAL: H031 (10th Strategy)
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
print('H031: IWM Small Cap Trend Following')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'IWM' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
iwm = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
iwm['date'] = pd.to_datetime(iwm['date'])
iwm['sma50'] = iwm['close'].rolling(50).mean()

train = iwm[(iwm['date'] >= '2021-01-01') & (iwm['date'] <= '2022-12-31')]
test = iwm[(iwm['date'] >= '2023-01-01') & (iwm['date'] <= '2024-12-31')]
validate = iwm[(iwm['date'] >= '2025-01-01') & (iwm['date'] <= '2026-02-20')]

def test_iwm(period_df):
    trades = []
    for i in range(50, len(period_df) - 10):
        if pd.notna(period_df['sma50'].iloc[i]) and period_df['close'].iloc[i] > period_df['sma50'].iloc[i]:
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_iwm(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_iwm(test)
v_res = test_iwm(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"\nVerdict: {verdict}")
else:
    print('\n❌ FAILED - Insufficient data')

conn.close()
