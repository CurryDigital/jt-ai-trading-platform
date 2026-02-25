#!/usr/bin/env python3
"""
FULL UNIVERSE GROUPING: S005 Trend Following
ALL tickers that pass, grouped by sector
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd

print('='*100)
print('FULL UNIVERSE GROUPING: S005 Trend Following')
print('Price > SMA(50), Hold 15 days')
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

SMA_DAYS = 50
HOLD_DAYS = 15

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
    df['sma'] = df['close'].rolling(SMA_DAYS).mean()
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(SMA_DAYS, len(test) - HOLD_DAYS):
        if pd.notna(test['sma'].iloc[i]) and test['close'].iloc[i] > test['sma'].iloc[i]:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(SMA_DAYS, len(validate) - HOLD_DAYS):
        if pd.notna(validate['sma'].iloc[i]) and validate['close'].iloc[i] > validate['sma'].iloc[i]:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    return {'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(test_trades), 'val_n': len(val_trades)}

sector_map = {
    '0883.HK': 'HK_Energy', '1810.HK': 'HK_Tech', '0941.HK': 'HK_Telecom',
    '0005.HK': 'HK_Banks', '0939.HK': 'HK_Banks', '3988.HK': 'HK_Banks',
    'JPM': 'US_Banks', 'BAC': 'US_Banks', 'C': 'US_Banks', 'GS': 'US_Banks',
    'GE': 'US_Industrials', 'LMT': 'US_Industrials',
    'NVDA': 'US_Tech', 'GOOGL': 'US_Tech',
}

print('\nTesting all tickers...\n')

sector_results = {}

for ticker, count in all_tickers:
    result = test_ticker(ticker)
    if result is None:
        continue
    
    if result['test_wr'] >= 60 and result['val_wr'] >= 55:
        sector = sector_map.get(ticker, 'Other')
        if sector not in sector_results:
            sector_results[sector] = []
        sector_results[sector].append({'ticker': ticker, **result})

conn.close()

print('='*100)
print(f'S005 Price > SMA({SMA_DAYS}), Hold {HOLD_DAYS}d: ALL PASSING TICKERS')
print('='*100)

total_tickers = 0
for sector in sorted(sector_results.keys()):
    tickers = sector_results[sector]
    if len(tickers) == 0:
        continue
    avg_test = pd.Series([t['test_wr'] for t in tickers]).mean()
    avg_val = pd.Series([t['val_wr'] for t in tickers]).mean()
    print(f'\n{sector}: {len(tickers)} tickers | Avg: {avg_test:.1f}% / {avg_val:.1f}%')
    for t in sorted(tickers, key=lambda x: x['test_wr'], reverse=True):
        print(f"    {t['ticker']:<15} {t['test_wr']:>6.1f}% / {t['val_wr']:>6.1f}%  n={t['test_n']:>3}")
    total_tickers += len(tickers)

print(f'\nTOTAL: {total_tickers} tickers')
print('='*100)
