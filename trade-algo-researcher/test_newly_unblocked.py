#!/usr/bin/env python3
"""
TESTING NEWLY UNBLOCKED HYPOTHESES
Data: REQUEST_003 (FX), REQUEST_006 (Sector ETFs), REQUEST_007 (Individual Stocks)
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
print('TESTING NEWLY UNBLOCKED HYPOTHESES')
print('Data: FX Hourly, Sector ETFs, Individual Stocks')
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

def get_data(ticker, start='2021-01-01', end='2024-12-31'):
    """Get daily price data"""
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
    df['date'] = pd.to_datetime(df['date'])
    df['return'] = df['close'].pct_change() * 100
    return df

def classify(train_wr, test_wr, test_n, decay):
    if test_n < 30:
        return '⏳ INSUFFICIENT'
    if test_wr >= 70 and abs(decay) < 15:
        return '🏆 GOLDEN'
    if test_wr >= 55 and abs(decay) < 20:
        return '✅ VALIDATED'
    return '❌ REJECTED'

# ============================================
# TEST 1: BB SQUEEZE ON SECTOR ETFs
# ============================================
print('\n' + '='*80)
print('TEST 1: BB SQUEEZE ON SECTOR ETFs')
print('='*80)

sector_etfs = ['XLF', 'XLV', 'XLE', 'XLK', 'XLI', 'XLU', 'XLP', 'XLB']

for etf in sector_etfs:
    print(f'\n{etf}:')
    df = get_data(etf)
    if df is None:
        print('   No data available')
        continue
    
    # Calculate BB Squeeze
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_width'] = (4 * df['std20']) / df['sma20'] * 100
    df['bb_width_pctile'] = df['bb_width'].rolling(120).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
    
    # Split train/test
    train = df[df['date'] < pd.Timestamp('2023-01-01')]
    test = df[df['date'] >= pd.Timestamp('2023-01-01')]
    
    # Entry: BB Width < 10th percentile (squeeze) + breakout next day
    train_signals = []
    for i in range(120, len(train)-5):
        if train['bb_width_pctile'].iloc[i] < 0.10:
            # Check if breakout next day
            if i+1 < len(train) and train['close'].iloc[i+1] > train['high'].iloc[i]:
                ret = (train['close'].iloc[i+5] - train['close'].iloc[i+1]) / train['close'].iloc[i+1] * 100 - 0.1
                train_signals.append(ret)
    
    test_signals = []
    for i in range(120, len(test)-5):
        if test['bb_width_pctile'].iloc[i] < 0.10:
            if i+1 < len(test) and test['close'].iloc[i+1] > test['high'].iloc[i]:
                ret = (test['close'].iloc[i+5] - test['close'].iloc[i+1]) / test['close'].iloc[i+1] * 100 - 0.1
                test_signals.append(ret)
    
    if test_signals:
        train_wr = (pd.Series(train_signals) > 0).mean() * 100 if train_signals else 0
        test_wr = (pd.Series(test_signals) > 0).mean() * 100
        decay = train_wr - test_wr
        status = classify(train_wr, test_wr, len(test_signals), decay)
        print(f'   Train: {train_wr:.1f}% ({len(train_signals)}) | Test: {test_wr:.1f}% ({len(test_signals)}) | Decay: {decay:+.1f}% | {status}')
        results.append((f'BB Squeeze {etf}', train_wr, test_wr, len(test_signals), decay, status))
    else:
        print('   No signals in test period')

# ============================================
# TEST 2: BB SQUEEZE ON INDIVIDUAL STOCKS
# ============================================
print('\n' + '='*80)
print('TEST 2: BB SQUEEZE ON INDIVIDUAL STOCKS (Sector Leaders)')
print('='*80)

sector_stocks = {
    'Finance': ['JPM', 'BAC', 'GS'],
    'Healthcare': ['JNJ', 'PFE', 'UNH'],
    'Energy': ['XOM', 'CVX'],
    'Consumer': ['WMT', 'HD', 'NKE']
}

for sector, stocks in sector_stocks.items():
    print(f'\n{sector}:')
    for stock in stocks:
        df = get_data(stock)
        if df is None:
            continue
        
        df['sma20'] = df['close'].rolling(20).mean()
        df['std20'] = df['close'].rolling(20).std()
        df['bb_width'] = (4 * df['std20']) / df['sma20'] * 100
        df['bb_width_pctile'] = df['bb_width'].rolling(120).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
        
        train = df[df['date'] < pd.Timestamp('2023-01-01')]
        test = df[df['date'] >= pd.Timestamp('2023-01-01')]
        
        test_signals = []
        for i in range(120, len(test)-5):
            if test['bb_width_pctile'].iloc[i] < 0.10:
                if i+1 < len(test) and test['close'].iloc[i+1] > test['high'].iloc[i]:
                    ret = (test['close'].iloc[i+5] - test['close'].iloc[i+1]) / test['close'].iloc[i+1] * 100 - 0.1
                    test_signals.append(ret)
        
        if test_signals:
            train_wr = 0  # Skip train for quick summary
            test_wr = (pd.Series(test_signals) > 0).mean() * 100
            print(f'   {stock}: {test_wr:.1f}% ({len(test_signals)} trades)')
            results.append((f'BB Squeeze {stock}', 0, test_wr, len(test_signals), 0, 'TESTED'))

# ============================================
# TEST 3: ASIAN SESSION LIQUIDITY FADE (FX)
# ============================================
print('\n' + '='*80)
print('TEST 3: ASIAN SESSION LIQUIDITY FADE (FX)')
print('='*80)

# Check if hourly FX data exists
cursor.execute('''
    SELECT COUNT(*) FROM bronze.fx_hourly 
    WHERE pair IN ('USDJPY', 'EURUSD', 'GBPUSD') 
    AND timestamp BETWEEN '2023-01-01' AND '2024-12-31'
''')
fx_count = cursor.fetchone()[0]

if fx_count > 0:
    print(f'FX Hourly data available: {fx_count} records')
    
    # Test Asian Session Fade
    cursor.execute('''
        SELECT pair, 
               AVG(CASE WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 7 THEN (close - open)*10000 END) as asian_pips,
               COUNT(*) as count
        FROM bronze.fx_hourly 
        WHERE timestamp BETWEEN '2023-01-01' AND '2024-12-31'
        GROUP BY pair
        ORDER BY pair
    ''')
    fx_results = cursor.fetchall()
    
    print('\nAsian Session (00:00-07:59 UTC) Average Move:')
    for pair, pips, count in fx_results:
        if pips:
            print(f'   {pair}: {pips:+.2f} pips (n={count})')
else:
    print('FX Hourly data not yet in Bronze layer')
    print('Status: ⏳ Waiting for data ingestion')

conn.close()

# ============================================
# SUMMARY
# ============================================
print('\n' + '='*80)
print('SUMMARY')
print('='*80)

print(f'\nTotal Tests: {len(results)}')
golden = [r for r in results if r[5] == '🏆 GOLDEN']
validated = [r for r in results if r[5] == '✅ VALIDATED']
insufficient = [r for r in results if r[5] == '⏳ INSUFFICIENT']

print(f'🏆 Golden: {len(golden)}')
print(f'✅ Validated: {len(validated)}')
print(f'⏳ Insufficient: {len(insufficient)}')

if golden:
    print('\n🏆 GOLDEN STRATEGIES:')
    for name, train, test, n, decay, status in golden:
        print(f'   {name}: {test:.1f}% win ({n} trades)')

if validated:
    print('\n✅ VALIDATED STRATEGIES:')
    for name, train, test, n, decay, status in validated:
        print(f'   {name}: {test:.1f}% win ({n} trades)')
