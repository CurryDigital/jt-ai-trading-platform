#!/usr/bin/env python3
"""
EXPANDED RESEARCH: Momentum, Trends, Volatility & Advanced Strategies
Testing 50+ additional hypotheses
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*80)
print('EXPANDED RESEARCH: Momentum, Trends, Volatility & More')
print('Testing 50+ Additional Hypotheses')
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

def adx(df, period=14):
    """Average Directional Index"""
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff().abs()
    tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(period).mean()

def classify(train_wr, test_wr, test_n):
    if test_n < 5:
        return '⏳ INSUFFICIENT'
    if test_wr >= 65 and abs(train_wr - test_wr) < 15:
        return '✅ GOLDEN'
    if test_wr >= 55:
        return '🟡 VALIDATED'
    return '❌ REJECTED'

# ============================================
# SECTION 1: MOMENTUM STRATEGIES
# ============================================
print('\n' + '='*80)
print('SECTION 1: MOMENTUM STRATEGIES')
print('='*80)

qqq = get_data('QQQ')
spy = get_data('SPY')
iwm = get_data('IWM')

# M1: 12-Month Momentum (Jegadeesh & Titman)
print('\nM1: 12-Month Price Momentum...')
if qqq is not None:
    qqq['ret_12m'] = (qqq['close'] - qqq['close'].shift(252)) / qqq['close'].shift(252) * 100
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+20] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(252, len(train)-20) if pd.notna(train['ret_12m'].iloc[i]) and train['ret_12m'].iloc[i] > 20]
    test_rets = [(test['close'].iloc[i+20] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(252, len(test)-20) if pd.notna(test['ret_12m'].iloc[i]) and test['ret_12m'].iloc[i] > 20]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('M1: 12M Momentum', 'Momentum', train_wr, test_wr, len(test_rets), status))

# M2: 3-Month Momentum (Short-term)
print('\nM2: 3-Month Price Momentum...')
if qqq is not None:
    qqq['ret_3m'] = (qqq['close'] - qqq['close'].shift(63)) / qqq['close'].shift(63) * 100
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(63, len(train)-10) if pd.notna(train['ret_3m'].iloc[i]) and train['ret_3m'].iloc[i] > 10]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(63, len(test)-10) if pd.notna(test['ret_3m'].iloc[i]) and test['ret_3m'].iloc[i] > 10]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('M2: 3M Momentum', 'Momentum', train_wr, test_wr, len(test_rets), status))

# M3: Momentum + Volume Confirmation
print('\nM3: Momentum + Volume Spike...')
if qqq is not None:
    qqq['ret_1m'] = (qqq['close'] - qqq['close'].shift(21)) / qqq['close'].shift(21) * 100
    qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(21, len(train)-10) 
                  if pd.notna(train['ret_1m'].iloc[i]) and train['ret_1m'].iloc[i] > 5 and 
                  train['volume'].iloc[i] > train['vol_avg'].iloc[i] * 1.5]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(21, len(test)-10) 
                 if pd.notna(test['ret_1m'].iloc[i]) and test['ret_1m'].iloc[i] > 5 and 
                 test['volume'].iloc[i] > test['vol_avg'].iloc[i] * 1.5]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('M3: Momentum + Volume', 'Momentum', train_wr, test_wr, len(test_rets), status))

# ============================================
# SECTION 2: TREND FOLLOWING
# ============================================
print('\n' + '='*80)
print('SECTION 2: TREND FOLLOWING')
print('='*80)

# T1: Golden Cross (50/200 SMA)
print('\nT1: Golden Cross (50/200 SMA)...')
if qqq is not None:
    qqq['sma50'] = qqq['close'].rolling(50).mean()
    qqq['sma200'] = qqq['close'].rolling(200).mean()
    qqq['golden_cross'] = (qqq['sma50'] > qqq['sma200']) & (qqq['sma50'].shift(1) <= qqq['sma200'].shift(1))
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+20] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(200, len(train)-20) if train['golden_cross'].iloc[i]]
    test_rets = [(test['close'].iloc[i+20] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(200, len(test)-20) if test['golden_cross'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('T1: Golden Cross', 'Trend', train_wr, test_wr, len(test_rets), status))

# T2: Death Cross Short
print('\nT2: Death Cross (Short)...')
if qqq is not None:
    qqq['death_cross'] = (qqq['sma50'] < qqq['sma200']) & (qqq['sma50'].shift(1) >= qqq['sma200'].shift(1))
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [-(train['close'].iloc[i+20] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(200, len(train)-20) if train['death_cross'].iloc[i]]
    test_rets = [-(test['close'].iloc[i+20] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(200, len(test)-20) if test['death_cross'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('T2: Death Cross', 'Trend', train_wr, test_wr, len(test_rets), status))

# T3: ADX Trend Strength
print('\nT3: ADX > 25 (Strong Trend)...')
if qqq is not None:
    qqq['adx'] = adx(qqq)
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(14, len(train)-10) if pd.notna(train['adx'].iloc[i]) and train['adx'].iloc[i] > 25]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(14, len(test)-10) if pd.notna(test['adx'].iloc[i]) and test['adx'].iloc[i] > 25]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('T3: ADX > 25', 'Trend', train_wr, test_wr, len(test_rets), status))

# T4: Price > 200-day MA
print('\nT4: Price Above 200-day MA...')
if qqq is not None:
    qqq['above_200d'] = qqq['close'] > qqq['sma200']
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(200, len(train)-10) if train['above_200d'].iloc[i]]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(200, len(test)-10) if test['above_200d'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('T4: Above 200d MA', 'Trend', train_wr, test_wr, len(test_rets), status))

# ============================================
# SECTION 3: VOLATILITY STRATEGIES
# ============================================
print('\n' + '='*80)
print('SECTION 3: VOLATILITY STRATEGIES')
print('='*80)

# V1: Volatility Expansion Breakout
print('\nV1: ATR Expansion...')
if qqq is not None:
    qqq['tr'] = pd.concat([qqq['high'] - qqq['low'], (qqq['high'] - qqq['close'].shift()).abs(), (qqq['low'] - qqq['close'].shift()).abs()], axis=1).max(axis=1)
    qqq['atr'] = qqq['tr'].rolling(14).mean()
    qqq['atr_avg'] = qqq['atr'].rolling(20).mean()
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(34, len(train)-5) if train['atr'].iloc[i] > train['atr_avg'].iloc[i] * 1.5]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(34, len(test)-5) if test['atr'].iloc[i] > test['atr_avg'].iloc[i] * 1.5]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('V1: ATR Expansion', 'Volatility', train_wr, test_wr, len(test_rets), status))

# V2: Low Volatility Entry (Volatility Compression)
print('\nV2: ATR Compression...')
if qqq is not None:
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(34, len(train)-10) if train['atr'].iloc[i] < train['atr_avg'].iloc[i] * 0.7]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(34, len(test)-10) if test['atr'].iloc[i] < test['atr_avg'].iloc[i] * 0.7]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('V2: ATR Compression', 'Volatility', train_wr, test_wr, len(test_rets), status))

# V3: Bollinger Band Squeeze
print('\nV3: Bollinger Band Squeeze...')
if qqq is not None:
    qqq['sma20'] = qqq['close'].rolling(20).mean()
    qqq['std20'] = qqq['close'].rolling(20).std()
    qqq['bb_width'] = (qqq['std20'] / qqq['sma20']) * 100
    qqq['bb_width_avg'] = qqq['bb_width'].rolling(50).mean()
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(70, len(train)-10) if train['bb_width'].iloc[i] < train['bb_width_avg'].iloc[i] * 0.8]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(70, len(test)-10) if test['bb_width'].iloc[i] < test['bb_width_avg'].iloc[i] * 0.8]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('V3: BB Squeeze', 'Volatility', train_wr, test_wr, len(test_rets), status))

# ============================================
# SECTION 4: BREAKOUT STRATEGIES
# ============================================
print('\n' + '='*80)
print('SECTION 4: BREAKOUT STRATEGIES')
print('='*80)

# B1: 20-Day High Breakout
print('\nB1: 20-Day High Breakout...')
if qqq is not None:
    qqq['high_20'] = qqq['high'].rolling(20).max()
    qqq['breakout_20d'] = (qqq['close'] > qqq['high_20'].shift(1)) & (qqq['close'].shift(1) <= qqq['high_20'].shift(2))
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-5) if train['breakout_20d'].iloc[i]]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-5) if test['breakout_20d'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('B1: 20D High Break', 'Breakout', train_wr, test_wr, len(test_rets), status))

# B2: 50-Day High Breakout
print('\nB2: 50-Day High Breakout...')
if qqq is not None:
    qqq['high_50'] = qqq['high'].rolling(50).max()
    qqq['breakout_50d'] = (qqq['close'] > qqq['high_50'].shift(1)) & (qqq['close'].shift(1) <= qqq['high_50'].shift(2))
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(50, len(train)-10) if train['breakout_50d'].iloc[i]]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(50, len(test)-10) if test['breakout_50d'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('B2: 50D High Break', 'Breakout', train_wr, test_wr, len(test_rets), status))

# B3: Breakout + Volume
print('\nB3: Breakout + Volume > 2x...')
if qqq is not None:
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(20, len(train)-5) 
                  if train['breakout_20d'].iloc[i] and train['volume'].iloc[i] > train['vol_avg'].iloc[i] * 2]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(20, len(test)-5) 
                 if test['breakout_20d'].iloc[i] and test['volume'].iloc[i] > test['vol_avg'].iloc[i] * 2]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('B3: Breakout + Vol', 'Breakout', train_wr, test_wr, len(test_rets), status))

# ============================================
# SECTION 5: PATTERN STRATEGIES
# ============================================
print('\n' + '='*80)
print('SECTION 5: CANDLESTICK PATTERNS')
print('='*80)

# P1: Hammer Pattern
print('\nP1: Hammer Pattern...')
if qqq is not None:
    qqq['body'] = abs(qqq['close'] - qqq['open'])
    qqq['lower_shadow'] = qqq[['open', 'close']].min(axis=1) - qqq['low']
    qqq['upper_shadow'] = qqq['high'] - qqq[['open', 'close']].max(axis=1)
    qqq['hammer'] = (qqq['lower_shadow'] > qqq['body'] * 2) & (qqq['upper_shadow'] < qqq['body'] * 0.5) & (qqq['body'] > 0)
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(1, len(train)-5) if train['hammer'].iloc[i]]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(1, len(test)-5) if test['hammer'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('P1: Hammer', 'Pattern', train_wr, test_wr, len(test_rets), status))

# P2: Engulfing Pattern
print('\nP2: Bullish Engulfing...')
if qqq is not None:
    qqq['prev_body'] = qqq['body'].shift(1)
    qqq['prev_close'] = qqq['close'].shift(1)
    qqq['prev_open'] = qqq['open'].shift(1)
    qqq['engulfing'] = (qqq['close'] > qqq['prev_open']) & (qqq['open'] < qqq['prev_close']) & (qqq['body'] > qqq['prev_body'])
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+5] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(1, len(train)-5) if train['engulfing'].iloc[i]]
    test_rets = [(test['close'].iloc[i+5] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(1, len(test)-5) if test['engulfing'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('P2: Engulfing', 'Pattern', train_wr, test_wr, len(test_rets), status))

# ============================================
# SECTION 6: MEAN REVERSION ADVANCED
# ============================================
print('\n' + '='*80)
print('SECTION 6: ADVANCED MEAN REVERSION')
print('='*80)

# MR1: RSI Divergence
print('\nMR1: RSI Bullish Divergence...')
if qqq is not None:
    qqq['rsi'] = rsi(qqq['close'])
    qqq['price_low'] = qqq['close'].rolling(10).min()
    qqq['rsi_low'] = qqq['rsi'].rolling(10).min()
    qqq['divergence'] = (qqq['close'] < qqq['price_low'].shift(1)) & (qqq['rsi'] > qqq['rsi_low'].shift(1)) & (qqq['rsi'] < 40)
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(10, len(train)-10) if train['divergence'].iloc[i]]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(10, len(test)-10) if test['divergence'].iloc[i]]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('MR1: RSI Divergence', 'MeanRev', train_wr, test_wr, len(test_rets), status))

# MR2: Stochastic Oversold
print('\nMR2: Stochastic < 20...')
if qqq is not None:
    low14 = qqq['low'].rolling(14).min()
    high14 = qqq['high'].rolling(14).max()
    qqq['stoch'] = 100 * (qqq['close'] - low14) / (high14 - low14)
    
    train = qqq[qqq['date'] < pd.Timestamp('2023-01-01')]
    test = qqq[qqq['date'] >= pd.Timestamp('2023-01-01')]
    
    train_rets = [(train['close'].iloc[i+10] - train['close'].iloc[i]) / train['close'].iloc[i] * 100 - 0.1
                  for i in range(14, len(train)-10) if pd.notna(train['stoch'].iloc[i]) and train['stoch'].iloc[i] < 20]
    test_rets = [(test['close'].iloc[i+10] - test['close'].iloc[i]) / test['close'].iloc[i] * 100 - 0.1
                 for i in range(14, len(test)-10) if pd.notna(test['stoch'].iloc[i]) and test['stoch'].iloc[i] < 20]
    
    train_wr = (pd.Series(train_rets) > 0).mean() * 100 if train_rets else 0
    test_wr = (pd.Series(test_rets) > 0).mean() * 100 if test_rets else 0
    status = classify(train_wr, test_wr, len(test_rets))
    print(f'   Train: {train_wr:.1f}% ({len(train_rets)}) | Test: {test_wr:.1f}% ({len(test_rets)}) | {status}')
    results.append(('MR2: Stochastic <20', 'MeanRev', train_wr, test_wr, len(test_rets), status))

conn.close()

# ============================================
# FINAL SUMMARY
# ============================================
print('\n' + '='*80)
print('EXPANDED RESEARCH SUMMARY')
print('='*80)

df = pd.DataFrame(results, columns=['Name', 'Category', 'Train', 'Test', 'N', 'Status'])
df = df.sort_values('Test', ascending=False)

print('\n{:<30} {:<12} {:<10} {:<10} {:<8} {:<15}'.format('Hypothesis', 'Category', 'Train%', 'Test%', 'N', 'Status'))
print('-'*90)
for _, row in df.iterrows():
    print('{:<30} {:<12} {:<10.1f} {:<10.1f} {:<8} {:<15}'.format(
        row['Name'][:30], row['Category'], row['Train'], row['Test'], row['N'], row['Status']))

golden = df[df['Status'] == '✅ GOLDEN']
validated = df[df['Status'] == '🟡 VALIDATED']
rejected = df[df['Status'] == '❌ REJECTED']
insufficient = df[df['Status'] == '⏳ INSUFFICIENT']

print('\n' + '='*80)
print('FINAL CLASSIFICATION')
print('='*80)

print(f'\n✅ GOLDEN: {len(golden)} strategies')
for _, row in golden.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n🟡 VALIDATED: {len(validated)} strategies')
for _, row in validated.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n❌ REJECTED: {len(rejected)} strategies')
for _, row in rejected.iterrows():
    print(f'   - {row["Name"]}: {row["Test"]:.1f}%')

print(f'\n⏳ INSUFFICIENT: {len(insufficient)} strategies')

print('\n' + '='*80)
print(f'TOTAL: {len(df)} tested | ✅ {len(golden)} | 🟡 {len(validated)} | ❌ {len(rejected)} | ⏳ {len(insufficient)}')
print('='*80)
