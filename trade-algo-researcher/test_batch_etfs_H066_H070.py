#!/usr/bin/env python3
"""
BATCH: Sector ETFs — XLE, XLF, XLU, XLI, XLP
H066-H070
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

results_summary = []

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

etfs = ['XLE', 'XLF', 'XLU', 'XLI', 'XLP']
h_ids = ['H066', 'H067', 'H068', 'H069', 'H070']

for etf, h_id in zip(etfs, h_ids):
    print('='*90)
    print(f'{h_id}: {etf} RSI < 30 Mean Reversion')
    print('='*90)
    
    cursor.execute(f"""SELECT date, close::float FROM bronze.yf_prices WHERE ticker = '{etf}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date""")
    df = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
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
    
    for name, period in [('Test', test), ('Validate', validate)]:
        res = test_rsi(period)
        if res:
            print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
        else:
            print(f"{name}: Insufficient trades")
    
    t_res = test_rsi(test)
    v_res = test_rsi(validate)
    if t_res and v_res:
        verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
        print(f"Verdict: {verdict}")
        results_summary.append((h_id, f'{etf} RSI<30', verdict, t_res['win_rate'], v_res['win_rate']))
    print()

print('='*90)
print('NEW VALIDATED')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
