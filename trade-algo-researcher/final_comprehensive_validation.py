#!/usr/bin/env python3
"""
COMPREHENSIVE STRATEGY & HYPOTHESIS RE-VALIDATION
Complete audit of all strategies with proper train/test splits
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
print('COMPREHENSIVE VALIDATION: ALL STRATEGIES & HYPOTHESES')
print('Method: Walk-forward analysis with train/test splits')
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

all_results = []

def get_data(ticker, start='2021-01-01', end='2024-12-31'):
    """Get price data"""
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '{start}' AND '{end}'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) == 0:
        return None
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['return'] = df['close'].pct_change() * 100
    return df

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def walk_forward_test(name, train_data, test_data, strategy_func):
    """Test strategy with walk-forward validation"""
    
    # Train period performance
    train_signals = strategy_func(train_data)
    train_wr = (train_signals['return'] > 0).mean() * 100 if len(train_signals) > 0 else 0
    
    # Test period performance
    test_signals = strategy_func(test_data)
    test_wr = (test_signals['return'] > 0).mean() * 100 if len(test_signals) > 0 else 0
    
    # Decay check
    decay = train_wr - test_wr
    
    status = '✅' if test_wr >= 55 and decay < 15 else '🟡' if test_wr >= 50 else '❌'
    
    return {
        'name': name,
        'train_wr': train_wr,
        'test_wr': test_wr,
        'train_trades': len(train_signals),
        'test_trades': len(test_signals),
        'decay': decay,
        'status': status
    }

print('\n' + '='*80)
print('PART 1: GOLDEN STRATEGIES')
print('='*80)

# STRATEGY 1: COIN Strong Uptrend
print('\n1. COIN Strong Uptrend GOLD...')
coin = get_data('COIN')
spy = get_data('SPY')

if coin is not None and spy is not None:
    coin['rsi'] = calculate_rsi(coin['close'])
    spy['sma200'] = spy['close'].rolling(200).mean()
    spy['sma50'] = spy['close'].rolling(50).mean()
    spy['golden_cross'] = spy['sma50'] > spy['sma200']
    
    merged = coin.merge(spy[['date', 'golden_cross']], on='date')
    merged['date'] = pd.to_datetime(merged['date'])
    
    # Split: Train 2021-2022, Test 2023-2024
    train = merged[merged['date'] < '2023-01-01']
    test = merged[merged['date'] >= '2023-01-01']
    
    def coin_strategy(df):
        trades = []
        for i in range(20, len(df) - 10):
            if pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 25 and df['golden_cross'].iloc[i]:
                ret = (df['close'].iloc[i+10] - df['close'].iloc[i]) / df['close'].iloc[i] * 100 - 0.1
                trades.append({'return': ret})
        return pd.DataFrame(trades)
    
    result = walk_forward_test('COIN Strong Uptrend', train, test, coin_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

# STRATEGY 2: QQQ Lead-Lag
print('\n2. QQQ Lead-Lag → 0700.HK...')
qqq = get_data('QQQ')
hk = get_data('0700.HK')

if qqq is not None and hk is not None:
    hk['prev'] = hk['close'].shift(1)
    hk['gap'] = (hk['open'] - hk['prev']) / hk['prev'] * 100
    
    qqq['next_date'] = pd.to_datetime(qqq['date']) + pd.Timedelta(days=1)
    hk['date'] = pd.to_datetime(hk['date'])
    merged = qqq.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    
    train = merged[merged['date_y'] < '2023-01-01']
    test = merged[merged['date_y'] >= '2023-01-01']
    
    def qqq_strategy(df):
        signals = df[df['return'] > 2.0]
        return pd.DataFrame({'return': signals['gap']})
    
    result = walk_forward_test('QQQ Lead-Lag', train, test, qqq_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

# STRATEGY 3: IWM SPY Regime
print('\n3. IWM SPY Regime...')
iwm = get_data('IWM')

if iwm is not None and spy is not None:
    iwm['rsi'] = calculate_rsi(iwm['close'])
    spy['above_200d'] = spy['close'] > spy['close'].rolling(200).mean()
    
    merged = iwm.merge(spy[['date', 'above_200d']], on='date')
    
    train = merged[merged['date'] < '2023-01-01']
    test = merged[merged['date'] >= '2023-01-01']
    
    def iwm_strategy(df):
        trades = []
        for i in range(20, len(df) - 10):
            if pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 20 and df['above_200d'].iloc[i]:
                ret = (df['close'].iloc[i+10] - df['close'].iloc[i]) / df['close'].iloc[i] * 100 - 0.1
                trades.append({'return': ret})
        return pd.DataFrame(trades)
    
    result = walk_forward_test('IWM SPY Regime', train, test, iwm_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

# STRATEGY 4: MSTR SPY Regime
print('\n4. MSTR SPY Regime...')
mstr = get_data('MSTR')

if mstr is not None and spy is not None:
    mstr['rsi'] = calculate_rsi(mstr['close'])
    spy['above_50d'] = spy['close'] > spy['close'].rolling(50).mean()
    
    merged = mstr.merge(spy[['date', 'above_50d']], on='date')
    
    train = merged[merged['date'] < '2023-01-01']
    test = merged[merged['date'] >= '2023-01-01']
    
    def mstr_strategy(df):
        trades = []
        for i in range(20, len(df) - 10):
            if pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 25 and df['above_50d'].iloc[i]:
                ret = (df['close'].iloc[i+10] - df['close'].iloc[i]) / df['close'].iloc[i] * 100 - 0.1
                trades.append({'return': ret})
        return pd.DataFrame(trades)
    
    result = walk_forward_test('MSTR SPY Regime', train, test, mstr_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

print('\n' + '='*80)
print('PART 2: CROSS-MARKET HYPOTHESES')
print('='*80)

# H#005: NVDA Lead-Lag
print('\nH#005: NVDA → 0700.HK...')
nvda = get_data('NVDA')

if nvda is not None and hk is not None:
    nvda['next_date'] = pd.to_datetime(nvda['date']) + pd.Timedelta(days=1)
    merged = nvda.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    
    train = merged[merged['date_y'] < '2023-01-01']
    test = merged[merged['date_y'] >= '2023-01-01']
    
    def nvda_strategy(df):
        signals = df[df['return'] > 5.0]
        return pd.DataFrame({'return': signals['gap']})
    
    result = walk_forward_test('NVDA AI Theme', train, test, nvda_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

# H#006: IWM Lead-Lag
print('\nH#006: IWM → 0700.HK...')
if iwm is not None and hk is not None:
    iwm['next_date'] = pd.to_datetime(iwm['date']) + pd.Timedelta(days=1)
    merged = iwm.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    
    train = merged[merged['date_y'] < '2023-01-01']
    test = merged[merged['date_y'] >= '2023-01-01']
    
    def iwm_lag_strategy(df):
        signals = df[df['return'] > 2.0]
        return pd.DataFrame({'return': signals['gap']})
    
    result = walk_forward_test('IWM Lead-Lag', train, test, iwm_lag_strategy)
    all_results.append(result)
    print(f"   Train: {result['train_wr']:.1f}% ({result['train_trades']} trades)")
    print(f"   Test:  {result['test_wr']:.1f}% ({result['test_trades']} trades)")
    print(f"   Decay: {result['decay']:+.1f}% {result['status']}")

conn.close()

# ============================================
# FINAL SUMMARY
# ============================================
print('\n' + '='*80)
print('COMPREHENSIVE VALIDATION SUMMARY')
print('='*80)

results_df = pd.DataFrame(all_results)
results_df = results_df.sort_values('test_wr', ascending=False)

print('\n{:<25} {:<10} {:<10} {:<10} {:<10} {:<8}'.format(
    'Strategy', 'Train WR%', 'Test WR%', 'Decay%', 'Test Trades', 'Status'
))
print('-'*80)

for _, row in results_df.iterrows():
    print('{:<25} {:<10.1f} {:<10.1f} {:<10.1f} {:<10} {:<8}'.format(
        row['name'][:25], row['train_wr'], row['test_wr'], row['decay'], 
        row['test_trades'], row['status']
    ))

# Categorize
reliable = results_df[(results_df['test_wr'] >= 65) & (results_df['decay'] < 15)]
moderate = results_df[(results_df['test_wr'] >= 55) & ((results_df['test_wr'] < 65) | (results_df['decay'] >= 15))]
weak = results_df[results_df['test_wr'] < 55]

print('\n' + '='*80)
print('FINAL CLASSIFICATION (Out-of-Sample Performance)')
print('='*80)

print(f'\n✅ RELIABLE (Test >=65%, Decay <15%): {len(reliable)} strategies')
for _, row in reliable.iterrows():
    print(f'   - {row["name"]}: {row["test_wr"]:.1f}% test, {row["decay"]:.1f}% decay')

print(f'\n🟡 MODERATE (Test 55-65% OR high decay): {len(moderate)} strategies')
for _, row in moderate.iterrows():
    print(f'   - {row["name"]}: {row["test_wr"]:.1f}% test, {row["decay"]:.1f}% decay')

print(f'\n❌ WEAK (Test <55%): {len(weak)} strategies')
for _, row in weak.iterrows():
    print(f'   - {row["name"]}: {row["test_wr"]:.1f}% test, {row["decay"]:.1f}% decay')

print('\n' + '='*80)
print('KEY FINDINGS:')
print('='*80)
print('1. Train/Test split reveals true out-of-sample performance')
print('2. Decay >15% indicates overfitting to training period')
print('3. Test period (2023-2024) includes different market regimes')
print('4. Only strategies with Test >=65% AND Decay <15% are reliable')
print('='*80)
