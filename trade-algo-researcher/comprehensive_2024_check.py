#!/usr/bin/env python3
"""
COMPREHENSIVE PORTFOLIO RE-CHECK
Test ALL strategies with 2024-only data for current accuracy
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
print('COMPREHENSIVE PORTFOLIO RE-CHECK (2024 DATA ONLY)')
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

# Use ONLY 2024 data for realistic current performance
START_DATE = '2024-01-01'
END_DATE = '2024-12-31'

results = []

def get_data(ticker):
    """Get 2024-only data"""
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '{START_DATE}' AND '{END_DATE}'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) == 0:
        return None
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['return'] = df['close'].pct_change() * 100
    return df

def calculate_rsi(df, period=14):
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

print(f'\\nTesting period: {START_DATE} to {END_DATE}')
print('This shows CURRENT performance (not historical backtest)\\n')

# ============================================
# GOLDEN STRATEGIES
# ============================================

print('='*70)
print('GOLDEN STRATEGIES (2024 DATA)')
print('='*70)

# 1. BB+Monday GOLD
print('\\n1. BB+Monday GOLD (0700.HK)...')
bb = get_data('0700.HK')
if bb is not None:
    # Calculate BB
    bb['sma20'] = bb['close'].rolling(20).mean()
    bb['std20'] = bb['close'].rolling(20).std()
    bb['bb_lower'] = bb['sma20'] - (2 * bb['std20'])
    bb['rsi'] = calculate_rsi(bb)
    bb['vol_avg'] = bb['volume'].rolling(20).mean()
    bb['day_of_week'] = pd.to_datetime(bb['date']).dt.dayofweek
    
    trades = []
    for i in range(20, len(bb) - 10):
        if (bb['close'].iloc[i] < bb['bb_lower'].iloc[i] and 
            bb['rsi'].iloc[i] < 20 and 
            bb['volume'].iloc[i] > bb['vol_avg'].iloc[i] * 1.5 and
            bb['day_of_week'].iloc[i] == 0):  # Monday
            
            entry = bb['close'].iloc[i]
            exit_p = bb['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if trades:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        print(f'   Trades: {len(trades)}, Win%: {wr:.1f}%, Avg: {r.mean():.2f}%')
        results.append(('BB+Monday GOLD', 'Golden', len(trades), wr, r.mean(), '✅' if wr >=70 else '🟡'))
    else:
        print('   No trades in 2024')
        results.append(('BB+Monday GOLD', 'Golden', 0, 0, 0, '⚠️'))

# 2. Inside Day Breakout
print('\\n2. Inside Day Breakout (QQQ)...')
qqq = get_data('QQQ')
if qqq is not None:
    qqq['prev_high'] = qqq['high'].shift(1)
    qqq['prev_low'] = qqq['low'].shift(1)
    qqq['inside_day'] = (qqq['high'] < qqq['prev_high']) & (qqq['low'] > qqq['prev_low'])
    qqq['vol_avg'] = qqq['volume'].rolling(20).mean()
    
    trades = []
    for i in range(1, len(qqq) - 5):
        if qqq['inside_day'].iloc[i] and qqq['volume'].iloc[i] > qqq['vol_avg'].iloc[i] * 2:
            entry = qqq['close'].iloc[i]
            exit_p = qqq['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if trades:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        print(f'   Trades: {len(trades)}, Win%: {wr:.1f}%, Avg: {r.mean():.2f}%')
        results.append(('Inside Day', 'Golden', len(trades), wr, r.mean(), '✅' if wr >=70 else '🟡'))
    else:
        print('   No trades in 2024')

# 3. COIN Strong Uptrend
print('\\n3. COIN Strong Uptrend...')
coin = get_data('COIN')
spy = get_data('SPY')
if coin is not None and spy is not None:
    coin['rsi'] = calculate_rsi(coin)
    spy['sma50'] = spy['close'].rolling(50).mean()
    spy['sma200'] = spy['close'].rolling(200).mean()
    spy['golden_cross'] = spy['sma50'] > spy['sma200']
    
    merged = coin.merge(spy[['date', 'golden_cross']], on='date', how='inner')
    
    trades = []
    for i in range(20, len(merged) - 10):
        if merged['rsi'].iloc[i] < 25 and merged['golden_cross'].iloc[i]:
            entry = merged['close'].iloc[i]
            exit_p = merged['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if trades:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        print(f'   Trades: {len(trades)}, Win%: {wr:.1f}%, Avg: {r.mean():.2f}%')
        results.append(('COIN Strong Uptrend', 'Golden', len(trades), wr, r.mean(), '✅' if wr >=70 else '🟡'))
    else:
        print('   No trades in 2024')

# 4. MSTR SPY Regime
print('\\n4. MSTR SPY Regime...')
mstr = get_data('MSTR')
if mstr is not None and spy is not None:
    mstr['rsi'] = calculate_rsi(mstr)
    spy['above_50d'] = spy['close'] > spy['close'].rolling(50).mean()
    
    merged = mstr.merge(spy[['date', 'above_50d']], on='date', how='inner')
    
    trades = []
    for i in range(20, len(merged) - 10):
        if merged['rsi'].iloc[i] < 25 and merged['above_50d'].iloc[i]:
            entry = merged['close'].iloc[i]
            exit_p = merged['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if trades:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        print(f'   Trades: {len(trades)}, Win%: {wr:.1f}%, Avg: {r.mean():.2f}%')
        results.append(('MSTR SPY Regime', 'Golden', len(trades), wr, r.mean(), '✅' if wr >=70 else '🟡'))
    else:
        print('   No trades in 2024')

# ============================================
# CROSS-MARKET STRATEGIES
# ============================================

print('\\n' + '='*70)
print('CROSS-MARKET STRATEGIES (2024 DATA)')
print('='*70)

# 5. QQQ Lead-Lag
print('\\n5. QQQ Lead-Lag → 0700.HK...')
if qqq is not None and bb is not None:
    bb['prev_close'] = bb['close'].shift(1)
    bb['overnight_gap'] = (bb['open'] - bb['prev_close']) / bb['prev_close'] * 100
    
    qqq['next_date'] = pd.to_datetime(qqq['date']) + pd.Timedelta(days=1)
    bb['date'] = pd.to_datetime(bb['date'])
    merged = qqq.merge(bb[['date', 'overnight_gap']], left_on='next_date', right_on='date', how='inner')
    
    signals = merged[merged['return'] > 2.0]
    if len(signals) > 0:
        wr = (signals['overnight_gap'] > 0).mean() * 100
        print(f'   Signals: {len(signals)}, Win%: {wr:.1f}%, Avg Gap: {signals["overnight_gap"].mean():.2f}%')
        results.append(('QQQ Lead-Lag', 'Cross-Market', len(signals), wr, signals['overnight_gap'].mean(), '✅' if wr >=60 else '🟡'))
    else:
        print('   No signals in 2024')

# 6. NVDA AI Theme
print('\\n6. NVDA AI Theme → 0700.HK...')
nvda = get_data('NVDA')
if nvda is not None and bb is not None:
    nvda['next_date'] = pd.to_datetime(nvda['date']) + pd.Timedelta(days=1)
    merged = nvda.merge(bb[['date', 'overnight_gap']], left_on='next_date', right_on='date', how='inner')
    
    signals = merged[merged['return'] > 5.0]
    if len(signals) > 0:
        wr = (signals['overnight_gap'] > 0).mean() * 100
        print(f'   Signals: {len(signals)}, Win%: {wr:.1f}%, Avg Gap: {signals["overnight_gap"].mean():.2f}%')
        results.append(('NVDA AI Theme', 'Cross-Market', len(signals), wr, signals['overnight_gap'].mean(), '✅' if wr >=60 else '🟡'))
    else:
        print('   No signals in 2024')

conn.close()

# ============================================
# SUMMARY
# ============================================
print('\\n' + '='*70)
print('2024 PERFORMANCE SUMMARY')
print('='*70)

results_df = pd.DataFrame(results, columns=['Strategy', 'Category', 'Trades', 'Win%', 'Avg_Return', 'Status'])
results_df = results_df.sort_values('Win%', ascending=False)

print('\\n{:<25} {:<12} {:<8} {:<10} {:<12} {:<8}'.format(
    'Strategy', 'Category', 'Trades', 'Win%', 'Avg Return', 'Status'
))
print('-'*75)

for _, row in results_df.iterrows():
    print('{:<25} {:<12} {:<8} {:<10.1f} {:<12.2f} {:<8}'.format(
        row['Strategy'][:25], row['Category'], row['Trades'], row['Win%'], row['Avg_Return'], row['Status']
    ))

# Categorize
reliable = results_df[results_df['Win%'] >= 70]
moderate = results_df[(results_df['Win%'] >= 55) & (results_df['Win%'] < 70)]
weak = results_df[results_df['Win%'] < 55]

print('\\n' + '='*70)
print('CURRENT STATUS (2024 DATA)')
print('='*70)

print(f'\\n✅ RELIABLE (70%+ win): {len(reliable)} strategies')
for _, row in reliable.iterrows():
    print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

print(f'\\n🟡 MODERATE (55-70% win): {len(moderate)} strategies')
for _, row in moderate.iterrows():
    print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

if len(weak) > 0:
    print(f'\\n❌ WEAK (<55% win): {len(weak)} strategies')
    for _, row in weak.iterrows():
        print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

print('\\n' + '='*70)
print('⚠️  IMPORTANT: 2024 = Different market regime than 2022-2023')
print('   - Higher volatility')
print('   - Different macro conditions')
print('   - Strategy decay possible')
print('='*70)
