#!/usr/bin/env python3
"""
RIGOROUS PARAMETER SWEEP: S005 Trend Following
Test SMA periods: 20, 30, 50, 100
Test hold periods: 5, 10, 15 days
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
print('PARAMETER SWEEP: S005 Trend Following')
print('SMA: 20, 30, 50, 100 | Hold: 5, 10, 15 days')
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

cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

sma_periods = [20, 30, 50, 100]
hold_periods = [5, 10, 15]

def test_params(ticker, sma_days, hold_days):
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
    df['sma'] = df['close'].rolling(sma_days).mean()
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(sma_days, len(test) - hold_days):
        if pd.notna(test['sma'].iloc[i]) and test['close'].iloc[i] > test['sma'].iloc[i]:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(sma_days, len(validate) - hold_days):
        if pd.notna(validate['sma'].iloc[i]) and validate['close'].iloc[i] > validate['sma'].iloc[i]:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    return {
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

print('\nTesting parameter combinations...')

results = []
for ticker in [r[0] for r in all_tickers[:60]]:  # Test 60 tickers
    for sma in sma_periods:
        for hold in hold_periods:
            result = test_params(ticker, sma, hold)
            if result:
                results.append({
                    'ticker': ticker,
                    'sma': sma,
                    'hold': hold,
                    **result
                })

# Find best combinations
valid_results = [r for r in results if r['val_wr'] >= 50 and r['test_wr'] >= 60]

print('\n' + '='*100)
print('TOP 20 PARAMETER COMBINATIONS (SMA X, Hold Y days)')
print('='*100)
print(f"{'Rank':<6} {'Ticker':<12} {'SMA':<8} {'Hold':<6} {'Test':<8} {'Val':<8} {'Trades':<8}")
print('-'*80)

for i, r in enumerate(sorted(valid_results, key=lambda x: x['test_wr'], reverse=True)[:20], 1):
    print(f"{i:<6} {r['ticker']:<12} {r['sma']:>6}d {r['hold']:>4}d {r['test_wr']:>6.1f}% {r['val_wr']:>6.1f}% {r['test_n']:>6}")

# SMA period analysis
print('\n' + '='*100)
print('SMA PERIOD ANALYSIS')
print('='*100)

for sma in sma_periods:
    sma_results = [r for r in valid_results if r['sma'] == sma]
    if sma_results:
        avg_wr = np.mean([r['test_wr'] for r in sma_results])
        count = len(sma_results)
        print(f"SMA {sma}: {count} tickers, Avg Test WR {avg_wr:.1f}%")

# Hold period analysis
print('\n' + '='*100)
print('HOLD PERIOD ANALYSIS')
print('='*100)

for hold in hold_periods:
    hold_results = [r for r in valid_results if r['hold'] == hold]
    if hold_results:
        avg_wr = np.mean([r['test_wr'] for r in hold_results])
        count = len(hold_results)
        print(f"Hold {hold} days: {count} tickers, Avg Test WR {avg_wr:.1f}%")

conn.close()
print('\n' + '='*100)
