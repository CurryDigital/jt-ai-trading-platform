#!/usr/bin/env python3
"""
RIGOROUS TEST: S004-Candidate — Volume Spike Breakout
Volume >2x 20-day average, Hold 5 days
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
print('RIGOROUS TEST: S004-Candidate (Volume Spike Breakout)')
print('Volume >2x 20-day average, Hold 5 days')
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

# Get all tickers with volume data
cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01' AND volume IS NOT NULL
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

print(f'\nTesting {len(all_tickers)} tickers with volume data...')

def test_ticker(ticker):
    cursor.execute(f"""
        SELECT date, close::float, volume::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return {'status': 'INSUFFICIENT_DATA', 'ticker': ticker}
    
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    # Test period: 2023-2024
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(20, len(test) - 5):
        if pd.notna(test['vol_ratio'].iloc[i]) and test['vol_ratio'].iloc[i] > 2.0:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return {'status': 'INSUFFICIENT_SIGNALS', 'test_n': len(test_trades), 'ticker': ticker}
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period: 2025+
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(20, len(validate) - 5):
        if pd.notna(validate['vol_ratio'].iloc[i]) and validate['vol_ratio'].iloc[i] > 2.0:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    val_n = len(val_trades)
    
    # Classification
    if test_wr >= 60 and val_wr >= 55 and val_n >= 5:
        status = 'GOLDEN'
    elif test_wr >= 55 and val_n >= 5:
        status = 'VALIDATED'
    elif test_wr >= 50:
        status = 'MARGINAL'
    else:
        status = 'FAIL'
    
    return {
        'status': status,
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': val_n,
        'ticker': ticker
    }

# Test ALL tickers
results = []
for i, (ticker, count) in enumerate(all_tickers):
    result = test_ticker(ticker)
    results.append(result)
    if (i + 1) % 50 == 0:
        print(f'Progress: {i+1}/{len(all_tickers)}...')

# Summary
golden = [r for r in results if r.get('status') == 'GOLDEN']
validated = [r for r in results if r.get('status') == 'VALIDATED']
marginal = [r for r in results if r.get('status') == 'MARGINAL']
fail = [r for r in results if r.get('status') == 'FAIL']
insufficient = [r for r in results if 'INSUFFICIENT' in r.get('status', '')]

print('\n' + '='*100)
print('S004-Candidate RESULTS (Volume Spike >2x)')
print('='*100)
print(f'GOLDEN: {len(golden)} tickers')
for r in golden[:10]:
    print(f"  {r['ticker']}: {r['test_wr']:.1f}% / {r['val_wr']:.1f}% (n={r['test_n']})")

print(f"\nVALIDATED: {len(validated)} tickers")
for r in validated[:10]:
    print(f"  {r['ticker']}: {r['test_wr']:.1f}% / {r['val_wr']:.1f}%")

print(f"\nMARGINAL: {len(marginal)} tickers")
print(f"FAIL: {len(fail)} tickers")
print(f"INSUFFICIENT: {len(insufficient)} tickers")

print(f"\nPass rate (Golden + Validated): {(len(golden) + len(validated))/len([r for r in results if 'test_wr' in r])*100:.1f}%")

conn.close()

print('\n' + '='*100)
