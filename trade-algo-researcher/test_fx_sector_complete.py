#!/usr/bin/env python3
"""
ASIAN SESSION LIQUIDITY FADE STRATEGY TEST
Using bronze.fx_prices (REQUEST_003 data)
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
print('ASIAN SESSION LIQUIDITY FADE STRATEGY TEST')
print('Data: bronze.fx_prices (36,843 hourly records)')
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
        SELECT timestamp, open, high, low, close
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
    asian = df[(df['hour'] >= 0) & (df['hour'] <= 7)]
    london = df[(df['hour'] >= 8) & (df['hour'] <= 15)]  # London session
    ny = df[(df['hour'] >= 13) & (df['hour'] <= 20)]  # NY session (overlap)
    
    if len(asian) > 0:
        # Calculate Asian session move
        asian_daily = asian.groupby('date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).reset_index()
        
        asian_daily['asian_range'] = asian_daily['high'] - asian_daily['low']
        asian_daily['asian_return'] = (asian_daily['close'] - asian_daily['open']) * 10000  # pips
        
        # Test hypothesis: Large Asian move → fade in London/NY
        threshold = asian_daily['asian_range'].quantile(0.8)  # Top 20% moves
        
        large_moves = asian_daily[asian_daily['asian_range'] >= threshold]
        
        print(f'   Total sessions: {len(asian_daily)}')
        print(f'   Large Asian moves (>{threshold:.4f}): {len(large_moves)}')
        print(f'   Avg Asian return: {asian_daily["asian_return"].mean():.2f} pips')
        print(f'   Asian range avg: {asian_daily["asian_range"].mean():.4f}')

# ============================================
# SECTOR ETF BB SQUEEZE (from bronze.yf_prices)
# ============================================
print('\n' + '='*80)
print('SECTOR ETF BB SQUEEZE TEST')
print('Data: bronze.yf_prices (REQUEST_006 data)')
print('='*80)

sector_etfs = ['XLF', 'XLV', 'XLE', 'XLK', 'XLI', 'XLU', 'XLP', 'XLB']

for etf in sector_etfs:
    print(f'\n{etf}:')
    
    cursor.execute(f'''
        SELECT date, open, high, low, close, volume
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
    df['bb_width_pctile'] = df['bb_width'].rolling(120).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) >= 120 else np.nan)
    
    # Split train/test
    train = df[df['date'] < pd.Timestamp('2023-01-01')]
    test = df[df['date'] >= pd.Timestamp('2023-01-01')]
    
    # Entry: BB Width < 10th percentile + breakout
    test_signals = []
    for i in range(120, len(test)-5):
        if pd.notna(test['bb_width_pctile'].iloc[i]) and test['bb_width_pctile'].iloc[i] < 0.10:
            if i+1 < len(test) and test['close'].iloc[i+1] > test['high'].iloc[i]:
                ret = (test['close'].iloc[i+5] - test['close'].iloc[i+1]) / test['close'].iloc[i+1] * 100 - 0.1
                test_signals.append(ret)
    
    if test_signals:
        test_wr = (pd.Series(test_signals) > 0).mean() * 100
        print(f'   Test: {test_wr:.1f}% ({len(test_signals)} trades)')
        
        if test_wr >= 65 and len(test_signals) >= 10:
            print(f'   ✅ VALIDATED')
        elif test_wr >= 55:
            print(f'   🟡 Near-Validated')
        else:
            print(f'   ❌ Rejected')
    else:
        print('   No signals in test period')

conn.close()

print('\n' + '='*80)
print('TESTING COMPLETE')
print('='*80)
