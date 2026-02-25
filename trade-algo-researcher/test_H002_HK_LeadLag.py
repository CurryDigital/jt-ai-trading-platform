#!/usr/bin/env python3
"""
3-TIER TESTING: H002 - HK Tech Lead-Lag (QQQ → 0700.HK)
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*90)
print('H002: HK Tech Lead-Lag (QQQ → 0700.HK)')
print('Entry: QQQ > +1% → Buy 0700.HK next day')
print('Exit: 1 day hold')
print('='*90)

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

# Get QQQ data
cursor.execute('''
    SELECT date, close::float
    FROM silver.unified_prices
    WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
qqq_data = cursor.fetchall()
qqq_df = pd.DataFrame(qqq_data, columns=['date', 'close'])
qqq_df['date'] = pd.to_datetime(qqq_df['date'])
qqq_df['qqq_return'] = qqq_df['close'].pct_change() * 100

# Get 0700.HK data
cursor.execute('''
    SELECT date, close::float
    FROM silver.unified_prices
    WHERE ticker = '0700.HK' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
hk_data = cursor.fetchall()
hk_df = pd.DataFrame(hk_data, columns=['date', 'close'])
hk_df['date'] = pd.to_datetime(hk_df['date'])
hk_df['hk_return'] = hk_df['close'].pct_change() * 100

# Merge on date
df = pd.merge(qqq_df, hk_df, on='date', suffixes=('_qqq', '_hk'))
df = df.sort_values('date').reset_index(drop=True)

# Split periods
train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_strategy(period_df):
    trades = []
    
    for i in range(1, len(period_df) - 1):
        # QQQ > +1% today
        if period_df['qqq_return'].iloc[i] > 1.0:
            # Buy 0700.HK next day, hold 1 day
            entry = period_df['close_hk'].iloc[i]  # Same day close approximation
            exit_p = period_df['close_hk'].iloc[i+1]  # Next day close
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10:
        return None
    
    r = pd.Series(trades)
    wr = (r > 0).mean()
    avg_ret = r.mean()
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0
    
    n = len(trades)
    ci_low = max(0, wr - 1.96 * np.sqrt(wr * (1-wr) / n)) if n > 0 else 0
    ci_high = min(1, wr + 1.96 * np.sqrt(wr * (1-wr) / n)) if n > 0 else 1
    
    return {
        'trades': n,
        'win_rate': wr * 100,
        'avg_return': avg_ret,
        'sharpe': sharpe,
        'ci_low': ci_low * 100,
        'ci_high': ci_high * 100
    }

print('\n' + '='*90)
results = {}
for name, period in [('Train (2021-22)', train), ('Test (2023-24)', test), ('Validate (2025-26)', validate)]:
    print(f'\n{name}:')
    res = test_strategy(period)
    if res:
        print(f"  Trades: {res['trades']}")
        print(f"  Win Rate: {res['win_rate']:.1f}% [95% CI: {res['ci_low']:.1f}%, {res['ci_high']:.1f}%]")
        print(f"  Avg Return: {res['avg_return']:.2f}%")
        print(f"  Sharpe: {res['sharpe']:.2f}")
        results[name] = res
    else:
        print('  INSUFFICIENT TRADES')
        results[name] = None

print('\n' + '='*90)
print('CLASSIFICATION')
print('='*90)

if results['Validate (2025-26)'] and results['Test (2023-24)']:
    val_wr = results['Validate (2025-26)']['win_rate']
    test_wr = results['Test (2023-24)']['win_rate']
    train_wr = results['Train (2021-22)']['win_rate'] if results['Train (2021-22)'] else 0
    
    decay_test = test_wr - train_wr
    decay_val = val_wr - test_wr
    
    print(f'\nDecay Test vs Train: {decay_test:+.1f}%')
    print(f'Decay Val vs Test: {decay_val:+.1f}%')
    
    if val_wr >= 60 and test_wr >= 60 and abs(decay_val) < 20:
        verdict = '🏆 GOLDEN'
    elif test_wr >= 60 and val_wr >= 55:
        verdict = '✅ VALIDATED'
    elif test_wr >= 55 and val_wr >= 50:
        verdict = '🟡 BORDERLINE'
    else:
        verdict = '❌ FAILED'
    
    print(f'\nVerdict: {verdict}')
    print(f'  Train: {train_wr:.1f}% | Test: {test_wr:.1f}% | Validate: {val_wr:.1f}%')
else:
    print('\n❌ FAILED - Insufficient data')

conn.close()
