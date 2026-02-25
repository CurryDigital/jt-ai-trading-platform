#!/usr/bin/env python3
"""
COMBINED STRATEGY: S001 + S002
3 consecutive down days AND RSI < 25
Buy Day 3, Hold 5-10 days
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
print('COMBINED STRATEGY: S001 + S002')
print('3-Day Panic + RSI <25, Hold 5-10 days')
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

# Test on best performers from both strategies
target_tickers = [
    '0005.HK', '1398.HK', '3988.HK', '3328.HK',  # S001 Banks
    '0002.HK',  # S001 Utilities + S002 Property
    '0001.HK', '0016.HK',  # S002 Property
    '601398.SS', '601668.SS',  # S002 China Property
]

hold_periods = [5, 7, 10]

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_combined(ticker, hold_days):
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
        # Combined condition: 3-day down AND RSI < 25
        if (test['close'].iloc[i-3] > test['close'].iloc[i-2] and
            test['close'].iloc[i-2] > test['close'].iloc[i-1] and
            test['close'].iloc[i-1] > test['close'].iloc[i] and
            pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 3:  # Lower threshold for combined (rarer signals)
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(14, len(validate) - hold_days):
        if (validate['close'].iloc[i-3] > validate['close'].iloc[i-2] and
            validate['close'].iloc[i-2] > validate['close'].iloc[i-1] and
            validate['close'].iloc[i-1] > validate['close'].iloc[i] and
            pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 25):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 2 else 0
    
    return {
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

print('\nTesting combined strategy...\n')

results = []
for ticker in target_tickers:
    for hold_days in hold_periods:
        result = test_combined(ticker, hold_days)
        if result:
            results.append({
                'ticker': ticker,
                'hold': hold_days,
                **result
            })

print('='*100)
print('COMBINED STRATEGY RESULTS (3-Day Panic + RSI <25)')
print('='*100)

# Compare vs individual strategies
print(f"\n{'Ticker':<12} {'Hold':<6} {'Test WR':<10} {'Val WR':<10} {'Trades':<8} {'Status':<12}")
print('-'*80)

for r in sorted(results, key=lambda x: x['test_wr'], reverse=True):
    if r['val_wr'] >= 50:
        status = '🏆 GOLDEN' if r['test_wr'] >= 70 else '✅ VALID'
    else:
        status = '🟡 MARGINAL' if r['test_wr'] >= 60 else '❌ WEAK'
    print(f"{r['ticker']:<12} {r['hold']:<6} {r['test_wr']:>8.1f}% {r['val_wr']:>8.1f}% {r['test_n']:>6} {status:<12}")

# Summary
print('\n' + '='*100)
print('COMPARISON: Combined vs Individual Strategies')
print('='*100)

golden_combined = [r for r in results if r['test_wr'] >= 70 and r['val_wr'] >= 50]
print(f"\nCombined Strategy (3-day + RSI<25):")
print(f"  GOLDEN tickers: {len(golden_combined)}")
for r in golden_combined:
    print(f"    {r['ticker']}: {r['test_wr']:.1f}% / {r['val_wr']:.1f}% (n={r['test_n']})")

print(f"\nNote: Combined strategy produces fewer signals (rarer) but potentially higher quality.")

conn.close()
print('\n' + '='*100)
