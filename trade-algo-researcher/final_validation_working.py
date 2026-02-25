#!/usr/bin/env python3
"""
COMPREHENSIVE VALIDATION - SIMPLIFIED
All strategies with proper date handling
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*70)
print('COMPREHENSIVE VALIDATION - ALL STRATEGIES')
print('Train: 2021-2022 | Test: 2023-2024')
print('='*70)

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

all_results = []

# Helper function
def get_prices(ticker):
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) == 0:
        return None
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['return'] = df['close'].pct_change() * 100
    return df

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

print('\n' + '='*70)
print('GOLDEN STRATEGIES')
print('='*70)

# 1. COIN Strong Uptrend
print('\n1. COIN Strong Uptrend GOLD...')
coin = get_prices('COIN')
spy = get_prices('SPY')

if coin is not None and spy is not None:
    coin['rsi'] = calculate_rsi(coin['close'])
    spy['sma200'] = spy['close'].rolling(200).mean()
    spy['sma50'] = spy['close'].rolling(50).mean()
    spy['golden_cross'] = spy['sma50'] > spy['sma200']
    
    merged = coin.merge(spy[['date', 'golden_cross']], on='date')
    
    # Train/Test split
    train = merged[merged['date'] < pd.Timestamp('2023-01-01')]
    test = merged[merged['date'] >= pd.Timestamp('2023-01-01')]
    
    # Train performance
    train_trades = []
    for i in range(20, len(train) - 10):
        if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 25 and train['golden_cross'].iloc[i]:
            ret = (train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
            train_trades.append(ret)
    
    # Test performance
    test_trades = []
    for i in range(20, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25 and test['golden_cross'].iloc[i]:
            ret = (test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
            test_trades.append(ret)
    
    train_wr = (pd.Series(train_trades) > 0).mean() * 100 if train_trades else 0
    test_wr = (pd.Series(test_trades) > 0).mean() * 100 if test_trades else 0
    decay = train_wr - test_wr
    
    print(f'   Train: {train_wr:.1f}% ({len(train_trades)} trades)')
    print(f'   Test:  {test_wr:.1f}% ({len(test_trades)} trades)')
    print(f'   Decay: {decay:+.1f}%')
    all_results.append(('COIN Strong Uptrend', train_wr, test_wr, len(test_trades), decay))

# 2. QQQ Lead-Lag
print('\n2. QQQ Lead-Lag → 0700.HK...')
qqq = get_prices('QQQ')
hk = get_prices('0700.HK')

if qqq is not None and hk is not None:
    hk['prev'] = hk['close'].shift(1)
    hk['gap'] = (hk['close'] - hk['prev']) / hk['prev'] * 100
    
    qqq['next_date'] = qqq['date'] + pd.Timedelta(days=1)
    merged = qqq.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    
    train = merged[merged['date_y'] < pd.Timestamp('2023-01-01')]
    test = merged[merged['date_y'] >= pd.Timestamp('2023-01-01')]
    
    train_signals = train[train['return'] > 2.0]
    test_signals = test[test['return'] > 2.0]
    
    train_wr = (train_signals['gap'] > 0).mean() * 100 if len(train_signals) > 0 else 0
    test_wr = (test_signals['gap'] > 0).mean() * 100 if len(test_signals) > 0 else 0
    decay = train_wr - test_wr
    
    print(f'   Train: {train_wr:.1f}% ({len(train_signals)} signals)')
    print(f'   Test:  {test_wr:.1f}% ({len(test_signals)} signals)')
    print(f'   Decay: {decay:+.1f}%')
    all_results.append(('QQQ Lead-Lag', train_wr, test_wr, len(test_signals), decay))

# 3. MSTR SPY Regime
print('\n3. MSTR SPY Regime...')
mstr = get_prices('MSTR')

if mstr is not None and spy is not None:
    mstr['rsi'] = calculate_rsi(mstr['close'])
    spy['above_50d'] = spy['close'] > spy['close'].rolling(50).mean()
    
    merged = mstr.merge(spy[['date', 'above_50d']], on='date')
    
    train = merged[merged['date'] < pd.Timestamp('2023-01-01')]
    test = merged[merged['date'] >= pd.Timestamp('2023-01-01')]
    
    train_trades = []
    for i in range(20, len(train) - 10):
        if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 25 and train['above_50d'].iloc[i]:
            ret = (train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
            train_trades.append(ret)
    
    test_trades = []
    for i in range(20, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25 and test['above_50d'].iloc[i]:
            ret = (test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
            test_trades.append(ret)
    
    train_wr = (pd.Series(train_trades) > 0).mean() * 100 if train_trades else 0
    test_wr = (pd.Series(test_trades) > 0).mean() * 100 if test_trades else 0
    decay = train_wr - test_wr
    
    print(f'   Train: {train_wr:.1f}% ({len(train_trades)} trades)')
    print(f'   Test:  {test_wr:.1f}% ({len(test_trades)} trades)')
    print(f'   Decay: {decay:+.1f}%')
    all_results.append(('MSTR SPY Regime', train_wr, test_wr, len(test_trades), decay))

# 4. IWM SPY Regime
print('\n4. IWM SPY Regime...')
iwm = get_prices('IWM')

if iwm is not None and spy is not None:
    iwm['rsi'] = calculate_rsi(iwm['close'])
    spy['above_200d'] = spy['close'] > spy['close'].rolling(200).mean()
    
    merged = iwm.merge(spy[['date', 'above_200d']], on='date')
    
    train = merged[merged['date'] < pd.Timestamp('2023-01-01')]
    test = merged[merged['date'] >= pd.Timestamp('2023-01-01')]
    
    train_trades = []
    for i in range(20, len(train) - 10):
        if pd.notna(train['rsi'].iloc[i]) and train['rsi'].iloc[i] < 20 and train['above_200d'].iloc[i]:
            ret = (train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
            train_trades.append(ret)
    
    test_trades = []
    for i in range(20, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 20 and test['above_200d'].iloc[i]:
            ret = (test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
            test_trades.append(ret)
    
    train_wr = (pd.Series(train_trades) > 0).mean() * 100 if train_trades else 0
    test_wr = (pd.Series(test_trades) > 0).mean() * 100 if test_trades else 0
    decay = train_wr - test_wr
    
    print(f'   Train: {train_wr:.1f}% ({len(train_trades)} trades)')
    print(f'   Test:  {test_wr:.1f}% ({len(test_trades)} trades)')
    print(f'   Decay: {decay:+.1f}%')
    all_results.append(('IWM SPY Regime', train_wr, test_wr, len(test_trades), decay))

# 5. NVDA AI Theme
print('\n5. NVDA AI Theme → 0700.HK...')
nvda = get_prices('NVDA')

if nvda is not None and hk is not None:
    nvda['next_date'] = nvda['date'] + pd.Timedelta(days=1)
    merged = nvda.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    
    train = merged[merged['date_y'] < pd.Timestamp('2023-01-01')]
    test = merged[merged['date_y'] >= pd.Timestamp('2023-01-01')]
    
    train_signals = train[train['return'] > 5.0]
    test_signals = test[test['return'] > 5.0]
    
    train_wr = (train_signals['gap'] > 0).mean() * 100 if len(train_signals) > 0 else 0
    test_wr = (test_signals['gap'] > 0).mean() * 100 if len(test_signals) > 0 else 0
    decay = train_wr - test_wr
    
    print(f'   Train: {train_wr:.1f}% ({len(train_signals)} signals)')
    print(f'   Test:  {test_wr:.1f}% ({len(test_signals)} signals)')
    print(f'   Decay: {decay:+.1f}%')
    all_results.append(('NVDA AI Theme', train_wr, test_wr, len(test_signals), decay))

conn.close()

# Summary
print('\n' + '='*70)
print('FINAL VALIDATION SUMMARY')
print('='*70)

print('\n{:<25} {:<12} {:<12} {:<12} {:<10} {:<8}'.format(
    'Strategy', 'Train WR%', 'Test WR%', 'Decay%', 'Test N', 'Status'
))
print('-'*70)

for name, train_wr, test_wr, n, decay in all_results:
    status = '✅' if test_wr >= 65 and abs(decay) < 15 else '🟡' if test_wr >= 55 else '❌'
    print('{:<25} {:<12.1f} {:<12.1f} {:<12.1f} {:<10} {:<8}'.format(
        name, train_wr, test_wr, decay, n, status
    ))

print('\n' + '='*70)
print('INTERPRETATION:')
print('='*70)
print('✅ = Test >=65% AND Decay <15% (Reliable)')
print('🟡 = Test 55-65% OR High Decay (Moderate)')
print('❌ = Test <55% (Weak)')
print('\nTest period (2023-2024) is OUT-OF-SAMPLE from training')
print('='*70)
