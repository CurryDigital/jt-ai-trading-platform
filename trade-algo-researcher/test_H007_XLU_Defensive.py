#!/usr/bin/env python3
"""
3-TIER TESTING: H007 - Defensive Sector Flight (XLU vs SPY)
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
print('H007: Defensive Sector Flight (XLU vs SPY)')
print('Entry: SPY < SMA50 + XLU > SMA20')
print('Exit: 5 days or SPY > SMA50')
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

# Get SPY data
cursor.execute('''
    SELECT date, close::float
    FROM silver.unified_prices
    WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close'])
spy_df['date'] = pd.to_datetime(spy_df['date'])
spy_df['spy_sma50'] = spy_df['spy_close'].rolling(50).mean()

# Get XLU data
cursor.execute('''
    SELECT date, close::float
    FROM bronze.yf_prices
    WHERE ticker = 'XLU' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
xlu_data = cursor.fetchall()
xlu_df = pd.DataFrame(xlu_data, columns=['date', 'xlu_close'])
xlu_df['date'] = pd.to_datetime(xlu_df['date'])
xlu_df['xlu_sma20'] = xlu_df['xlu_close'].rolling(20).mean()

# Merge
df = pd.merge(spy_df, xlu_df, on='date')
df = df.sort_values('date').reset_index(drop=True)

train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_strategy(period_df):
    trades = []
    
    for i in range(50, len(period_df) - 5):
        if (pd.notna(period_df['spy_sma50'].iloc[i]) and
            period_df['spy_close'].iloc[i] < period_df['spy_sma50'].iloc[i] and
            pd.notna(period_df['xlu_sma20'].iloc[i]) and
            period_df['xlu_close'].iloc[i] > period_df['xlu_sma20'].iloc[i]):
            
            entry = period_df['xlu_close'].iloc[i]
            
            # Exit at 5 days OR when SPY > SMA50
            exit_idx = i + 5
            for j in range(i+1, min(i+6, len(period_df))):
                if (pd.notna(period_df['spy_close'].iloc[j]) and
                    pd.notna(period_df['spy_sma50'].iloc[j]) and
                    period_df['spy_close'].iloc[j] > period_df['spy_sma50'].iloc[j]):
                    exit_idx = j
                    break
            
            exit_p = period_df['xlu_close'].iloc[exit_idx]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10:
        return None
    
    r = pd.Series(trades)
    wr = (r > 0).mean()
    avg_ret = r.mean()
    sharpe = r.mean() / r.std() * np.sqrt(252/5) if r.std() > 0 else 0
    
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
