#!/usr/bin/env python3
"""
FULL UNIVERSE GROUPING: S002 3-Day Panic Reversal
ALL tickers that pass 3-tier backtesting, grouped by sector
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
print('FULL UNIVERSE GROUPING: S002 3-Day Panic Reversal')
print('3 consecutive down days, Buy Day 3, Hold 5 days')
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

# Use optimal hold period of 5 days
HOLD_DAYS = 5

def test_ticker(ticker):
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
    for i in range(3, len(test) - HOLD_DAYS):
        if (test['close'].iloc[i-3] > test['close'].iloc[i-2] and
            test['close'].iloc[i-2] > test['close'].iloc[i-1] and
            test['close'].iloc[i-1] > test['close'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(3, len(validate) - HOLD_DAYS):
        if (validate['close'].iloc[i-3] > validate['close'].iloc[i-2] and
            validate['close'].iloc[i-2] > validate['close'].iloc[i-1] and
            validate['close'].iloc[i-1] > validate['close'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    return {
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

# Industry classification
sector_map = {
    '0001.HK': 'HK_Property', '0002.HK': 'HK_Property', '0016.HK': 'HK_Property',
    '0688.HK': 'HK_Property', '1109.HK': 'HK_Property', '1113.HK': 'HK_Property',
    '0083.HK': 'HK_Property', '0101.HK': 'HK_Property', '0197.HK': 'HK_Property',
    '601668.SS': 'CN_Property', '601669.SS': 'CN_Property', '601888.SS': 'CN_Property',
    '601186.SS': 'CN_Property', '000333.SZ': 'CN_Property',
    '300750.SZ': 'CN_EV', '002594.SZ': 'CN_EV', '1211.HK': 'CN_EV',
    '601398.SS': 'CN_Banks', '601939.SS': 'CN_Banks', '601988.SS': 'CN_Banks',
    '0005.HK': 'HK_Banks', '0939.HK': 'HK_Banks', '1398.HK': 'HK_Banks',
    '3328.HK': 'HK_Banks', '3988.HK': 'HK_Banks',
    '0002.HK': 'HK_Utilities', '0003.HK': 'HK_Utilities', '0006.HK': 'HK_Utilities',
    '6862.HK': 'HK_Consumer', '2319.HK': 'HK_Consumer', '1929.HK': 'HK_Consumer',
    '0700.HK': 'HK_Tech', '9988.HK': 'HK_Tech', '1810.HK': 'HK_Tech', '1024.HK': 'HK_Tech',
    '0883.HK': 'HK_Energy', '0386.HK': 'HK_Energy', '0857.HK': 'HK_Energy',
    '600028.SS': 'CN_Energy', '601088.SS': 'CN_Energy',
    '2318.HK': 'HK_Insurance', '1299.HK': 'HK_Insurance', '2628.HK': 'HK_Insurance',
    '0066.HK': 'HK_Transport',
}

print('\nTesting all tickers...\n')

sector_results = {}

for ticker, count in all_tickers:
    result = test_ticker(ticker)
    if result is None:
        continue
    
    if result['test_wr'] >= 55 and result['val_wr'] >= 50:
        sector = sector_map.get(ticker, 'Other')
        
        if sector not in sector_results:
            sector_results[sector] = []
        
        sector_results[sector].append({
            'ticker': ticker,
            **result
        })

conn.close()

print('='*100)
print(f'S002 3-Day Panic (Hold {HOLD_DAYS}d): ALL PASSING TICKERS BY SECTOR')
print('Pass criteria: Test >=55%, Val >=50%, n >=10')
print('='*100)

total_tickers = 0
for sector in sorted(sector_results.keys()):
    tickers = sector_results[sector]
    if len(tickers) == 0:
        continue
    
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_test_n = sum([t['test_n'] for t in tickers])
    
    print(f'\n{sector}: {len(tickers)} tickers')
    print(f'  Avg: Test {avg_test:.1f}% | Val {avg_val:.1f}% | Total Trades: {total_test_n}')
    print('  Tickers:')
    for t in sorted(tickers, key=lambda x: x['test_wr'], reverse=True):
        print(f"    {t['ticker']:<15} Test: {t['test_wr']:>6.1f}%  Val: {t['val_wr']:>6.1f}%  n={t['test_n']:>3}")
    
    total_tickers += len(tickers)

print('\n' + '='*100)
print(f'TOTAL: {total_tickers} tickers across {len([s for s in sector_results if sector_results[s]])} sectors')
print('='*100)

# Grouping recommendations
print('\n' + '='*100)
print('STRATEGY GROUPING RECOMMENDATIONS')
print('='*100)

major_sectors = {k: v for k, v in sector_results.items() if len(v) >= 3}

print('\n🏆 MAJOR GROUPINGS:')
for sector in sorted(major_sectors.keys()):
    tickers = major_sectors[sector]
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    ticker_list = [t['ticker'] for t in tickers]
    print(f'\n  S002-{sector}: {len(tickers)} tickers')
    print(f'    {", ".join(ticker_list)}')
    print(f'    Avg: {avg_test:.1f}% test / {avg_val:.1f}% val')

minor_sectors = {k: v for k, v in sector_results.items() if 0 < len(v) < 3}
if minor_sectors:
    print('\n🟡 MINOR GROUPINGS (Combine into S002-Others):')
    for sector in sorted(minor_sectors.keys()):
        tickers = minor_sectors[sector]
        ticker_list = [t['ticker'] for t in tickers]
        print(f'  {sector}: {", ".join(ticker_list)}')

print('\n' + '='*100)
