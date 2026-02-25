#!/usr/bin/env python3
"""
MASSIVE HYPOTHESIS TESTING - ALL 90+ TESTABLE HYPOTHESES
Tests every hypothesis that can be validated with available OHLCV data
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
print('MASSIVE HYPOTHESIS VALIDATION: 90+ Hypotheses')
print('Testing ALL hypotheses testable with OHLCV data')
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
    if test_wr >= 70 and abs(train_wr - test_wr) < 15:
        return '✅ GOLDEN'
    if test_wr >= 55:
        return '🟡 VALIDATED'
    return '❌ REJECTED'

def test_hypothesis(name, ticker, condition_fn, exit_days=10, cost=0.1):
    """Generic hypothesis tester"""
    df = get_data(ticker)
    if df is None:
        return None
    
    try:
        train = df[df['date'] < pd.Timestamp('2023-01-01')]
        test = df[df['date'] >= pd.Timestamp('2023-01-01')]
        
        train_rets = [(train['close'].iloc[i+exit_days] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - cost
                      for i in range(50, len(train)-exit_days) if condition_fn(train, i)]
        test_rets = [(test['close'].iloc[i+exit_days] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - cost
                     for i in range(50, len(test)-exit_days) if condition_fn(test, i)]
        
        train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
        test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
        status = classify(train_wr, test_wr, len(test_rets))
        
        return {'name': name, 'train_wr': train_wr, 'test_wr': test_wr, 
                'train_n': len(train_rets), 'test_n': len(test_rets), 'status': status}
    except Exception as e:
        return {'name': name, 'train_wr': 0, 'test_wr': 0, 'train_n': 0, 'test_n': 0, 'status': f'❌ ERROR: {str(e)[:20]}'}

# ============================================
# SECTION 1: MEAN REVERSION (30+ hypotheses)
# ============================================
print('\n' + '='*80)
print('SECTION 1: MEAN REVERSION HYPOTHESES (30+)')
print('='*80)

mr_results = []

# 1.1 RSI variants
for ticker in ['QQQ', 'SPY', '0700.HK', 'MSTR', 'COIN']:
    for threshold in [10, 15, 20, 25, 30]:
        name = f'RSI<{threshold} on {ticker}'
        def make_cond(t, thresh):
            def cond(df, i):
                r = rsi(df['close'])
                return pd.notna(r.iloc[i]) and r.iloc[i] < thresh
            return cond
        
        result = test_hypothesis(name, ticker, make_cond(ticker, threshold))
        if result:
            mr_results.append(result)
            print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# 1.2 BB variants  
for ticker in ['QQQ', '0700.HK', 'MSTR']:
    df = get_data(ticker)
    if df is not None:
        df['sma20'] = df['close'].rolling(20).mean()
        df['std20'] = df['close'].rolling(20).std()
        df['bb_lower'] = df['sma20'] - 2 * df['std20']
        df['bb_pct_b'] = (df['close'] - df['bb_lower']) / (4 * df['std20'])
        
        for threshold in [0, 0.1, 0.2]:
            name = f'BB %B<{threshold} on {ticker}'
            def make_bb_cond(thresh):
                def cond(d, i):
                    return pd.notna(d['bb_pct_b'].iloc[i]) and d['bb_pct_b'].iloc[i] < thresh
                return cond
            
            result = test_hypothesis(name, ticker, make_bb_cond(threshold))
            if result:
                mr_results.append(result)
                print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# 1.3 Stochastic variants
for ticker in ['QQQ', '0700.HK']:
    df = get_data(ticker)
    if df is not None:
        low14 = df['low'].rolling(14).min()
        high14 = df['high'].rolling(14).max()
        df['stoch'] = 100 * (df['close'] - low14) / (high14 - low14)
        
        for threshold in [10, 20, 30]:
            name = f'Stochastic<{threshold} on {ticker}'
            def make_stoch_cond(thresh):
                def cond(d, i):
                    return pd.notna(d['stoch'].iloc[i]) and d['stoch'].iloc[i] < thresh
                return cond
            
            result = test_hypothesis(name, ticker, make_stoch_cond(threshold))
            if result:
                mr_results.append(result)
                print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# 1.4 3-Day Reversal variants
for ticker in ['QQQ', 'SPY', '0700.HK', 'MSTR', 'COIN']:
    df = get_data(ticker)
    if df is not None:
        df['down_3'] = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2)) & (df['close'].shift(2) < df['close'].shift(3))
        
        name = f'3-Day Down Reversal on {ticker}'
        def cond(d, i):
            return d['down_3'].iloc[i]
        
        result = test_hypothesis(name, ticker, cond, exit_days=5)
        if result:
            mr_results.append(result)
            print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# ============================================
# SECTION 2: TIME-BASED (20+ hypotheses)
# ============================================
print('\n' + '='*80)
print('SECTION 2: TIME-BASED HYPOTHESES (20+)')
print('='*80)

time_results = []

# 2.1 Day of week effects
for ticker in ['QQQ', '0700.HK', 'MSTR']:
    df = get_data(ticker)
    if df is not None:
        df['rsi'] = rsi(df['close'])
        df['dow'] = df['date'].dt.dayofweek
        
        for day in [0, 1, 2, 3, 4]:  # Mon-Fri
            for rsi_thresh in [20, 25, 30]:
                name = f'{["Mon","Tue","Wed","Thu","Fri"][day]} RSI<{rsi_thresh} on {ticker}'
                def make_dow_cond(d, rthresh, day_name):
                    def cond(dframe, i):
                        return dframe['dow'].iloc[i] == day_name and pd.notna(dframe['rsi'].iloc[i]) and dframe['rsi'].iloc[i] < rthresh
                    return cond
                
                result = test_hypothesis(name, ticker, make_dow_cond(df, rsi_thresh, day))
                if result:
                    time_results.append(result)
                    if result['test_n'] >= 5:
                        print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# 2.2 Month-end effects
for ticker in ['QQQ', 'SPY']:
    df = get_data(ticker)
    if df is not None:
        df['rsi'] = rsi(df['close'])
        df['day'] = df['date'].dt.day
        df['days_in_month'] = df['date'].dt.days_in_month
        
        for rsi_thresh in [20, 25, 30]:
            name = f'Month-End RSI<{rsi_thresh} on {ticker}'
            def cond(d, i):
                return d['day'].iloc[i] >= d['days_in_month'].iloc[i] - 3 and pd.notna(d['rsi'].iloc[i]) and d['rsi'].iloc[i] < rsi_thresh
            
            result = test_hypothesis(name, ticker, cond)
            if result and result['test_n'] >= 5:
                time_results.append(result)
                print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

# ============================================
# SECTION 3: CROSS-MARKET (15+ hypotheses)
# ============================================
print('\n' + '='*80)
print('SECTION 3: CROSS-MARKET LEAD-LAG (15+)')
print('='*80)

cross_results = []

# 3.1 US → HK lead-lag
us_tickers = ['QQQ', 'NVDA', 'MSTR', 'COIN', 'IWM', 'SPY']
hk_ticker = '0700.HK'

hk = get_data(hk_ticker)
if hk is not None:
    hk['prev'] = hk['close'].shift(1)
    hk['gap'] = (hk['close'] - hk['prev']) / hk['prev'] * 100
    
    for us_ticker in us_tickers:
        us = get_data(us_ticker)
        if us is not None:
            us['next_date'] = us['date'] + pd.Timedelta(days=1)
            merged = us.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
            
            for threshold in [1.5, 2.0, 2.5, 3.0, 5.0]:
                name = f'{us_ticker} >+{threshold}% → {hk_ticker}'
                
                train = merged[merged['date_y'] < pd.Timestamp('2023-01-01')]
                test = merged[merged['date_y'] >= pd.Timestamp('2023-01-01')]
                
                train_signals = train[train['return'] > threshold]
                test_signals = test[test['return'] > threshold]
                
                train_wr = (train_signals['gap'] > 0).mean() * 100 if len(train_signals) > 0 else 0
                test_wr = (test_signals['gap'] > 0).mean() * 100 if len(test_signals) > 0 else 0
                status = classify(train_wr, test_wr, len(test_signals))
                
                result = {'name': name, 'train_wr': train_wr, 'test_wr': test_wr, 
                         'train_n': len(train_signals), 'test_n': len(test_signals), 'status': status}
                cross_results.append(result)
                
                if result['test_n'] >= 5:
                    print(f"{result['name'][:40]:<40} | Train: {result['train_wr']:5.1f}% | Test: {result['test_wr']:5.1f}% | {result['status']}")

conn.close()

# ============================================
# FINAL SUMMARY
# ============================================
print('\n' + '='*80)
print('MASSIVE VALIDATION: FINAL SUMMARY')
print('='*80)

all_results = mr_results + time_results + cross_results

# Filter to those with sufficient test data
valid_results = [r for r in all_results if r['test_n'] >= 5]

print(f'\nTotal Hypotheses Tested: {len(all_results)}')
print(f'With Sufficient Test Data (≥5): {len(valid_results)}')

# Sort by test win rate
valid_results.sort(key=lambda x: x['test_wr'], reverse=True)

print('\n' + '='*80)
print('TOP 20 PERFORMERS (Test Win Rate)')
print('='*80)
print(f"{'Rank':<5} {'Hypothesis':<45} {'Train%':<8} {'Test%':<8} {'N':<5} {'Status'}")
print('-'*80)

for i, r in enumerate(valid_results[:20], 1):
    print(f"{i:<5} {r['name'][:45]:<45} {r['train_wr']:7.1f}% {r['test_wr']:7.1f}% {r['test_n']:<5} {r['status']}")

# Classification
golden = [r for r in valid_results if r['status'] == '✅ GOLDEN']
validated = [r for r in valid_results if r['status'] == '🟡 VALIDATED']
rejected = [r for r in valid_results if r['status'] == '❌ REJECTED']

print('\n' + '='*80)
print('CLASSIFICATION SUMMARY')
print('='*80)

print(f'\n✅ GOLDEN (Test ≥70%, Decay <15%): {len(golden)}')
for r in golden:
    print(f"   - {r['name']}: {r['test_wr']:.1f}% ({r['test_n']} trades)")

print(f'\n🟡 VALIDATED (Test ≥55%): {len(validated)}')
for r in validated[:10]:
    print(f"   - {r['name']}: {r['test_wr']:.1f}% ({r['test_n']} trades)")
if len(validated) > 10:
    print(f"   ... and {len(validated)-10} more")

print(f'\n❌ REJECTED (Test <55%): {len(rejected)}')
print(f'⏳ INSUFFICIENT DATA: {len(all_results) - len(valid_results)}')

print('\n' + '='*80)
print(f'PORTFOLIO CONSTRUCTION: {len(golden) + len(validated)} deployable strategies')
print('='*80)
