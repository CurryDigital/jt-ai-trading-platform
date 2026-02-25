#!/usr/bin/env python3
"""
H#007: NVDA AI Theme + BTC Risk-On Tests
Limited data - preliminary analysis only
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
print('H#007: NVDA AI Theme + BTC Risk-On Tests')
print('⚠️  LIMITED DATA - Preliminary Analysis Only')
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

# Check data availability
print('\\n=== DATA AVAILABILITY CHECK ===')

cursor.execute('''
    SELECT COUNT(*), MIN(date), MAX(date)
    FROM silver.unified_prices
    WHERE ticker = 'NVDA'
''')
nvda_cnt, nvda_min, nvda_max = cursor.fetchone()
print(f'NVDA: {nvda_cnt} records ({nvda_min} to {nvda_max})')

cursor.execute('''
    SELECT COUNT(*), MIN(date), MAX(date)
    FROM silver.unified_prices
    WHERE ticker = '0700.HK'
''')
hk_cnt, hk_min, hk_max = cursor.fetchone()
print(f'0700.HK: {hk_cnt} records ({hk_min} to {hk_max})')

# Check crypto data
cursor.execute('''
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'gold' AND table_name = 'crypto_metrics'
    LIMIT 10
''')
crypto_cols = [row[0] for row in cursor.fetchall()]
print(f'\\ngold.crypto_metrics columns: {crypto_cols}')

cursor.execute('''
    SELECT DISTINCT ticker
    FROM gold.crypto_metrics
    LIMIT 10
''')
crypto_symbols = [row[0] for row in cursor.fetchall()]
print(f'Available crypto symbols: {crypto_symbols}')

# TEST 1: NVDA > +5% → 0700.HK (if sufficient data)
print('\\n' + '='*70)
print('TEST 1: NVDA > +5% → 0700.HK')
print('='*70)

if nvda_cnt >= 30:  # Minimum for any analysis
    cursor.execute('''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = 'NVDA'
        ORDER BY date
    ''')
    nvda_data = cursor.fetchall()
    nvda_df = pd.DataFrame(nvda_data, columns=['date', 'close'])
    nvda_df['return'] = nvda_df['close'].pct_change() * 100
    
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
    nvda_df['date_plus_1'] = pd.to_datetime(nvda_df['date']) + pd.Timedelta(days=1)
    hk_df['date'] = pd.to_datetime(hk_df['date'])
    merged = nvda_df.merge(hk_df, left_on='date_plus_1', right_on='date', how='inner')
    
    print(f'Matched days: {len(merged)}')
    
    if len(merged) >= 10:
        # Test NVDA > +5%
        signals = merged[merged['return'] > 5.0]
        print(f'NVDA > +5% days: {len(signals)}')
        
        if len(signals) >= 3:
            win_rate = (signals['overnight_gap'] > 0).mean() * 100
            avg_gap = signals['overnight_gap'].mean()
            print(f'0700.HK win rate: {win_rate:.1f}%')
            print(f'Avg overnight gap: {avg_gap:.2f}%')
            
            # Show individual trades
            print('\\nIndividual signals:')
            for _, row in signals.iterrows():
                print(f'  {row["date"].date()}: NVDA {row["return"]:+.1f}% → 0700.HK {row["overnight_gap"]:+.2f}%')
        else:
            print('⚠️  Insufficient signals (need 3+, have {})'.format(len(signals)))
    else:
        print('⚠️  Insufficient matched days')
else:
    print('❌ Insufficient NVDA data (need 30+ days, have {})'.format(nvda_cnt))

# TEST 2: BTC proxy → HK Tech (MSTR/COIN as proxy)
print('\\n' + '='*70)
print('TEST 2: Crypto Proxy (MSTR/COIN) → 0700.HK')
print('(BTC data not available, using crypto stocks as proxy)')
print('='*70)

for crypto_proxy in ['MSTR', 'COIN']:
    cursor.execute(f'''
        SELECT COUNT(*)
        FROM silver.unified_prices
        WHERE ticker = '{crypto_proxy}'
    ''')
    proxy_cnt = cursor.fetchone()[0]
    
    if proxy_cnt > 0:
        cursor.execute(f'''
            SELECT date, close::float
            FROM silver.unified_prices
            WHERE ticker = '{crypto_proxy}'
            ORDER BY date
        ''')
        proxy_data = cursor.fetchall()
        proxy_df = pd.DataFrame(proxy_data, columns=['date', 'close'])
        proxy_df['return'] = proxy_df['close'].pct_change() * 100
        
        # Align with 0700.HK
        proxy_df['date_plus_1'] = pd.to_datetime(proxy_df['date']) + pd.Timedelta(days=1)
        merged_proxy = proxy_df.merge(hk_df, left_on='date_plus_1', right_on='date', how='inner')
        
        print(f'\\n{crypto_proxy} → 0700.HK:')
        print(f'  Matched days: {len(merged_proxy)}')
        
        if len(merged_proxy) >= 5:
            # Test extreme moves (> +10% as proxy for BTC > +10%)
            signals = merged_proxy[merged_proxy['return'] > 10.0]
            print(f'  {crypto_proxy} > +10% days: {len(signals)}')
            
            if len(signals) >= 2:
                win_rate = (signals['overnight_gap'] > 0).mean() * 100
                avg_gap = signals['overnight_gap'].mean()
                print(f'  0700.HK win rate: {win_rate:.1f}%')
                print(f'  Avg gap: {avg_gap:.2f}%')
            else:
                print(f'  ⚠️  Insufficient extreme moves')

conn.close()

print('\\n' + '='*70)
print('SUMMARY')
print('='*70)
print('\\n⚠️  DATA LIMITATIONS:')
print('   - NVDA: Only 3 months of data (insufficient for reliable backtest)')
print('   - BTC-USD: No data in database')
print('   - Used MSTR/COIN as crypto proxies')
print('\\n✅ RECOMMENDATION:')
print('   Request historical data from JT Trading Agent:')
print('   1. NVDA: 2+ years of daily data')
print('   2. BTC-USD: 2+ years of daily data')
print('   3. ETH-USD: Optional, for additional tests')
print('\\n   Once data available, re-run tests for robust results')
print('='*70)
