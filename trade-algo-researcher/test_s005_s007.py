#!/usr/bin/env python3
"""
S005-S007: Volume Breakout, BB Squeeze, Sector Rotation
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
        elif code in ['0700', '9999', '9618', '9988']:
            return 'HK_Tech'
        else:
            return 'HK_Other'
    elif ticker.endswith('.SZ') or ticker.endswith('.SS'):
        return 'China_A_Shares'
    elif ticker in ['SPY', 'QQQ', 'IWM']:
        return 'US_ETF_Index'
    elif ticker in ['XLF', 'XLK', 'XLE', 'XLU']:
        return 'US_Sector_ETF'
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'PLTR']:
        return 'US_Tech_Growth'
    elif ticker in ['JPM', 'BAC', 'GS', 'MS']:
        return 'US_Banks'
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
print('S005: High Volume Breakout (Vol > 1.5x + Price > SMA20)')
print('='*90)

s005_results = {}

for ticker in valid_tickers[:200]:
    cursor.execute(f"SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades = []
    for i in range(20, len(test) - 5):
        if (pd.notna(test['vol_ratio'].iloc[i]) and test['vol_ratio'].iloc[i] > 1.5 and
            pd.notna(test['sma20'].iloc[i]) and test['close'].iloc[i] > test['sma20'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10: continue
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    val_trades = []
    for i in range(20, len(validate) - 5):
        if (pd.notna(validate['vol_ratio'].iloc[i]) and validate['vol_ratio'].iloc[i] > 1.5 and
            pd.notna(validate['sma20'].iloc[i]) and validate['close'].iloc[i] > validate['sma20'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    if len(val_trades) < 5: continue
    val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s005_results:
            s005_results[sector] = []
        s005_results[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr})

for sector, tickers in sorted(s005_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    print(f"{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}%")
    for t in tickers[:3]:
        print(f"  {t['ticker']}: Test {t['test_wr']:.1f}%")

print(f"\nS005 passing: {sum(len(v) for v in s005_results.values())} tickers")

print('\n' + '='*90)
print('S006: Bollinger Band Squeeze')
print('='*90)

s006_results = {}

for ticker in valid_tickers[:200]:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_width'] = df['std20'] / df['sma20'] * 100
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades = []
    for i in range(60, len(test) - 5):
        width_pctile = test['bb_width'].iloc[i-60:i].quantile(0.2)
        if pd.notna(test['bb_width'].iloc[i]) and test['bb_width'].iloc[i] < width_pctile:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10: continue
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    val_trades = []
    for i in range(60, len(validate) - 5):
        width_pctile = validate['bb_width'].iloc[i-60:i].quantile(0.2)
        if pd.notna(validate['bb_width'].iloc[i]) and validate['bb_width'].iloc[i] < width_pctile:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    if len(val_trades) < 5: continue
    val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s006_results:
            s006_results[sector] = []
        s006_results[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr})

for sector, tickers in sorted(s006_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    print(f"{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}%")

print(f"\nS006 passing: {sum(len(v) for v in s006_results.values())} tickers")

print('\n' + '='*90)
print('S007: Sector Rotation (XLK/XLF)')
print('='*90)

cursor.execute("SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
xlk_data = cursor.fetchall()
cursor.execute("SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLF' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
xlf_data = cursor.fetchall()

if xlk_data and xlf_data:
    xlk = pd.DataFrame(xlk_data, columns=['date', 'close'])
    xlf = pd.DataFrame(xlf_data, columns=['date', 'close'])
    xlk['date'] = pd.to_datetime(xlk['date'])
    xlf['date'] = pd.to_datetime(xlf['date'])
    
    df = pd.merge(xlk, xlf, on='date', suffixes=('_xlk', '_xlf'))
    df['ratio'] = df['close_xlk'] / df['close_xlf']
    df['ratio_sma20'] = df['ratio'].rolling(20).mean()
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades = []
    for i in range(20, len(test) - 10):
        if pd.notna(test['ratio_sma20'].iloc[i]) and test['ratio'].iloc[i] > test['ratio_sma20'].iloc[i]:
            entry = test['close_xlk'].iloc[i]
            exit_p = test['close_xlk'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    val_trades = []
    for i in range(20, len(validate) - 10):
        if pd.notna(validate['ratio_sma20'].iloc[i]) and validate['ratio'].iloc[i] > validate['ratio_sma20'].iloc[i]:
            entry = validate['close_xlk'].iloc[i]
            exit_p = validate['close_xlk'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    print(f"XLK/XLF: Test {test_wr:.1f}% | Val {val_wr:.1f}% | Trades {len(trades)}")
    if test_wr >= 60 and val_wr >= 55:
        print("🏆 GOLDEN")

conn.close()

print('\n' + '='*90)
print('SUMMARY S005-S007')
print('='*90)
print(f"S005 Volume Breakout: {sum(len(v) for v in s005_results.values())} tickers")
print(f"S006 BB Squeeze: {sum(len(v) for v in s006_results.values())} tickers")
print("S007 Sector Rotation: Tested (XLK/XLF only)")
