#!/usr/bin/env python3
"""
COMPREHENSIVE HYPOTHESIS TESTING — ALL REMAINING BATCHES
Walk-forward validation on all untested hypotheses
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime

print('='*80)
print('COMPREHENSIVE: Testing ALL Remaining Hypotheses')
print('Method: Walk-forward (Train 2021-2022 / Test 2023-2024)')
print('='*80)

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
results = []

def get_data(ticker):
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) == 0:
        return None
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['return'] = df['close'].pct_change() * 100
    return df

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def classify(train_wr, test_wr, test_n):
    if test_n < 5:
        return '⏳ INSUFFICIENT'
    if test_wr >= 65 and abs(train_wr - test_wr) < 15:
        return '✅ GOLDEN'
    if test_wr >= 55:
        return '🟡 VALIDATED'
    return '❌ REJECTED'

def run_test(name, category, train_fn, test_fn):
    """Run a test and collect results"""
    try:
        train_rets = train_fn()
        test_rets = test_fn()
        
        train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
        test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
        status = classify(train_wr, test_wr, len(test_rets))
        
        print(f'{name}:')
        print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
        results.append((name, category, train_wr, test_wr, len(test_rets), status))
    except Exception as e:
        print(f'{name}: ERROR - {str(e)[:50]}')
        results.append((name, category, 0, 0, 0, '❌ ERROR'))

# ============================================
# BATCH 6: RSI + Stochastic Combinations
# ============================================
print('\n' + '='*80)
print('BATCH 6: RSI + Stochastic Combinations')
print('='*80)

qqq = get_data('QQQ')

# H6.1: RSI Extreme + Oversold
print('\nH6.1: RSI Extreme (<10)...')
if qqq is not None:
    qqq['rsi'] = rsi(qqq['close'])
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-10) if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 10]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-10) if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 10]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H6.1: RSI Extreme', 'Batch 6', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 7: Crypto Hypotheses (MSTR, COIN)
# ============================================
print('\n' + '='*80)
print('BATCH 7: Crypto Hypotheses')
print('='*80)

# H7.1: MSTR RSI Extreme
print('\nH7.1: MSTR RSI < 20...')
mstr = get_data('MSTR')
if mstr is not None:
    mstr['rsi'] = rsi(mstr['close'])
    train = mstr[mstr['date'] < pd.Timestamp('2023-01-01')]
    test = mstr[mstr['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-10) if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 20]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-10) if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 20]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H7.1: MSTR RSI Extreme', 'Batch 7', train_wr, test_wr, len(test_rets), status))

# H7.2: COIN RSI Extreme
print('\nH7.2: COIN RSI < 25...')
coin = get_data('COIN')
if coin is not None:
    coin['rsi'] = rsi(coin['close'])
    train = coin[coin['date'] < pd.Timestamp('2023-01-01')]
    test = coin[coin['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-10) if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 25]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-10) if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H7.2: COIN RSI Extreme', 'Batch 7', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 8: Volume + Price Patterns
# ============================================
print('\n' + '='*80)
print('BATCH 8: Volume + Price Patterns')
print('='*80)

# H8.1: Volume at Support
print('\nH8.1: Volume Spike at Support...')
if qqq is not None:
    qqq['sma50'] = qqq['close'].rolling(50).mean()
    qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(50, len(train)-5) 
                  if train['close'].iloc[i] > train['sma50'].iloc[i] * 0.98 and 
                  train['close'].iloc[i] < train['sma50'].iloc[i] * 1.02 and
                  train['volume'].iloc[i] > train['vol_avg'].iloc[i] * 1.5]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(50, len(test)-5) 
                 if test['close'].iloc[i] > test['sma50'].iloc[i] * 0.98 and 
                 test['close'].iloc[i] < test['sma50'].iloc[i] * 1.02 and
                 test['volume'].iloc[i] > test['vol_avg'].iloc[i] * 1.5]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H8.1: Volume at Support', 'Batch 8', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 9: BB %B Extreme
# ============================================
print('\n' + '='*80)
print('BATCH 9: Bollinger %B Extreme')
print('='*80)

print('\nH9.1: BB %B < 0...')
if qqq is not None:
    qqq['sma20'] = qqq['close'].rolling(20).mean()
    qqq['std20'] = qqq['close'].rolling(20).std()
    qqq['bb_lower'] = qqq['sma20'] - 2 * qqq['std20']
    qqq['bb_upper'] = qqq['sma20'] + 2 * qqq['std20']
    qqq['bb_pct_b'] = (qqq['close'] - qqq['bb_lower']) / (qqq['bb_upper'] - qqq['bb_lower'])
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-10) if pd.notna(train['bb_pct_b'].iloc[i]) and train['bb_pct_b'].iloc[i] < 0]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-10) if pd.notna(test['bb_pct_b'].iloc[i]) and test['bb_pct_b'].iloc[i] < 0]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H9.1: BB %B < 0', 'Batch 9', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 10: Multi-Indicator Combinations
# ============================================
print('\n' + '='*80)
print('BATCH 10: Multi-Indicator Combinations')
print('='*80)

print('\nH10.1: RSI + MACD + Volume...')
if qqq is not None:
    qqq['rsi'] = rsi(qqq['close'])
    qqq['ema12'] = qqq['close'].ewm(span=12).mean()
    qqq['ema26'] = qqq['close'].ewm(span=26).mean()
    qqq['macd'] = qqq['ema12'] - qqq['ema26']
    qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(26, len(train)-5) 
                  if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 30 and
                  train['macd'].iloc[i] > train['macd'].iloc[i-1] and
                  train['volume'].iloc[i] > train['vol_avg'].iloc[i]]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(26, len(test)-5) 
                 if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 30 and
                 test['macd'].iloc[i] > test['macd'].iloc[i-1] and
                 test['volume'].iloc[i] > test['vol_avg'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H10.1: RSI+MACD+Vol', 'Batch 10', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 11: Market Regime
# ============================================
print('\n' + '='*80)
print('BATCH 11: Market Regime Strategies')
print('='*80)

print('\nH11.1: RSI Extreme on Mondays...')
if qqq is not None:
    qqq['rsi'] = rsi(qqq['close'])
    qqq['dow'] = qqq['date'].dt.dayofweek
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(14, len(train)-10) 
                  if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 25 and train['dow'].iloc[i] == 0]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(14, len(test)-10) 
                 if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25 and test['dow'].iloc[i] == 0]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H11.1: Monday RSI Extreme', 'Batch 11', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 12: Time-Based
# ============================================
print('\n' + '='*80)
print('BATCH 12: Time-Based Strategies')
print('='*80)

print('\nH12.1: Month-End RSI Extreme...')
if qqq is not None:
    qqq['day'] = qqq['date'].dt.day
    qqq['days_in_month'] = qqq['date'].dt.days_in_month
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(14, len(train)-10) 
                  if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 25 and 
                  train['day'].iloc[i] >= train['days_in_month'].iloc[i] - 3]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(14, len(test)-10) 
                 if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25 and 
                 test['day'].iloc[i] >= test['days_in_month'].iloc[i] - 3]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H12.1: Month-End RSI', 'Batch 12', train_wr, test_wr, len(test_rets), status))

# ============================================
# BATCH 13: Extended Time-Based
# ============================================
print('\n' + '='*80)
print('BATCH 13: Extended Time-Based')
print('='*80)

print('\nH13.1: Friday Volume BO...')
if qqq is not None:
    qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-5) 
                  if train['volume'].iloc[i] > train['vol_avg'].iloc[i] * 1.5 and train['dow'].iloc[i] == 4]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-5) 
                 if test['volume'].iloc[i] > test['vol_avg'].iloc[i] * 1.5 and test['dow'].iloc[i] == 4]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('H13.1: Friday Volume BO', 'Batch 13', train_wr, test_wr, len(test_rets), status))

# ============================================
# ADDITIONAL: Momentum Lifecycle
# ============================================
print('\n' + '='*80)
print('ADDITIONAL: Momentum Strategies')
print('='*80)

print('\nA1: 3-Day Reversal...')
if qqq is not None:
    qqq['down_3'] = (qqq['close'] < qqq['close'].shift(1)) & (qqq['close'].shift(1) < qqq['close'].shift(2)) & (qqq['close'].shift(2) < qqq['close'].shift(3))
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(3, len(train)-5) if train['down_3'].iloc[i]]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(3, len(test)-5) if test['down_3'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('A1: 3-Day Reversal', 'Additional', train_wr, test_wr, len(test_rets), status))

conn.close()

# ============================================
# SUMMARY
# ============================================
print('\n' + '='*80)
print('COMPREHENSIVE VALIDATION SUMMARY')
print('='*80)

df = pd.DataFrame(results, columns=['Name', 'Batch', 'Train', 'Test', 'N', 'Status'])
df = df.sort_values('Test', ascending=False)

print('\n{:<30} {:<12} {:<10} {:<10} {:<8} {:<15}'.format('Hypothesis', 'Batch', 'Train%', 'Test%', 'N', 'Status'))
print('-'*90)
for _, row in df.iterrows():
    print('{:<30} {:<12} {:<10.1f} {:<10.1f} {:<8} {:<15}'.format(
        row['Name'][:30], row['Batch'], row['Train'], row['Test'], row['N'], row['Status']))

golden = df[df['Status'] == '✅ GOLDEN']
validated = df[df['Status'] == '🟡 VALIDATED']
rejected = df[df['Status'] == '❌ REJECTED']
insufficient = df[df['Status'] == '⏳ INSUFFICIENT']

print('\n' + '='*80)
print('FINAL CLASSIFICATION')
print('='*80)

print(f'\n✅ GOLDEN: {len(golden)} hypotheses')
for _, row in golden.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n🟡 VALIDATED: {len(validated)} hypotheses')
for _, row in validated.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n❌ REJECTED: {len(rejected)} hypotheses')
for _, row in rejected.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n⏳ INSUFFICIENT: {len(insufficient)} hypotheses')

print('\n' + '='*80)
print(f'TOTAL: {len(df)} tested | ✅ {len(golden)} | 🟡 {len(validated)} | ❌ {len(rejected)} | ⏳ {len(insufficient)}')
print('='*80)
