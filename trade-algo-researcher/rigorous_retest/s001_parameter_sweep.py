#!/usr/bin/env python3
"""
PARAMETER SWEEP: S001 RSI Mean Reversion
Test different RSI thresholds: 20, 22, 25, 28, 30
Find optimal threshold for each sector
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*100)
print('PARAMETER SWEEP: S001 RSI Mean Reversion')
print('Testing RSI thresholds: 20, 22, 25, 28, 30')
print('='*100)

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

# Focus on HK Banks and HK Utilities (best performers)
target_tickers = [
    '0005.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK',  # Banks
    '0002.HK', '0003.HK', '0006.HK', '0027.HK', '0083.HK'  # Utilities
]

rsi_thresholds = [20, 22, 25, 28, 30]
hold_periods = [5, 7, 10, 15]

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_params(ticker, rsi_thresh, hold_days):
    cursor.execute(f"""
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(14, len(test) - hold_days):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < rsi_thresh:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 5:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(14, len(validate) - hold_days):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < rsi_thresh:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 3 else 0
    
    return {
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

# Test all combinations
print('\nTesting parameter combinations...\n')

results = []
for ticker in target_tickers:
    for rsi_thresh in rsi_thresholds:
        for hold_days in hold_periods:
            result = test_params(ticker, rsi_thresh, hold_days)
            if result:
                results.append({
                    'ticker': ticker,
                    'rsi': rsi_thresh,
                    'hold': hold_days,
                    **result
                })

# Find best parameters per ticker
print('='*100)
print('OPTIMAL PARAMETERS BY TICKER (Best Test WR with Val WR >= 50%)')
print('='*100)

for ticker in target_tickers:
    ticker_results = [r for r in results if r['ticker'] == ticker]
    if not ticker_results:
        continue
    
    # Filter for valid validate and sort by test WR
    valid_results = [r for r in ticker_results if r['val_wr'] >= 50]
    if valid_results:
        best = sorted(valid_results, key=lambda x: x['test_wr'], reverse=True)[0]
        status = '🏆' if best['test_wr'] >= 65 else '✅'
        print(f"{status} {ticker}: RSI <{best['rsi']}, Hold {best['hold']}d | Test {best['test_wr']:.1f}% | Val {best['val_wr']:.1f}% | n={best['test_n']}")

# Overall best combinations
print('\n' + '='*100)
print('TOP 10 PARAMETER COMBINATIONS (Across All Tickers)')
print('='*100)

sorted_results = sorted([r for r in results if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)
for i, r in enumerate(sorted_results[:10], 1):
    print(f"{i:2d}. {r['ticker']} | RSI <{r['rsi']} | Hold {r['hold']}d | Test {r['test_wr']:.1f}% | Val {r['val_wr']:.1f}%")

# Summary by sector
print('\n' + '='*100)
print('SECTOR SUMMARY: Optimal Parameters')
print('='*100)

hk_banks = [r for r in results if r['ticker'] in ['0005.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK']]
hk_utils = [r for r in results if r['ticker'] in ['0002.HK', '0003.HK', '0006.HK', '0027.HK', '0083.HK']]

if hk_banks:
    best_bank = sorted([r for r in hk_banks if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)[0]
    print(f"\nHK Banks: RSI <{best_bank['rsi']}, Hold {best_bank['hold']}d")
    print(f"  Best performer: {best_bank['ticker']} — {best_bank['test_wr']:.1f}% / {best_bank['val_wr']:.1f}%")

if hk_utils:
    best_util = sorted([r for r in hk_utils if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)[0]
    print(f"\nHK Utilities: RSI <{best_util['rsi']}, Hold {best_util['hold']}d")
    print(f"  Best performer: {best_util['ticker']} — {best_util['test_wr']:.1f}% / {best_util['val_wr']:.1f}%")

conn.close()
print('\n' + '='*100)
