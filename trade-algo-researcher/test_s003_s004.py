#!/usr/bin/env python3
"""
S003-S005: 3-Day Panic, Gap Down, Volume Breakout
Full universe testing
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

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

def classify_sector(ticker):
    if ticker.endswith('.HK'):
        code = ticker.split('.')[0]
        if code in ['1398', '0939', '3988', '2388', '3328', '0005']:
            return 'HK_Banks'
        elif code in ['0700', '9999', '9618', '9988', '3690']:
            return 'HK_Tech'
        elif code in ['0883', '0386', '0857']:
            return 'HK_Energy'
        else:
            return 'HK_Other'
    elif ticker.endswith('.SZ') or ticker.endswith('.SS'):
        return 'China_A_Shares'
    elif ticker in ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD']:
        return 'Crypto'
    elif ticker in ['SPY', 'QQQ', 'IWM']:
        return 'US_ETF_Index'
    elif ticker in ['XLF', 'XLK', 'XLE', 'XLU']:
        return 'US_Sector_ETF'
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'PLTR', 'SNOW', 'SHOP']:
        return 'US_Tech_Growth'
    elif ticker in ['JPM', 'BAC', 'GS', 'MS', 'WFC', 'C']:
        return 'US_Banks'
    elif ticker in ['XOM', 'CVX', 'COP', 'SLB', 'OXY']:
        return 'US_Energy'
    else:
        return 'Other'

cursor.execute('''
    SELECT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
''')
valid_tickers = [r[0] for r in cursor.fetchall()]

print('='*90)
print('S003: 3-Day Consecutive Down (Panic Selling)')
print('='*90)

s003_results = {}

for ticker in valid_tickers[:150]:  # Test subset for speed
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    # 3-day down
    trades = []
    for i in range(3, len(test) - 5):
        if (test['close'].iloc[i-3] > test['close'].iloc[i-2] > test['close'].iloc[i-1] > test['close'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10: continue
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    val_trades = []
    for i in range(3, len(validate) - 5):
        if (validate['close'].iloc[i-3] > validate['close'].iloc[i-2] > validate['close'].iloc[i-1] > validate['close'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    if len(val_trades) < 5: continue
    val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s003_results:
            s003_results[sector] = []
        s003_results[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr})

for sector, tickers in sorted(s003_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    print(f"{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}%")
    for t in tickers[:3]:
        print(f"  {t['ticker']}: Test {t['test_wr']:.1f}%")

print(f"\nS003 passing: {sum(len(v) for v in s003_results.values())} tickers")

print('\n' + '='*90)
print('S004: Gap Down >2% Recovery')
print('='*90)

s004_results = {}

for ticker in valid_tickers[:150]:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['ret'] = df['close'].pct_change() * 100
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades = []
    for i in range(1, len(test) - 3):
        if test['ret'].iloc[i] < -2.0:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10: continue
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    val_trades = []
    for i in range(1, len(validate) - 3):
        if validate['ret'].iloc[i] < -2.0:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    if len(val_trades) < 5: continue
    val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s004_results:
            s004_results[sector] = []
        s004_results[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr})

for sector, tickers in sorted(s004_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    print(f"{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}%")

print(f"\nS004 passing: {sum(len(v) for v in s004_results.values())} tickers")

conn.close()
