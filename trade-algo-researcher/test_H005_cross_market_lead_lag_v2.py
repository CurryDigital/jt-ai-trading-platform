#!/usr/bin/env python3
"""
H#005: Cross-Market Lead-Lag Test (REVISED)
US Tech (QQQ - has full data) → HK Tech (0700.HK, 9988.HK)
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
print('H#005: US Tech Lead-Lag → HK Tech (REVISED with QQQ)')
print('Testing: If US tech rises, do HK tech stocks gap up?')
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

# Get QQQ data (has full history)
cursor.execute('''
    SELECT date, close::float
    FROM silver.unified_prices
    WHERE ticker = 'QQQ'
    AND date BETWEEN '2022-01-01' AND '2025-02-20'
    ORDER BY date
''')
qqq_data = cursor.fetchall()
qqq_df = pd.DataFrame(qqq_data, columns=['date', 'close'])
qqq_df['qqq_return'] = qqq_df['close'].pct_change() * 100

# Get 0700.HK data
cursor.execute('''
    SELECT date, open::float, close::float
    FROM silver.unified_prices
    WHERE ticker = '0700.HK'
    AND date BETWEEN '2022-01-01' AND '2025-02-20'
    ORDER BY date
''')
_0700_data = cursor.fetchall()
_0700_df = pd.DataFrame(_0700_data, columns=['date', 'open', 'close'])
_0700_df['prev_close'] = _0700_df['close'].shift(1)
_0700_df['overnight_gap'] = (_0700_df['open'] - _0700_df['prev_close']) / _0700_df['prev_close'] * 100

# Get 9988.HK data
cursor.execute('''
    SELECT date, open::float, close::float
    FROM silver.unified_prices
    WHERE ticker = '9988.HK'
    AND date BETWEEN '2022-01-01' AND '2025-02-20'
    ORDER BY date
''')
_9988_data = cursor.fetchall()
_9988_df = pd.DataFrame(_9988_data, columns=['date', 'open', 'close'])
_9988_df['prev_close'] = _9988_df['close'].shift(1)
_9988_df['overnight_gap'] = (_9988_df['open'] - _9988_df['prev_close']) / _9988_df['prev_close'] * 100

conn.close()

print(f'\\n=== Data Loaded ===')
print(f'QQQ records: {len(qqq_df)}')
print(f'0700.HK records: {len(_0700_df)}')
print(f'9988.HK records: {len(_9988_df)}')

# Merge QQQ (Day T) with HK (Day T+1)
# Need to handle trading days properly
def align_us_hk(us_df, hk_df, us_col, hk_col):
    results = []
    for idx, us_row in us_df.iterrows():
        us_date = us_row['date']
        us_return = us_row[us_col]
        
        # Find next HK trading day
        hk_next = hk_df[hk_df['date'] > us_date]
        if len(hk_next) > 0:
            hk_row = hk_next.iloc[0]
            # Check if it's the next calendar day or reasonable gap
            gap_days = (hk_row['date'] - us_date).days
            if gap_days <= 5:  # Within a week (accounts for holidays)
                results.append({
                    'us_date': us_date,
                    'hk_date': hk_row['date'],
                    'us_return': us_return,
                    'hk_gap': hk_row[hk_col],
                    'gap_days': gap_days
                })
    return pd.DataFrame(results)

print('\\n=== QQQ → 0700.HK Analysis ===')
merged_0700 = align_us_hk(qqq_df, _0700_df, 'qqq_return', 'overnight_gap')
print(f'Matched pairs: {len(merged_0700)}')

if len(merged_0700) > 50:
    # Correlation
    corr = merged_0700['us_return'].corr(merged_0700['hk_gap'])
    print(f'Correlation: {corr:.3f}')
    
    # Signal test: QQQ > +2%
    signals = merged_0700[merged_0700['us_return'] > 2.0]
    print(f'\\nQQQ > +2% days: {len(signals)}')
    
    if len(signals) > 10:
        win_rate = (signals['hk_gap'] > 0).mean() * 100
        avg_gap = signals['hk_gap'].mean()
        median_gap = signals['hk_gap'].median()
        
        print(f'0700.HK win rate: {win_rate:.1f}%')
        print(f'Avg overnight gap: {avg_gap:.2f}%')
        print(f'Median gap: {median_gap:.2f}%')
        
        # Distribution
        up_big = (signals['hk_gap'] > 1.0).sum()
        up_small = ((signals['hk_gap'] > 0) & (signals['hk_gap'] <= 1.0)).sum()
        down = (signals['hk_gap'] < 0).sum()
        
        print(f'\\nGap Distribution on QQQ > +2% days:')
        print(f'  Strong up (>1%): {up_big} ({up_big/len(signals)*100:.0f}%)')
        print(f'  Modest up (0-1%): {up_small} ({up_small/len(signals)*100:.0f}%)')
        print(f'  Down (<0%): {down} ({down/len(signals)*100:.0f}%)')
        
        # Test different thresholds
        print(f'\\n=== Threshold Sensitivity ===')
        for thresh in [1.0, 1.5, 2.0, 2.5, 3.0]:
            subset = merged_0700[merged_0700['us_return'] > thresh]
            if len(subset) > 5:
                wr = (subset['hk_gap'] > 0).mean() * 100
                avg_g = subset['hk_gap'].mean()
                print(f'QQQ > +{thresh}%: {len(subset):3d} days, {wr:5.1f}% win, {avg_g:+.2f}% avg')
    else:
        print('Insufficient signal days')
else:
    print('Insufficient matched data')

print('\\n=== QQQ → 9988.HK Analysis ===')
merged_9988 = align_us_hk(qqq_df, _9988_df, 'qqq_return', 'overnight_gap')
print(f'Matched pairs: {len(merged_9988)}')

if len(merged_9988) > 50:
    corr_9988 = merged_9988['us_return'].corr(merged_9988['hk_gap'])
    print(f'Correlation: {corr_9988:.3f}')
    
    signals_9988 = merged_9988[merged_9988['us_return'] > 2.0]
    if len(signals_9988) > 10:
        wr_9988 = (signals_9988['hk_gap'] > 0).mean() * 100
        avg_9988 = signals_9988['hk_gap'].mean()
        print(f'9988.HK win rate on QQQ > +2%: {wr_9988:.1f}%')
        print(f'Avg gap: {avg_9988:.2f}%')

print('\\n' + '='*70)
print('H#005: FINAL ASSESSMENT')
print('='*70)

if len(merged_0700) > 50 and len(signals) > 10:
    print(f'\\n0700.HK (Tencent):')
    print(f'  Correlation with QQQ: {corr:.3f}')
    print(f'  QQQ > +2% → 0700.HK gap win rate: {win_rate:.1f}%')
    print(f'  Average gap: {avg_gap:+.2f}%')
    
    if win_rate >= 60 and corr > 0.2:
        print('\\n✅ HYPOTHESIS VALIDATED: Strong support for cross-market lead-lag')
        print('   Recommendation: Deploy with QQQ > +2% threshold')
    elif win_rate >= 55 and corr > 0.15:
        print('\\n🟡 MODERATE SUPPORT: Strategy viable but monitor closely')
        print('   Recommendation: Paper trade first')
    else:
        print('\\n❌ WEAK SUPPORT: Effect too weak for deployment')
        print('   Gap already priced in by futures markets')
else:
    print('\\n⏳ INSUFFICIENT DATA: Need more overlapping trading days')
    print('   GOOGL data too recent; QQQ/0700.HK alignment needs verification')

print('='*70)
