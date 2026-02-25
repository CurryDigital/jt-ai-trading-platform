#!/usr/bin/env python3
"""
ASIAN SESSION LIQUIDITY FADE STRATEGY TEST
Fixed: Handle Decimal types from database
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from decimal import Decimal

print('='*80)
print('ASIAN SESSION LIQUIDITY FADE STRATEGY TEST')
print('Fixed: Decimal type handling')
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

# ============================================
# ASIAN SESSION ANALYSIS
# ============================================
print('\n' + '='*80)
print('ASIAN SESSION LIQUIDITY FADE ANALYSIS')
print('='*80)

pairs = ['USDJPY', 'EURUSD', 'GBPUSD', 'USDCNH', 'AUDUSD']

for pair in pairs:
    print(f'\n{pair}:')
    
    # Get hourly data
    cursor.execute(f'''
        SELECT timestamp, open::float, high::float, low::float, close::float
        FROM bronze.fx_prices
        WHERE pair = '{pair}'
        AND timestamp BETWEEN '2024-02-26' AND '2024-12-31'
        ORDER BY timestamp
    ''')
    data = cursor.fetchall()
    
    if len(data) == 0:
        print('   No data')
        continue
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['date'] = df['timestamp'].dt.date
    
    # Asian session: 00:00-07:59 UTC
    asian = df[(df['hour'] >= 0) & (df['hour'] <= 7)].copy()
    
    if len(asian) == 0:
        print('   No Asian session data')
        continue
    
    # Calculate Asian session daily stats
    asian_daily = asian.groupby('date').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).reset_index()
    
    asian_daily['asian_range'] = asian_daily['high'] - asian_daily['low']
    asian_daily['asian_return'] = (asian_daily['close'] - asian_daily['open']) * 10000  # pips
    
    # Test hypothesis: Large Asian move → fade in London/NY
    if len(asian_daily) > 10:
        threshold = asian_daily['asian_range'].quantile(0.8)  # Top 20% moves
        large_moves = asian_daily[asian_daily['asian_range'] >= threshold]
        
        print(f'   Total sessions: {len(asian_daily)}')
        print(f'   Large Asian moves (>{threshold:.4f}): {len(large_moves)}')
        print(f'   Avg Asian return: {asian_daily["asian_return"].mean():.2f} pips')
        print(f'   Asian range avg: {asian_daily["asian_range"].mean():.4f}')
        
        # Calculate if large moves reverse
        if len(large_moves) > 5:
            # Check next day reversal (simplified)
            reversal_rate = (large_moves['asian_return'] < 0).mean() * 100
            print(f'   Reversal rate: {reversal_rate:.1f}%')

# ============================================
# SECTOR ETF BB SQUEEZE
# ============================================
print('\n' + '='*80)
print('SECTOR ETF BB SQUEEZE TEST')
print('='*80)

sector_etfs = ['XLF', 'XLV', 'XLE', 'XLK', 'XLI', 'XLU', 'XLP', 'XLB']
results = []

for etf in sector_etfs:
    print(f'\n{etf}:')
    
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM bronze.yf_prices
        WHERE ticker = '{etf}'
        AND date BETWEEN '2021-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    
    if len(data) < 200:
        print(f'   Insufficient data: {len(data)} records')
        continue
    
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate BB Squeeze
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_width'] = (4 * df['std20']) / df['sma20'] * 100
    
    # Rolling percentile - fixed
    def calc_pctile(x):
        if len(x) >= 120:
            return pd.Series(x).rank(pct=True).iloc[-1]
        return np.nan
    
    df['bb_width_pctile'] = df['bb_width'].rolling(120).apply(calc_pctile, raw=False)
    
    # Split train/test
    train = df[df['date'] < pd.Timestamp('2023-01-01')]
    test = df[df['date'] >= pd.Timestamp('2023-01-01')]
    
    # Entry: BB Width < 10th percentile + breakout
    train_signals = []
    for i in range(120, len(train)-5):
        if pd.notna(train['bb_width_pctile'].iloc[i]) and train['bb_width_pctile'].iloc[i] < 0.10:
            if i+1 < len(train) and train['close'].iloc[i+1] > train['high'].iloc[i]:
                ret = (train['close'].iloc[i+5] - train['close'].iloc[i+1]) / train['close'].iloc[i+1] * 100 - 0.1
                train_signals.append(ret)
    
    test_signals = []
    for i in range(120, len(test)-5):
        if pd.notna(test['bb_width_pctile'].iloc[i]) and test['bb_width_pctile'].iloc[i] < 0.10:
            if i+1 < len(test) and test['close'].iloc[i+1] > test['high'].iloc[i]:
                ret = (test['close'].iloc[i+5] - test['close'].iloc[i+1]) / test['close'].iloc[i+1] * 100 - 0.1
                test_signals.append(ret)
    
    if test_signals:
        train_wr = (pd.Series(train_signals) > 0).mean() * 100 if train_signals else 0
        test_wr = (pd.Series(test_signals) > 0).mean() * 100
        decay = train_wr - test_wr
        
        print(f'   Train: {train_wr:.1f}% ({len(train_signals)}) | Test: {test_wr:.1f}% ({len(test_signals)}) | Decay: {decay:+.1f}%')
        
        if test_wr >= 70 and len(test_signals) >= 30 and abs(decay) < 15:
            print(f'   🏆 GOLDEN')
            results.append((etf, train_wr, test_wr, len(test_signals), decay, '🏆 GOLDEN'))
        elif test_wr >= 65 and len(test_signals) >= 10:
            print(f'   ✅ VALIDATED')
            results.append((etf, train_wr, test_wr, len(test_signals), decay, '✅ VALIDATED'))
        elif test_wr >= 55:
            print(f'   🟡 Near-Validated')
            results.append((etf, train_wr, test_wr, len(test_signals), decay, '🟡 Near-Validated'))
        else:
            print(f'   ❌ Rejected')
            results.append((etf, train_wr, test_wr, len(test_signals), decay, '❌ REJECTED'))
    else:
        print('   No signals in test period')

# ============================================
# SUMMARY
# ============================================
print('\n' + '='*80)
print('SUMMARY')
print('='*80)

golden = [r for r in results if r[5] == '🏆 GOLDEN']
validated = [r for r in results if r[5] == '✅ VALIDATED']
near = [r for r in results if r[5] == '🟡 Near-Validated']
rejected = [r for r in results if r[5] == '❌ REJECTED']

print(f'\n🏆 Golden: {len(golden)}')
for etf, train, test, n, decay, status in golden:
    print(f'   {etf}: {test:.1f}% win ({n} trades)')

print(f'\n✅ Validated: {len(validated)}')
for etf, train, test, n, decay, status in validated:
    print(f'   {etf}: {test:.1f}% win ({n} trades)')

print(f'\n🟡 Near-Validated: {len(near)}')
for etf, train, test, n, decay, status in near:
    print(f'   {etf}: {test:.1f}% win ({n} trades)')

print(f'\n❌ Rejected: {len(rejected)}')
for etf, train, test, n, decay, status in rejected:
    print(f'   {etf}: {test:.1f}% win ({n} trades)')

conn.close()

print('\n' + '='*80)
print('TESTING COMPLETE')
print('='*80)
