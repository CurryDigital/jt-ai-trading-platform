#!/usr/bin/env python3
"""
COMPREHENSIVE DATA AUDIT
Check all strategies for data sufficiency and quality
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
print('COMPREHENSIVE DATA AUDIT - All Strategies')
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

# All tickers used in our strategies
strategy_tickers = {
    # Golden Strategies
    'BB+Monday GOLD': ['0700.HK', '9988.HK'],
    'Inside Day': ['AAPL', 'MSFT', 'NVDA', 'TSLA', '0700.HK', '9988.HK'],
    'COIN Strong Uptrend': ['COIN', 'SPY'],
    'IWM SPY Regime': ['IWM', 'SPY'],
    'RSI Mean Reversion': ['AAPL', 'MSFT', '0700.HK', '9988.HK'],
    'Volume Breakout': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'COIN'],
    '3-Day+Monday': ['AAPL', 'MSFT', '0700.HK', '9988.HK'],
    
    # Crypto Strategies
    'MSTR SPY Regime': ['MSTR', 'SPY'],
    'RIOT': ['RIOT'],
    
    # Cross-Market
    'QQQ Lead-Lag': ['QQQ', '0700.HK'],
    'IWM Lead-Lag': ['IWM', '0700.HK'],
}

all_tickers = set()
for tickers in strategy_tickers.values():
    all_tickers.update(tickers)

print(f'\\n=== AUDITING {len(all_tickers)} TICKERS ===\\n')

audit_results = []

for ticker in sorted(all_tickers):
    cursor.execute(f'''
        SELECT COUNT(*), MIN(date), MAX(date)
        FROM silver.unified_prices
        WHERE ticker = '{ticker}'
    ''')
    cnt, min_d, max_d = cursor.fetchone()
    
    cursor.execute(f'''
        SELECT COUNT(*)
        FROM gold.technical_indicators_calculated
        WHERE ticker = '{ticker}'
    ''')
    ind_cnt = cursor.fetchone()[0]
    
    # Determine status
    if cnt is None or cnt == 0:
        status = '❌ NO DATA'
        quality = 'CRITICAL'
    elif cnt < 100:
        status = '⚠️  INSUFFICIENT'
        quality = 'LOW'
    elif cnt < 500:
        status = '🟡 LIMITED'
        quality = 'MEDIUM'
    else:
        status = '✅ GOOD'
        quality = 'HIGH'
    
    audit_results.append({
        'ticker': ticker,
        'records': cnt or 0,
        'indicators': ind_cnt or 0,
        'date_range': f'{min_d} to {max_d}' if min_d else 'N/A',
        'status': status,
        'quality': quality
    })
    
    print(f'{status} {ticker:<10} | Records: {cnt or 0:5d} | Indicators: {ind_cnt or 0:5d} | {min_d} to {max_d}')

conn.close()

print('\\n' + '='*70)
print('AUDIT SUMMARY')
print('='*70)

audit_df = pd.DataFrame(audit_results)

# Summary by status
good = audit_df[audit_df['quality'] == 'HIGH']
limited = audit_df[audit_df['quality'] == 'MEDIUM']
insufficient = audit_df[audit_df['quality'] == 'LOW']
no_data = audit_df[audit_df['quality'] == 'CRITICAL']

print(f'\\n✅ GOOD (500+ records): {len(good)} tickers')
print(f'🟡 LIMITED (100-500): {len(limited)} tickers')
print(f'⚠️  INSUFFICIENT (<100): {len(insufficient)} tickers')
print(f'❌ NO DATA: {len(no_data)} tickers')

print('\\n' + '='*70)
print('STRATEGY IMPACT ANALYSIS')
print('='*70)

# Check which strategies are affected
print('\\nStrategies with SUFFICIENT data:')
for strategy, tickers in strategy_tickers.items():
    strategy_data = audit_df[audit_df['ticker'].isin(tickers)]
    min_quality = strategy_data['quality'].min()
    
    if min_quality == 'HIGH':
        print(f'  ✅ {strategy}')
    elif min_quality == 'MEDIUM':
        print(f'  🟡 {strategy} (some tickers limited)')
    elif min_quality == 'LOW':
        print(f'  ⚠️  {strategy} (insufficient data)')
    else:
        print(f'  ❌ {strategy} (NO DATA)')

print('\\n' + '='*70)
print('RECOMMENDATIONS')
print('='*70)
print('\\n✅ RELIABLE (can trust backtests):')
for _, row in good.iterrows():
    print(f'   {row["ticker"]} ({row["records"]} records)')

print('\\n⚠️  NEEDS RE-TESTING (insufficient data):')
for _, row in insufficient.iterrows():
    print(f'   {row["ticker"]} ({row["records"]} records)')

print('\\n❌ CANNOT USE (no data):')
for _, row in no_data.iterrows():
    print(f'   {row["ticker"]}')

print('\\n' + '='*70)
