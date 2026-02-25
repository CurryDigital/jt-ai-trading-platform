#!/usr/bin/env python3
"""
HK MARKET EFFICIENCY TEST
Same strategies on HK Tech vs US Tech
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

print('='*90)
print('HK MARKET EFFICIENCY TEST: RSI < 30 Mean Reversion')
print('='*90)

hk_stocks = ['0700.HK', '9988.HK', '3690.HK', '1810.HK', '9999.HK', '9618.HK', '1024.HK']

results = []

for ticker in hk_stocks:
    print(f'\n--- {ticker} ---')
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
        if len(trades) < 5:
            return None
        r = pd.Series(trades)
        return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
    
    t_res = test_rsi(test)
    v_res = test_rsi(validate)
    
    if t_res and v_res:
        print(f"  Test: {t_res['trades']} trades, {t_res['win_rate']:.1f}% win")
        print(f"  Validate: {v_res['trades']} trades, {v_res['win_rate']:.1f}% win")
        status = '✅' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌'
        print(f"  {status}")
        results.append((ticker, t_res['win_rate'], v_res['win_rate'], t_res['trades']))

print('\n' + '='*90)
print('HK RSI < 30 SUMMARY')
print('='*90)
print(f'{"Ticker":<12} {"Test":<8} {"Validate":<8} {"Trades"}')
print('-'*50)
for r in results:
    print(f'{r[0]:<12} {r[1]:>6.1f}% {r[2]:>6.1f}% {r[3]:>6}')

# Compare to US
print('\n' + '='*90)
print('US vs HK COMPARISON (RSI < 30)')
print('='*90)
us_results = [('QQQ', 81.0, 66.7), ('SPY', 77.3, 69.2), ('NVDA', 90.9, 91.7), ('AMD', 63.3, 57.9)]
print(f'{"Market":<12} {"Avg Test":<10} {"Avg Validate"}')
print('-'*40)
us_avg_test = np.mean([r[1] for r in us_results])
us_avg_val = np.mean([r[2] for r in us_results])
hk_avg_test = np.mean([r[1] for r in results]) if results else 0
hk_avg_val = np.mean([r[2] for r in results]) if results else 0
print(f'{"US Tech":<12} {us_avg_test:>6.1f}% {us_avg_val:>10.1f}%')
print(f'{"HK Tech":<12} {hk_avg_test:>6.1f}% {hk_avg_val:>10.1f}%')

if hk_avg_test > us_avg_test:
    print('\n🎯 HK MARKET LESS EFFICIENT — Higher win rates confirmed!')
else:
    print('\n❌ HK market shows similar efficiency to US')

conn.close()
