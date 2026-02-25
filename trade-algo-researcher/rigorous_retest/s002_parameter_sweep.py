#!/usr/bin/env python3
"""
PARAMETER SWEEP: S002 3-Day Panic Reversal
Test different hold periods: 3, 5, 7, 10, 15 days
Find optimal hold period for each sector
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
print('PARAMETER SWEEP: S002 3-Day Panic Reversal')
print('Testing hold periods: 3, 5, 7, 10, 15 days')
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

# Focus on Property and China EV (best performers for S002)
target_tickers = [
    '0001.HK', '0002.HK', '0016.HK', '0688.HK', '1109.HK', '1113.HK',  # HK Property
    '601398.SS', '601668.SS', '601669.SS',  # China Property/Construction
    '300750.SZ',  # CATL
    '000333.SZ',  # Midea
    '6862.HK',  # Haidilao
]

hold_periods = [3, 5, 7, 10, 15]

def test_params(ticker, hold_days):
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
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(3, len(test) - hold_days):
        if (test['close'].iloc[i-3] > test['close'].iloc[i-2] and
            test['close'].iloc[i-2] > test['close'].iloc[i-1] and
            test['close'].iloc[i-1] > test['close'].iloc[i]):
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
    for i in range(3, len(validate) - hold_days):
        if (validate['close'].iloc[i-3] > validate['close'].iloc[i-2] and
            validate['close'].iloc[i-2] > validate['close'].iloc[i-1] and
            validate['close'].iloc[i-1] > validate['close'].iloc[i]):
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
print('\nTesting hold period variations...\n')

results = []
for ticker in target_tickers:
    for hold_days in hold_periods:
        result = test_params(ticker, hold_days)
        if result:
            results.append({
                'ticker': ticker,
                'hold': hold_days,
                **result
            })

# Find best parameters per ticker
print('='*100)
print('OPTIMAL HOLD PERIODS BY TICKER (Best Test WR with Val WR >= 50%)')
print('='*100)

for ticker in target_tickers:
    ticker_results = [r for r in results if r['ticker'] == ticker]
    if not ticker_results:
        continue
    
    valid_results = [r for r in ticker_results if r['val_wr'] >= 50]
    if valid_results:
        best = sorted(valid_results, key=lambda x: x['test_wr'], reverse=True)[0]
        status = '🏆' if best['test_wr'] >= 65 else '✅'
        print(f"{status} {ticker}: Hold {best['hold']}d | Test {best['test_wr']:.1f}% | Val {best['val_wr']:.1f}% | n={best['test_n']}")

# Overall best combinations
print('\n' + '='*100)
print('TOP 10 HOLD PERIOD COMBINATIONS (Across All Tickers)')
print('='*100)

sorted_results = sorted([r for r in results if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)
for i, r in enumerate(sorted_results[:10], 1):
    print(f"{i:2d}. {r['ticker']} | Hold {r['hold']}d | Test {r['test_wr']:.1f}% | Val {r['val_wr']:.1f}% | n={r['test_n']}")

# Sector summary
print('\n' + '='*100)
print('SECTOR SUMMARY: Optimal Hold Periods')
print('='*100)

hk_property = [r for r in results if r['ticker'] in ['0001.HK', '0002.HK', '0016.HK', '0688.HK', '1109.HK', '1113.HK']]
china_property = [r for r in results if r['ticker'] in ['601398.SS', '601668.SS', '601669.SS']]
china_ev = [r for r in results if r['ticker'] in ['300750.SZ', '000333.SZ']]

if hk_property:
    best = sorted([r for r in hk_property if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)[0]
    print(f"\nHK Property: Hold {best['hold']} days")
    print(f"  Best: {best['ticker']} — {best['test_wr']:.1f}% / {best['val_wr']:.1f}%")

if china_property:
    best = sorted([r for r in china_property if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)[0]
    print(f"\nChina Property: Hold {best['hold']} days")
    print(f"  Best: {best['ticker']} — {best['test_wr']:.1f}% / {best['val_wr']:.1f}%")

if china_ev:
    best = sorted([r for r in china_ev if r['val_wr'] >= 50], key=lambda x: x['test_wr'], reverse=True)[0]
    print(f"\nChina EV/Consumer: Hold {best['hold']} days")
    print(f"  Best: {best['ticker']} — {best['test_wr']:.1f}% / {best['val_wr']:.1f}%")

conn.close()
print('\n' + '='*100)
