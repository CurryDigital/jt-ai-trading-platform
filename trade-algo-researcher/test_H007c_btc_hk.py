#!/usr/bin/env python3
"""
H#007b: BTC from crypto_metrics → HK Tech
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
print('H#007b: BTC → HK Tech (Using gold.crypto_metrics)')
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

# Get BTC data from crypto_metrics
cursor.execute('''
    SELECT date, close_price
    FROM gold.crypto_metrics
    WHERE ticker = 'BTC-USD'
    ORDER BY date
''')
btc_data = cursor.fetchall()
print(f'BTC-USD records: {len(btc_data)}')

if len(btc_data) > 100:
    btc_df = pd.DataFrame(btc_data, columns=['date', 'close'])
    btc_df['return'] = btc_df['close'].pct_change() * 100
    print(f'Date range: {btc_df["date"].min()} to {btc_df["date"].max()}')
    
    # Get 0700.HK data
    cursor.execute('''
        SELECT date, open::float, close::float
        FROM silver.unified_prices
        WHERE ticker = '0700.HK'
        ORDER BY date
    ''')
    hk_data = cursor.fetchall()
    hk_df = pd.DataFrame(hk_data, columns=['date', 'open', 'close'])
    hk_df['prev_close'] = hk_df['close'].shift(1)
    hk_df['overnight_gap'] = (hk_df['open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100
    
    # Align
    btc_df['date'] = pd.to_datetime(btc_df['date'])
    btc_df['date_plus_1'] = btc_df['date'] + pd.Timedelta(days=1)
    hk_df['date'] = pd.to_datetime(hk_df['date'])
    merged = btc_df.merge(hk_df, left_on='date_plus_1', right_on='date', how='inner')
    
    print(f'\\nMatched days: {len(merged)}')
    
    if len(merged) > 50:
        # Test BTC > +10%
        print('\\n=== BTC > +10% → 0700.HK ===')
        signals = merged[merged['return'] > 10.0]
        print(f'BTC > +10% days: {len(signals)}')
        
        if len(signals) >= 10:
            win_rate = (signals['overnight_gap'] > 0).mean() * 100
            avg_gap = signals['overnight_gap'].mean()
            print(f'0700.HK win rate: {win_rate:.1f}%')
            print(f'Avg overnight gap: {avg_gap:.2f}%')
            
            # Distribution
            up_big = (signals['overnight_gap'] > 1.0).sum()
            up_small = ((signals['overnight_gap'] > 0) & (signals['overnight_gap'] <= 1.0)).sum()
            down = (signals['overnight_gap'] < 0).sum()
            
            print(f'\\nGap distribution:')
            print(f'  Strong up (>1%): {up_big} ({up_big/len(signals)*100:.0f}%)')
            print(f'  Modest up: {up_small} ({up_small/len(signals)*100:.0f}%)')
            print(f'  Down: {down} ({down/len(signals)*100:.0f}%)')
        else:
            print('⚠️  Insufficient extreme BTC moves')
        
        # Test different thresholds
        print('\\n=== Threshold Sensitivity ===')
        for thresh in [5.0, 7.0, 10.0, 15.0]:
            subset = merged[merged['return'] > thresh]
            if len(subset) >= 5:
                wr = (subset['overnight_gap'] > 0).mean() * 100
                avg = subset['overnight_gap'].mean()
                print(f'BTC > +{thresh}%: {len(subset):3d} days, {wr:5.1f}% win, {avg:+.2f}% avg')
    else:
        print('⚠️  Insufficient matched days')
else:
    print('❌ Insufficient BTC data')

conn.close()

print('\\n' + '='*70)
