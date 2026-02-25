#!/usr/bin/env python3
"""
FULL UNIVERSE GROUPING: S003 Gap Down Recovery
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
print('FULL UNIVERSE GROUPING: S003 Gap Down Recovery')
print('Gap >2%, Hold 3 days')
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
    WHERE date >= '2021-01-01' AND open IS NOT NULL
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

GAP_PCT = 2.0
HOLD_DAYS = 3

def test_ticker(ticker):
    cursor.execute(f"""
        SELECT date, open::float, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'open', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['prev_close'] = df['close'].shift(1)
    df['gap'] = (df['open'] - df['prev_close']) / df['prev_close'] * 100
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(1, len(test) - HOLD_DAYS):
        if pd.notna(test['gap'].iloc[i]) and test['gap'].iloc[i] < -GAP_PCT:
            entry = test['open'].iloc[i]
            exit_p = test['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 5:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(1, len(validate) - HOLD_DAYS):
        if pd.notna(validate['gap'].iloc[i]) and validate['gap'].iloc[i] < -GAP_PCT:
            entry = validate['open'].iloc[i]
            exit_p = validate['close'].iloc[i + HOLD_DAYS]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 3 else 0
    
    return {'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(test_trades), 'val_n': len(val_trades)}

sector_map = {
    '0883.HK': 'HK_Energy', '0386.HK': 'HK_Energy', '0857.HK': 'HK_Energy',
    '1044.HK': 'HK_Consumer', '2319.HK': 'HK_Consumer', '6862.HK': 'HK_Consumer',
    '1810.HK': 'HK_Tech', '0700.HK': 'HK_Tech', '1024.HK': 'HK_Tech',
    '2313.HK': 'HK_Consumer', '1299.HK': 'HK_Insurance',
    '1211.HK': 'CN_EV', '2688.HK': 'HK_Energy',
    'NVDA': 'US_Tech', 'TSLA': 'US_EV', 'COIN': 'Crypto', 'PLTR': 'US_Tech',
}

print('\nTesting all tickers...\n')

sector_results = {}

for ticker, count in all_tickers:
    result = test_ticker(ticker)
    if result is None:
        continue
    
    if result['test_wr'] >= 60 and result['val_wr'] >= 50:
        sector = sector_map.get(ticker, 'Other')
        if sector not in sector_results:
            sector_results[sector] = []
        sector_results[sector].append({'ticker': ticker, **result})

conn.close()

print('='*100)
print(f'S003 Gap >{GAP_PCT}%, Hold {HOLD_DAYS}d: ALL PASSING TICKERS')
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
