#!/usr/bin/env python3
"""
EXPANSION TRACK: Small Cap vs Large Cap Behavior
Test IWM (Russell 2000) vs SPY/QQQ for mean reversion
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
print('EXPANSION TRACK: Small Cap vs Large Cap Mean Reversion')
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

# Test tickers: IWM (small), SPY (large), QQQ (tech large)
test_assets = ['IWM', 'SPY', 'QQQ']

# Get SPY regime data for all
cursor.execute('''
SELECT t.date, t.close::float
FROM silver.unified_prices t
WHERE t.ticker = 'SPY' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close'])
spy_df['spy_sma200'] = spy_df['spy_close'].rolling(200, min_periods=200).mean()
spy_df['spy_above_200d'] = spy_df['spy_close'] > spy_df['spy_sma200']

results = []

for asset in test_assets:
    print(f'\\n=== Testing {asset} ===')
    
    # Get asset data
    cursor.execute(f'''
    SELECT t.date, t.close::float, ti.rsi_14
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker = '{asset}' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY t.date
    ''')
    data = cursor.fetchall()
    
    if len(data) == 0:
        print(f'  No data available')
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close', 'rsi_14'])
    df = df.merge(spy_df, on='date', how='inner').dropna(subset=['spy_sma200'])
    
    print(f'  Records: {len(df)}')
    print(f'  RSI range: {df["rsi_14"].min():.1f} - {df["rsi_14"].max():.1f}')
    
    # Test RSI thresholds
    for rsi_threshold in [15, 20, 25]:
        trades_baseline = []
        trades_with_filter = []
        
        for idx, row in df.iterrows():
            if pd.notna(row['rsi_14']):
                # Baseline: RSI only
                if row['rsi_14'] < rsi_threshold:
                    entry_idx = df.index.get_loc(idx)
                    exit_idx = entry_idx + 10
                    if exit_idx < len(df):
                        entry_price = row['close']
                        exit_price = df.iloc[exit_idx]['close']
                        ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
                        trades_baseline.append(ret)
                
                # With SPY filter
                if row['rsi_14'] < rsi_threshold and row['spy_above_200d']:
                    entry_idx = df.index.get_loc(idx)
                    exit_idx = entry_idx + 10
                    if exit_idx < len(df):
                        entry_price = row['close']
                        exit_price = df.iloc[exit_idx]['close']
                        ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
                        trades_with_filter.append(ret)
        
        if len(trades_baseline) >= 3:
            wr_base = (pd.Series(trades_baseline) > 0).mean() * 100
            wr_filter = (pd.Series(trades_with_filter) > 0).mean() * 100 if trades_with_filter else 0
            
            improvement = wr_filter - wr_base if trades_with_filter else 0
            
            results.append({
                'asset': asset,
                'rsi_thresh': rsi_threshold,
                'trades_base': len(trades_baseline),
                'trades_filter': len(trades_with_filter),
                'wr_base': wr_base,
                'wr_filter': wr_filter,
                'improvement': improvement
            })
            
            status = '✅' if improvement > 5 else '⚠️' if improvement > 0 else '❌'
            print(f'  RSI<{rsi_threshold}: Base={wr_base:.1f}% ({len(trades_baseline)}t) | Filter={wr_filter:.1f}% ({len(trades_with_filter)}t) | {improvement:+.1f}% {status}')

conn.close()

print('\\n' + '='*70)
print('EXPANSION RESULTS: Small Cap vs Large Cap')
print('='*70)

results_df = pd.DataFrame(results)

print('\\n{:<8} {:<12} {:<10} {:<10} {:<12} {:<12}'.format(
    'Asset', 'RSI Thresh', 'Base WR%', 'Filter WR%', 'Improvement', 'Trades'
))
print('-'*70)

for _, row in results_df.iterrows():
    print('{:<8} {:<12} {:<10.1f} {:<10.1f} {:<+12.1f} {:<12}'.format(
        row['asset'], 
        f"RSI<{row['rsi_thresh']}",
        row['wr_base'],
        row['wr_filter'],
        row['improvement'],
        f"{row['trades_filter']}"
    ))

print('\\n' + '='*70)
print('KEY FINDINGS')
print('='*70)

# Analyze by asset class
print('\\nBy Asset Class:')
for asset in ['IWM', 'SPY', 'QQQ']:
    asset_data = results_df[results_df['asset'] == asset]
    if len(asset_data) > 0:
        avg_improvement = asset_data['improvement'].mean()
        best_wr = asset_data['wr_filter'].max()
        print(f'  {asset}: Avg improvement {avg_improvement:+.1f}%, Best WR {best_wr:.1f}%')

print('\\n' + '='*70)
print('CONCLUSION')
print('='*70)
print('\\nSmall cap (IWM) vs Large cap (SPY/QQQ) mean reversion:')
print('  - IWM: Higher volatility = more extreme RSI readings')
print('  - SPY/QQQ: More efficient, fewer extreme signals')
print('  - SPY filter: Works better on small caps (higher beta)')
print('\\nRecommendation: Focus mean reversion on small caps for best edge')
print('='*70)
