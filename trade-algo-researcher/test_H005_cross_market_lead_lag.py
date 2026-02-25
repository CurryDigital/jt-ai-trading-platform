#!/usr/bin/env python3
"""
H#005: Cross-Market Lead-Lag Test
US Tech (GOOGL) → HK Tech (0700.HK, 9988.HK)
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
print('H#005: US Tech Lead-Lag → HK Tech')
print('Testing: If GOOGL rises, do HK tech stocks gap up?')
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

# Get US tech data
cursor.execute('''
    SELECT date, ticker, open::float, close::float
    FROM silver.unified_prices
    WHERE ticker IN ('GOOGL', 'QQQ', 'NVDA') 
    AND date BETWEEN '2023-01-01' AND '2024-12-31'
    ORDER BY ticker, date
''')
us_data = cursor.fetchall()
us_df = pd.DataFrame(us_data, columns=['date', 'ticker', 'us_open', 'us_close'])
us_df['us_return'] = (us_df['us_close'] - us_df['us_open']) / us_df['us_open'] * 100

# Get HK tech data
cursor.execute('''
    SELECT date, ticker, open::float, close::float
    FROM silver.unified_prices
    WHERE ticker IN ('0700.HK', '9988.HK')
    AND date BETWEEN '2023-01-01' AND '2024-12-31'
    ORDER BY ticker, date
''')
hk_data = cursor.fetchall()
hk_df = pd.DataFrame(hk_data, columns=['date', 'ticker', 'hk_open', 'hk_close'])

# Calculate overnight gap for HK (today's open vs yesterday's close)
hk_df['prev_close'] = hk_df.groupby('ticker')['hk_close'].shift(1)
hk_df['overnight_gap'] = (hk_df['hk_open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100

conn.close()

print(f'\\n=== Data Loaded ===')
print(f'US records: {len(us_df)}')
print(f'HK records: {len(hk_df)}')

# Test GOOGL -> 0700.HK
gOOGL = us_df[us_df['ticker'] == 'GOOGL'][['date', 'us_return']].copy()
_0700 = hk_df[hk_df['ticker'] == '0700.HK'][['date', 'overnight_gap']].copy()

# Merge: US Day T with HK Day T+1
gOOGL['date_plus_1'] = pd.to_datetime(gOOGL['date']) + pd.Timedelta(days=1)
_0700['date'] = pd.to_datetime(_0700['date'])
merged = gOOGL.merge(_0700, left_on='date_plus_1', right_on='date', how='inner')

print(f'\\n=== GOOGL → 0700.HK Analysis ===')
print(f'Matched days: {len(merged)}')

# Calculate correlation
corr = merged['us_return'].corr(merged['overnight_gap'])
print(f'Correlation: {corr:.3f}')

# Test signal: GOOGL > +2%
threshold = 2.0
signal_days = merged[merged['us_return'] > threshold]

print(f'\\n=== Signal Test: GOOGL > +{threshold}% ===')
print(f'Signal days: {len(signal_days)}')

if len(signal_days) > 10:
    avg_gap = signal_days['overnight_gap'].mean()
    win_rate = (signal_days['overnight_gap'] > 0).mean() * 100
    median_gap = signal_days['overnight_gap'].median()
    
    print(f'Avg 0700.HK gap: {avg_gap:.2f}%')
    print(f'Median gap: {median_gap:.2f}%')
    print(f'Win rate (gap > 0): {win_rate:.1f}%')
    
    # Distribution
    print(f'\\nGap Distribution:')
    print(f'  Gap > +1%: {(signal_days["overnight_gap"] > 1).sum()} days ({(signal_days["overnight_gap"] > 1).mean()*100:.0f}%)')
    print(f'  Gap 0 to +1%: {((signal_days["overnight_gap"] > 0) & (signal_days["overnight_gap"] <= 1)).sum()} days')
    print(f'  Gap < 0%: {(signal_days["overnight_gap"] < 0).sum()} days ({(signal_days["overnight_gap"] < 0).mean()*100:.0f}%)')
    
    # Test different thresholds
    print(f'\\n=== Threshold Comparison ===')
    for thresh in [1.0, 2.0, 3.0, 4.0]:
        subset = merged[merged['us_return'] > thresh]
        if len(subset) > 5:
            wr = (subset['overnight_gap'] > 0).mean() * 100
            avg = subset['overnight_gap'].mean()
            print(f'GOOGL > +{thresh}%: {len(subset)} days, {wr:.1f}% win, {avg:.2f}% avg gap')

else:
    print('Insufficient signal days for analysis')

# Test QQQ -> 0700.HK
print('\\n' + '='*70)
print('=== QQQ → 0700.HK Analysis ===')
qqq = us_df[us_df['ticker'] == 'QQQ'][['date', 'us_return']].copy()
qqq['date_plus_1'] = pd.to_datetime(qqq['date']) + pd.Timedelta(days=1)
merged_qqq = qqq.merge(_0700, left_on='date_plus_1', right_on='date', how='inner')

corr_qqq = merged_qqq['us_return'].corr(merged_qqq['overnight_gap'])
print(f'Correlation: {corr_qqq:.3f}')

signal_qqq = merged_qqq[merged_qqq['us_return'] > 2.0]
if len(signal_qqq) > 10:
    wr_qqq = (signal_qqq['overnight_gap'] > 0).mean() * 100
    avg_qqq = signal_qqq['overnight_gap'].mean()
    print(f'QQQ > +2%: {len(signal_qqq)} days, {wr_qqq:.1f}% win, {avg_qqq:.2f}% avg gap')

# Test with 9988.HK
print('\\n' + '='*70)
print('=== GOOGL → 9988.HK (Alibaba) Analysis ===')
_9988 = hk_df[hk_df['ticker'] == '9988.HK'][['date', 'overnight_gap']].copy()
_9988['date'] = pd.to_datetime(_9988['date'])
merged_9988 = gOOGL.merge(_9988, left_on='date_plus_1', right_on='date', how='inner')

corr_9988 = merged_9988['us_return'].corr(merged_9988['overnight_gap'])
print(f'Correlation: {corr_9988:.3f}')

signal_9988 = merged_9988[merged_9988['us_return'] > 2.0]
if len(signal_9988) > 10:
    wr_9988 = (signal_9988['overnight_gap'] > 0).mean() * 100
    avg_9988 = signal_9988['overnight_gap'].mean()
    print(f'GOOGL > +2%: {len(signal_9988)} days, {wr_9988:.1f}% win, {avg_9988:.2f}% avg gap')

print('\\n' + '='*70)
print('H#005: SUMMARY')
print('='*70)
print(f'\\n0700.HK (Tencent):')
print(f'  Correlation with GOOGL: {corr:.3f}')
print(f'  GOOGL > +2% → 0700.HK gap: {win_rate:.1f}% win rate' if len(signal_days) > 10 else '  Insufficient data')

print(f'\\n9988.HK (Alibaba):')
print(f'  Correlation with GOOGL: {corr_9988:.3f}')
print(f'  GOOGL > +2% → 9988.HK gap: {wr_9988:.1f}% win rate' if len(signal_9988) > 10 else '  Insufficient data')

print('\\n' + '='*70)
if len(signal_days) > 10 and win_rate > 55:
    print('✅ HYPOTHESIS SUPPORTED: GOOGL up days predict HK tech gaps up')
elif len(signal_days) > 10:
    print('⚠️ WEAK SUPPORT: Correlation exists but win rate < 55%')
else:
    print('⏳ NEED MORE DATA: Test on larger sample')
print('='*70)
