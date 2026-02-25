#!/usr/bin/env python3
"""
RIGOROUS PARAMETER SWEEP: S004 Volume Spike Breakout
Test volume thresholds: 1.5x, 2x, 2.5x, 3x
Test hold periods: 3, 5, 7, 10 days
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
print('PARAMETER SWEEP: S004 Volume Spike Breakout')
print('Volume: 1.5x, 2x, 2.5x, 3x | Hold: 3, 5, 7, 10 days')
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
    WHERE date >= '2021-01-01' AND volume IS NOT NULL
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

vol_thresholds = [1.5, 2.0, 2.5, 3.0]
hold_periods = [3, 5, 7, 10]

def test_params(ticker, vol_mult, hold_days):
    cursor.execute(f"""
        SELECT date, close::float, volume::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(20, len(test) - hold_days):
        if pd.notna(test['vol_ratio'].iloc[i]) and test['vol_ratio'].iloc[i] > vol_mult:
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
    for i in range(20, len(validate) - hold_days):
        if pd.notna(validate['vol_ratio'].iloc[i]) and validate['vol_ratio'].iloc[i] > vol_mult:
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

print('\nTesting parameter combinations...')

results = []
for ticker in [r[0] for r in all_tickers[:80]]:  # Test 80 tickers
    for vol in vol_thresholds:
        for hold in hold_periods:
            result = test_params(ticker, vol, hold)
            if result:
                results.append({
                    'ticker': ticker,
                    'vol': vol,
                    'hold': hold,
                    **result
                })

# Find best combinations
valid_results = [r for r in results if r['val_wr'] >= 50 and r['test_wr'] >= 60]

print('\n' + '='*100)
print('TOP 20 PARAMETER COMBINATIONS (Volume >Xx, Hold Y days)')
print('='*100)
print(f"{'Rank':<6} {'Ticker':<12} {'Vol':<8} {'Hold':<6} {'Test':<8} {'Val':<8} {'Trades':<8}")
print('-'*80)

for i, r in enumerate(sorted(valid_results, key=lambda x: x['test_wr'], reverse=True)[:20], 1):
    print(f"{i:<6} {r['ticker']:<12} {r['vol']:>6.1f}x {r['hold']:>4}d {r['test_wr']:>6.1f}% {r['val_wr']:>6.1f}% {r['test_n']:>6}")

# Volume threshold analysis
print('\n' + '='*100)
print('VOLUME THRESHOLD ANALYSIS')
print('='*100)

for vol in vol_thresholds:
    vol_results = [r for r in valid_results if r['vol'] == vol]
    if vol_results:
        avg_wr = np.mean([r['test_wr'] for r in vol_results])
        count = len(vol_results)
        print(f"Volume >{vol}x: {count} tickers, Avg Test WR {avg_wr:.1f}%")

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
