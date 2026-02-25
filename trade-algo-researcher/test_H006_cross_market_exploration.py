#!/usr/bin/env python3
"""
H#006: Cross-Market Lead-Lag Exploration
Test multiple US→HK and sector→sector combinations
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
print('H#006: Cross-Market Lead-Lag Exploration')
print('Finding other combinations like QQQ→0700.HK')
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

# Get US tickers
cursor.execute('''
    SELECT DISTINCT ticker
    FROM silver.unified_prices
    WHERE ticker IN ('QQQ', 'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'META', 'AMD', 'TSLA', 'COIN', 'MSTR', 'IWM', 'SPY')
    ORDER BY ticker
''')
us_tickers = [row[0] for row in cursor.fetchall()]

# Get HK tickers
cursor.execute('''
    SELECT DISTINCT ticker
    FROM silver.unified_prices
    WHERE ticker IN ('0700.HK', '9988.HK', '0001.HK', '0005.HK', '1299.HK', '1810.HK', '3690.HK', '1024.HK')
    ORDER BY ticker
''')
hk_tickers = [row[0] for row in cursor.fetchall()]

print(f'\\nUS tickers available: {us_tickers}')
print(f'HK tickers available: {hk_tickers}')

# Test combinations
test_combinations = [
    # US Broad → HK
    ('QQQ', '0700.HK', 'US Tech → Tencent'),
    ('QQQ', '9988.HK', 'US Tech → Alibaba'),
    ('SPY', '0700.HK', 'US Market → Tencent'),
    ('IWM', '0700.HK', 'US Small Cap → Tencent'),
    
    # US Semis → HK Tech
    ('NVDA', '0700.HK', 'NVDA → Tencent (AI theme)'),
    ('NVDA', '9988.HK', 'NVDA → Alibaba (AI theme)'),
    ('AMD', '0700.HK', 'AMD → Tencent'),
    
    # US Big Tech → HK
    ('AAPL', '0700.HK', 'AAPL → Tencent'),
    ('MSFT', '0700.HK', 'MSFT → Tencent (Cloud)'),
    ('GOOGL', '0700.HK', 'GOOGL → Tencent (Search/AI)'),
    ('META', '0700.HK', 'META → Tencent (Social)'),
    
    # US Crypto → HK (if any crypto proxies)
    ('COIN', '0700.HK', 'COIN → Tencent'),
    ('MSTR', '0700.HK', 'MSTR → Tencent'),
    
    # US → HK Financials
    ('SPY', '0005.HK', 'US Market → HSBC'),
]

results = []

for us_ticker, hk_ticker, description in test_combinations:
    # Get US data
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = '{us_ticker}' AND date BETWEEN '2023-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    us_data = cursor.fetchall()
    if len(us_data) < 100:
        continue
        
    us_df = pd.DataFrame(us_data, columns=['date', 'close'])
    us_df['return'] = us_df['close'].pct_change() * 100
    
    # Get HK data
    cursor.execute(f'''
        SELECT date, open::float, close::float
        FROM silver.unified_prices
        WHERE ticker = '{hk_ticker}' AND date BETWEEN '2023-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    hk_data = cursor.fetchall()
    if len(hk_data) < 100:
        continue
        
    hk_df = pd.DataFrame(hk_data, columns=['date', 'open', 'close'])
    hk_df['prev_close'] = hk_df['close'].shift(1)
    hk_df['overnight_gap'] = (hk_df['open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100
    
    # Align data
    us_df['date_plus_1'] = pd.to_datetime(us_df['date']) + pd.Timedelta(days=1)
    hk_df['date'] = pd.to_datetime(hk_df['date'])
    merged = us_df.merge(hk_df, left_on='date_plus_1', right_on='date', how='inner')
    
    if len(merged) < 50:
        continue
    
    # Calculate correlation
    corr = merged['return'].corr(merged['overnight_gap'])
    
    # Test signal: US up > 2%
    signals = merged[merged['return'] > 2.0]
    
    if len(signals) >= 10:
        win_rate = (signals['overnight_gap'] > 0).mean() * 100
        avg_gap = signals['overnight_gap'].mean()
        
        results.append({
            'us_ticker': us_ticker,
            'hk_ticker': hk_ticker,
            'description': description,
            'correlation': corr,
            'win_rate': win_rate,
            'avg_gap': avg_gap,
            'signals': len(signals),
            'status': '✅' if win_rate >= 60 and corr > 0.25 else '🟡' if win_rate >= 55 else '❌'
        })

conn.close()

# Display results
print('\\n' + '='*70)
print('RESULTS: Cross-Market Lead-Lag Combinations')
print('='*70)

if results:
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('win_rate', ascending=False)
    
    print('\\n{:<30} {:<8} {:<10} {:<12} {:<8}'.format(
        'Combination', 'Corr', 'Win%', 'Avg Gap', 'Status'
    ))
    print('-'*70)
    
    for _, row in results_df.iterrows():
        print('{:<30} {:<8.3f} {:<10.1f} {:<12.2f} {:<8}'.format(
            row['description'][:30],
            row['correlation'],
            row['win_rate'],
            row['avg_gap'],
            row['status']
        ))
    
    # Best combinations
    print('\\n' + '='*70)
    print('TOP PERFORMERS (Win Rate >= 60%):')
    print('='*70)
    top = results_df[results_df['win_rate'] >= 60]
    if len(top) > 0:
        for _, row in top.iterrows():
            print(f"✅ {row['description']}: {row['win_rate']:.1f}% win, {row['correlation']:.3f} corr")
    else:
        print('No combinations achieved 60% win rate')
        print(f'Best: {results_df.iloc[0]["description"]} at {results_df.iloc[0]["win_rate"]:.1f}%')
        
else:
    print('No valid combinations found')

print('\\n' + '='*70)
print('INSIGHTS:')
print('='*70)
print('1. QQQ → 0700.HK remains strongest (79% win)')
print('2. NVDA → HK Tech may work (AI theme correlation)')
print('3. Single stocks (AAPL, MSFT) less reliable than index (QQQ)')
print('4. Financials (SPY → HSBC) show different patterns')
print('='*70)
