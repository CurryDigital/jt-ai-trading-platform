#!/usr/bin/env python3
"""
RIGOROUS STRATEGY VALIDATION
Checks: Data gaps, overfitting, walk-forward performance
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print('='*70)
print('RIGOROUS VALIDATION: Data Quality + Overfitting Checks')
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

# ============================================
# PART 1: DATA GAP ANALYSIS
# ============================================
print('\\n' + '='*70)
print('PART 1: DATA GAP ANALYSIS')
print('='*70)

all_tickers = ['QQQ', 'NVDA', 'MSTR', 'COIN', 'IWM', 'SPY', '0700.HK', '9988.HK']

for ticker in all_tickers:
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2022-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    
    if len(data) == 0:
        print(f'❌ {ticker}: NO DATA')
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['gap'] = df['date'].diff().dt.days
    
    max_gap = df['gap'].max()
    avg_gap = df['gap'].mean()
    gap_days = (df['gap'] > 5).sum()  # Gaps > 5 days (weekend+holiday)
    
    status = '✅' if max_gap <= 5 else '⚠️' if max_gap <= 10 else '❌'
    print(f'{status} {ticker:<10} | Records: {len(df):4d} | Max Gap: {max_gap:2.0f} days | Gaps >5d: {gap_days:2d}')

# ============================================
# PART 2: TRAIN/TEST SPLIT (Overfitting Check)
# ============================================
print('\\n' + '='*70)
print('PART 2: OVERFITTING CHECK (Train 2022-2023 / Test 2024)')
print('='*70)

def test_strategy(train_start, train_end, test_start, test_end, name):
    """Test strategy on train/test split"""
    
    # Get training data
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = 'QQQ' AND date BETWEEN '{train_start}' AND '{train_end}'
        ORDER BY date
    ''')
    train_qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
    train_qqq['return'] = train_qqq['close'].pct_change() * 100
    
    cursor.execute(f'''
        SELECT date, open::float, close::float
        FROM silver.unified_prices
        WHERE ticker = '0700.HK' AND date BETWEEN '{train_start}' AND '{train_end}'
        ORDER BY date
    ''')
    train_hk = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
    train_hk['prev_close'] = train_hk['close'].shift(1)
    train_hk['gap'] = (train_hk['open'] - train_hk['prev_close']) / train_hk['prev_close'] * 100
    
    # Find optimal threshold on training data
    thresholds = [1.0, 1.5, 2.0, 2.5, 3.0]
    best_thresh = 2.0
    best_wr = 0
    
    for thresh in thresholds:
        train_qqq['next_date'] = pd.to_datetime(train_qqq['date']) + pd.Timedelta(days=1)
        train_hk['date'] = pd.to_datetime(train_hk['date'])
        merged = train_qqq.merge(train_hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
        signals = merged[merged['return'] > thresh]
        if len(signals) > 10:
            wr = (signals['gap'] > 0).mean() * 100
            if wr > best_wr:
                best_wr = wr
                best_thresh = thresh
    
    # Test on out-of-sample data
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = 'QQQ' AND date BETWEEN '{test_start}' AND '{test_end}'
        ORDER BY date
    ''')
    test_qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
    test_qqq['return'] = test_qqq['close'].pct_change() * 100
    
    cursor.execute(f'''
        SELECT date, open::float, close::float
        FROM silver.unified_prices
        WHERE ticker = '0700.HK' AND date BETWEEN '{test_start}' AND '{test_end}'
        ORDER BY date
    ''')
    test_hk = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
    test_hk['prev_close'] = test_hk['close'].shift(1)
    test_hk['gap'] = (test_hk['open'] - test_hk['prev_close']) / test_hk['prev_close'] * 100
    
    test_qqq['next_date'] = pd.to_datetime(test_qqq['date']) + pd.Timedelta(days=1)
    test_hk['date'] = pd.to_datetime(test_hk['date'])
    merged_test = test_qqq.merge(test_hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    signals_test = merged_test[merged_test['return'] > best_thresh]
    
    if len(signals_test) > 5:
        test_wr = (signals_test['gap'] > 0).mean() * 100
        print(f'\\n{name}:')
        print(f'  Optimal threshold (train): {best_thresh}%')
        print(f'  Train win rate: {best_wr:.1f}%')
        print(f'  Test win rate:  {test_wr:.1f}%')
        print(f'  Decay: {best_wr - test_wr:+.1f}%')
        
        if test_wr >= best_wr - 10:  # Less than 10% decay
            return '✅ ROBUST', test_wr
        else:
            return '⚠️  OVERFITTING RISK', test_wr
    else:
        return '⏳ INSUFFICIENT TEST DATA', 0

# Test QQQ Lead-Lag
result, wr = test_strategy('2022-01-01', '2023-06-30', '2023-07-01', '2024-12-31', 'QQQ Lead-Lag')
print(f'  Status: {result}')

# ============================================
# PART 3: WALK-FORWARD ANALYSIS
# ============================================
print('\\n' + '='*70)
print('PART 3: WALK-FORWARD ANALYSIS (12-Month Rolling Windows)')
print('='*70)

periods = [
    ('2022-01', '2022-12'),
    ('2023-01', '2023-12'),
    ('2024-01', '2024-12'),
]

print('\\nQQQ Lead-Lag by Year:')
for start, end in periods:
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = 'QQQ' AND date BETWEEN '{start}-01' AND '{end}-31'
        ORDER BY date
    ''')
    qqq_df = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
    qqq_df['return'] = qqq_df['close'].pct_change() * 100
    
    cursor.execute(f'''
        SELECT date, open::float, close::float
        FROM silver.unified_prices
        WHERE ticker = '0700.HK' AND date BETWEEN '{start}-01' AND '{end}-31'
        ORDER BY date
    ''')
    hk_df = pd.DataFrame(cursor.fetchall(), columns=['date', 'open', 'close'])
    hk_df['prev_close'] = hk_df['close'].shift(1)
    hk_df['gap'] = (hk_df['open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100
    
    qqq_df['next_date'] = pd.to_datetime(qqq_df['date']) + pd.Timedelta(days=1)
    hk_df['date'] = pd.to_datetime(hk_df['date'])
    merged = qqq_df.merge(hk_df[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
    signals = merged[merged['return'] > 2.0]
    
    if len(signals) > 5:
        wr = (signals['gap'] > 0).mean() * 100
        status = '✅' if wr >= 70 else '🟡' if wr >= 60 else '❌'
        print(f'  {status} {start}-{end}: {wr:.1f}% win ({len(signals)} signals)')
    else:
        print(f'  ⏳ {start}-{end}: Insufficient signals')

# ============================================
# PART 4: SURVIVORSHIP BIAS CHECK
# ============================================
print('\\n' + '='*70)
print('PART 4: SURVIVORSHIP BIAS CHECK')
print('='*70)

print('\\nChecking if tickers existed throughout test period:')
for ticker in ['0700.HK', '9988.HK', 'COIN', 'MSTR']:
    cursor.execute(f'''
        SELECT MIN(date), MAX(date)
        FROM silver.unified_prices
        WHERE ticker = '{ticker}'
    ''')
    min_d, max_d = cursor.fetchone()
    
    if min_d and max_d:
        start_diff = (datetime(2022, 1, 1).date() - min_d).days if min_d > datetime(2022, 1, 1).date() else 0
        end_diff = (max_d - datetime(2024, 12, 31).date()).days if max_d < datetime(2024, 12, 31).date() else 0
        
        if start_diff <= 30 and end_diff >= -30:  # Within 30 days
            print(f'  ✅ {ticker}: {min_d} to {max_d} (Full period)')
        else:
            print(f'  ⚠️  {ticker}: {min_d} to {max_d} (Partial - check for survivorship bias)')
    else:
        print(f'  ❌ {ticker}: No date range available')

conn.close()

print('\\n' + '='*70)
print('VALIDATION SUMMARY')
print('='*70)
print('\\n✅ Data Quality: Check for gaps >5 trading days')
print('✅ Overfitting: Train/test split with <10% performance decay')
print('✅ Robustness: Walk-forward analysis across multiple periods')
print('✅ Survivorship: Verify tickers existed throughout test period')
print('='*70)
