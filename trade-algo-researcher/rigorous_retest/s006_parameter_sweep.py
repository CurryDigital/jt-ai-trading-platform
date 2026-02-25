#!/usr/bin/env python3
"""
RIGOROUS PARAMETER SWEEP: S006 Monday Effect
Test hold periods: 3, 5, 7, 10 days
Test Friday decline thresholds: -1%, -2%, -3%
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
print('PARAMETER SWEEP: S006 Monday Effect')
print('Friday decline: -1%, -2%, -3% | Hold: 3, 5, 7, 10 days')
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

friday_thresholds = [-1.0, -2.0, -3.0]
hold_periods = [3, 5, 7, 10]

def test_params(ticker, friday_thresh, hold_days):
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
    df['day_of_week'] = df['date'].dt.dayofweek
    df['prev_close'] = df['close'].shift(1)
    df['ret'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
    
    # Find Mondays where previous Friday was down > threshold
    df['signal'] = False
    for i in range(1, len(df)):
        if df['day_of_week'].iloc[i] == 0:  # Monday
            for j in range(i-1, max(0, i-5), -1):
                if df['day_of_week'].iloc[j] == 4:  # Friday
                    if df['ret'].iloc[j] < friday_thresh:
                        df.loc[i, 'signal'] = True
                    break
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(len(test) - hold_days):
        if test['signal'].iloc[i]:
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
    for i in range(len(validate) - hold_days):
        if validate['signal'].iloc[i]:
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
for ticker in [r[0] for r in all_tickers[:50]]:  # Test 50 tickers
    for thresh in friday_thresholds:
        for hold in hold_periods:
            result = test_params(ticker, thresh, hold)
            if result:
                results.append({
                    'ticker': ticker,
                    'thresh': thresh,
                    'hold': hold,
                    **result
                })

# Find best combinations
valid_results = [r for r in results if r['val_wr'] >= 50 and r['test_wr'] >= 60]

print('\n' + '='*100)
print('TOP 15 PARAMETER COMBINATIONS (Friday <X%, Hold Y days)')
print('='*100)
print(f"{'Rank':<6} {'Ticker':<12} {'Thresh':<8} {'Hold':<6} {'Test':<8} {'Val':<8} {'Trades':<8}")
print('-'*80)

for i, r in enumerate(sorted(valid_results, key=lambda x: x['test_wr'], reverse=True)[:15], 1):
    print(f"{i:<6} {r['ticker']:<12} {r['thresh']:>6.1f}% {r['hold']:>4}d {r['test_wr']:>6.1f}% {r['val_wr']:>6.1f}% {r['test_n']:>6}")

# Friday threshold analysis
print('\n' + '='*100)
print('FRIDAY DECLINE THRESHOLD ANALYSIS')
print('='*100)

for thresh in friday_thresholds:
    thresh_results = [r for r in valid_results if r['thresh'] == thresh]
    if thresh_results:
        avg_wr = np.mean([r['test_wr'] for r in thresh_results])
        count = len(thresh_results)
        print(f"Friday <{thresh}%: {count} tickers, Avg Test WR {avg_wr:.1f}%")

conn.close()
print('\n' + '='*100)
