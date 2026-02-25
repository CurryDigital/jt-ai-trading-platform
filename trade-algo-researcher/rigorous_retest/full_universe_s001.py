#!/usr/bin/env python3
"""
RIGOROUS FULL UNIVERSE TEST: S001-Candidate
RSI(14) < 25, Hold 10 days
Report ALL results: PASS, FAIL, INSUFFICIENT
NO cherry-picking
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
print('RIGOROUS FULL UNIVERSE TEST: S001-Candidate')
print('RSI(14) < 25, Hold 10 days')
print('REPORTING ALL RESULTS — PASS AND FAIL')
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

# Get all tickers
cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

print(f'\nTotal tickers to test: {len(all_tickers)}')
print('\n' + '='*100)

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_ticker(ticker):
    """Test S001-Candidate on single ticker — report full results"""
    cursor.execute(f"""
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return {'status': 'INSUFFICIENT_DATA', 'test_wr': 0, 'val_wr': 0, 'test_n': 0, 'val_n': 0, 'ticker': ticker}
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    # Test period: 2023-2024
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(14, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return {'status': 'INSUFFICIENT_SIGNALS', 'test_wr': 0, 'val_wr': 0, 'test_n': len(test_trades), 'val_n': 0, 'ticker': ticker}
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period: 2025+
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(14, len(validate) - 10):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 25:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
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

# Sort by win rate
results_sorted = sorted(results, key=lambda x: x['test_wr'], reverse=True)

# Print ALL results
print('\n' + '='*100)
print('FULL RESULTS (sorted by Test Win Rate)')
print('='*100)
print(f"{'Ticker':<15} {'Status':<18} {'Test WR':<10} {'Val WR':<10} {'Test n':<8} {'Val n':<8}")
print('-'*100)

for r in results_sorted:
    print(f"{r['ticker']:<15} {r['status']:<18} {r['test_wr']:>8.1f}% {r['val_wr']:>8.1f}% {r['test_n']:>6} {r['val_n']:>6}")

# Summary
print('\n' + '='*100)
print('SUMMARY')
print('='*100)

golden = [r for r in results if r['status'] == 'GOLDEN']
validated = [r for r in results if r['status'] == 'VALIDATED']
marginal = [r for r in results if r['status'] == 'MARGINAL']
fail = [r for r in results if r['status'] == 'FAIL']
insufficient = [r for r in results if 'INSUFFICIENT' in r['status']]

print(f"GOLDEN (Test >=60%, Val >=55%): {len(golden)} tickers")
for r in golden[:5]:
    print(f"  {r['ticker']}: {r['test_wr']:.1f}% / {r['val_wr']:.1f}%")

print(f"\nVALIDATED (Test >=55%): {len(validated)} tickers")
for r in validated[:5]:
    print(f"  {r['ticker']}: {r['test_wr']:.1f}% / {r['val_wr']:.1f}%")

print(f"\nMARGINAL (Test >=50%): {len(marginal)} tickers")
print(f"\nFAIL (Test <50%): {len(fail)} tickers")
print(f"\nINSUFFICIENT: {len(insufficient)} tickers")

print(f"\nTotal tested: {len(results)}")
print(f"Pass rate (Golden + Validated): {(len(golden) + len(validated))/len(results)*100:.1f}%")

conn.close()

print('\n' + '='*100)
print('HONEST ASSESSMENT:')
print('='*100)
if len(golden) >= 3:
    print(f'✓ Found {len(golden)} tickers with strong performance')
    print('✓ Proceed to sector analysis')
elif len(golden) + len(validated) >= 5:
    print(f'✓ Found {len(golden) + len(validated)} tickers with decent performance')
    print('✓ May be viable with tight risk management')
else:
    print(f'✗ Only {len(golden) + len(validated)} tickers pass minimum criteria')
    print('✗ Strategy may not be viable — consider abandoning')
