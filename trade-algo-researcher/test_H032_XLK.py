#!/usr/bin/env python3
"""
FINAL: H032 (10th Strategy - Alternative)
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
print('H032: XLK Tech ETF RSI < 30 Mean Reversion')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

xlk['rsi'] = rsi(xlk['close'])

train = xlk[(xlk['date'] >= '2021-01-01') & (xlk['date'] <= '2022-12-31')]
test = xlk[(xlk['date'] >= '2023-01-01') & (xlk['date'] <= '2024-12-31')]
validate = xlk[(xlk['date'] >= '2025-01-01') & (xlk['date'] <= '2026-02-20')]

def test_xlk(period_df):
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

for name, period in [('Train', train), ('Test', test), ('Validate', validate)]:
    res = test_xlk(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_xlk(test)
v_res = test_xlk(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"\nVerdict: {verdict}")
else:
    print('\n❌ FAILED - Insufficient data')

conn.close()
