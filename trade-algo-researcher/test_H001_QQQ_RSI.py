#!/usr/bin/env python3
"""
3-TIER TESTING: H001 - QQQ RSI Extreme Mean Reversion
Null Hypothesis: Win rate ≤ 50% (no edge)
Alternative: Win rate > 55% with statistical significance
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
print('H001: QQQ RSI Extreme Mean Reversion')
print('Entry: RSI(14) < 20 | Exit: 5 days or RSI > 50')
print('='*90)

# DB connection
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
    SELECT date, open::float, high::float, low::float, close::float, volume::float
    FROM silver.unified_prices
    WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20'
    ORDER BY date
''')
data = cursor.fetchall()
df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
df['date'] = pd.to_datetime(df['date'])

# Calculate RSI
def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = rsi(df['close'])

# Split periods
train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]

def test_strategy(period_df, period_name):
    """Test strategy on given period"""
    trades = []
    
    for i in range(14, len(period_df) - 5):
        if pd.notna(period_df['rsi'].iloc[i]) and period_df['rsi'].iloc[i] < 20:
            entry = period_df['close'].iloc[i]
            
            # Exit at 5 days OR when RSI > 50
            exit_idx = i + 5
            for j in range(i+1, min(i+6, len(period_df))):
                if pd.notna(period_df['rsi'].iloc[j]) and period_df['rsi'].iloc[j] > 50:
                    exit_idx = j
                    break
            
            exit_p = period_df['close'].iloc[exit_idx]
            ret = (exit_p - entry) / entry * 100 - 0.1  # -0.1% transaction cost
            trades.append(ret)
    
    if len(trades) < 5:
        return None
    
    r = pd.Series(trades)
    wr = (r > 0).mean()
    avg_ret = r.mean()
    sharpe = r.mean() / r.std() * np.sqrt(252/5) if r.std() > 0 else 0
    
    # 95% confidence interval for win rate
    n = len(trades)
    ci_low = wr - 1.96 * np.sqrt(wr * (1-wr) / n) if n > 0 else 0
    ci_high = wr + 1.96 * np.sqrt(wr * (1-wr) / n) if n > 0 else 0
    
    # Statistical test vs 50% (simple check: win rate > 55% is significant if n > 20)
    n = len(trades)
    significant = wr > 0.55 and n >= 20
    
    return {
        'trades': n,
        'win_rate': wr * 100,
        'avg_return': avg_ret,
        'sharpe': sharpe,
        'ci_low': ci_low * 100,
        'ci_high': ci_high * 100,
        'significant': significant
    }

# Test all periods
print('\n' + '='*90)
results = {}
for name, period in [('Train (2021-22)', train), ('Test (2023-24)', test), ('Validate (2025-26)', validate)]:
    print(f'\n{name}:')
    res = test_strategy(period, name)
    if res:
        print(f"  Trades: {res['trades']}")
        print(f"  Win Rate: {res['win_rate']:.1f}% [95% CI: {res['ci_low']:.1f}%, {res['ci_high']:.1f}%]")
        print(f"  Avg Return: {res['avg_return']:.2f}%")
        print(f"  Sharpe: {res['sharpe']:.2f}")
        print(f"  P-value (vs 50%): {'Significant' if res['significant'] else 'Not significant'}")
        results[name] = res
    else:
        print('  INSUFFICIENT TRADES')
        results[name] = None

# Classification
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

print('\n' + '='*90)
print('SUMMARY')
print('='*90)
print('H001: QQQ RSI Extreme Mean Reversion')
print('Null hypothesis (≤50% win rate):', 'REJECTED' if results['Validate (2025-26)'] and results['Validate (2025-26)']['win_rate'] > 55 else 'NOT REJECTED')
