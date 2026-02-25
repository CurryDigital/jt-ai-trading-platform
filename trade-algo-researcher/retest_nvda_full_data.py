#!/usr/bin/env python3
"""
RE-TEST: NVDA with full data (1289 records available)
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
print('RE-TEST: NVDA AI Theme Strategy (Full Data Available)')
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

# Get NVDA data (full range)
cursor.execute('''
    SELECT date, close::float
    FROM silver.unified_prices
    WHERE ticker = 'NVDA' AND date BETWEEN '2022-01-01' AND '2024-12-31'
    ORDER BY date
''')
nvda_data = cursor.fetchall()
print(f'NVDA records: {len(nvda_data)}')

nvda_df = pd.DataFrame(nvda_data, columns=['date', 'close'])
nvda_df['return'] = nvda_df['close'].pct_change() * 100

# Get 0700.HK data
cursor.execute('''
    SELECT date, open::float, close::float
    FROM silver.unified_prices
    WHERE ticker = '0700.HK' AND date BETWEEN '2022-01-01' AND '2024-12-31'
    ORDER BY date
''')
hk_data = cursor.fetchall()
hk_df = pd.DataFrame(hk_data, columns=['date', 'open', 'close'])
hk_df['prev_close'] = hk_df['close'].shift(1)
hk_df['overnight_gap'] = (hk_df['open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100

conn.close()

# Align
nvda_df['date_plus_1'] = pd.to_datetime(nvda_df['date']) + pd.Timedelta(days=1)
hk_df['date'] = pd.to_datetime(hk_df['date'])
merged = nvda_df.merge(hk_df, left_on='date_plus_1', right_on='date', how='inner')

print(f'\\nMatched days: {len(merged)}')

# Test NVDA > +5%
print('\\n=== TEST: NVDA > +5% → 0700.HK ===')
signals = merged[merged['return'] > 5.0]
print(f'NVDA > +5% days: {len(signals)}')

if len(signals) >= 10:
    win_rate = (signals['overnight_gap'] > 0).mean() * 100
    avg_gap = signals['overnight_gap'].mean()
    median_gap = signals['overnight_gap'].median()
    
    print(f'\\nResults:')
    print(f'Win rate: {win_rate:.1f}%')
    print(f'Avg overnight gap: {avg_gap:.2f}%')
    print(f'Median gap: {median_gap:.2f}%')
    
    # Distribution
    up_big = (signals['overnight_gap'] > 1.0).sum()
    up_small = ((signals['overnight_gap'] > 0) & (signals['overnight_gap'] <= 1.0)).sum()
    down = (signals['overnight_gap'] < 0).sum()
    
    print(f'\\nGap distribution:')
    print(f'  Strong up (>1%): {up_big} ({up_big/len(signals)*100:.0f}%)')
    print(f'  Modest up (0-1%): {up_small} ({up_small/len(signals)*100:.0f}%)')
    print(f'  Down (<0%): {down} ({down/len(signals)*100:.0f}%)')
    
    # Threshold sensitivity
    print(f'\\n=== Threshold Sensitivity ===')
    for thresh in [3.0, 5.0, 7.0, 10.0]:
        subset = merged[merged['return'] > thresh]
        if len(subset) >= 5:
            wr = (subset['overnight_gap'] > 0).mean() * 100
            avg = subset['overnight_gap'].mean()
            print(f'NVDA > +{thresh}%: {len(subset):3d} days, {wr:5.1f}% win, {avg:+.2f}% avg')
    
    # Verdict
    print('\\n' + '='*70)
    if win_rate >= 65:
        print(f'✅ STRONG: {win_rate:.1f}% win rate - Consider adding to portfolio')
    elif win_rate >= 55:
        print(f'🟡 MODERATE: {win_rate:.1f}% win rate - Validated but lower priority')
    else:
        print(f'❌ WEAK: {win_rate:.1f}% win rate - Not recommended')
else:
    print(f'⚠️  Insufficient signals (need 10+, have {len(signals)})')

print('='*70)
