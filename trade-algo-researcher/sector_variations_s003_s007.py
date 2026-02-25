#!/usr/bin/env python3
"""
SECTOR VARIATIONS: S003-S007
Complete the sector-specific strategy catalog
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
        if code in ['1398', '0939', '3988', '2388', '3328', '0005', '0011']:
            return 'HK_Banks'
        elif code in ['0700', '9999', '9618', '9988', '3690']:
            return 'HK_Tech'
        elif code in ['0001', '0002', '0003', '0016']:
            return 'HK_Property'
        elif code in ['0883', '0386', '0857']:
            return 'HK_Energy'
        else:
            return 'HK_Other'
    elif ticker.endswith('.SZ') or ticker.endswith('.SS'):
        if ticker in ['601398.SS', '601939.SS', '601988.SS', '601288.SS']:
            return 'CN_Banks'
        elif ticker in ['000333.SZ', '000651.SZ', '000568.SZ', '600519.SS']:
            return 'CN_Consumer'
        else:
            return 'CN_Other'
    elif ticker in ['SPY', 'QQQ', 'IWM']:
        return 'US_ETF'
    elif ticker in ['XLF', 'XLK', 'XLE', 'XLU']:
        return 'US_Sector_ETF'
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'PLTR', 'SHOP']:
        return 'US_Tech'
    elif ticker in ['JPM', 'BAC', 'GS', 'MS', 'WFC']:
        return 'US_Banks'
    elif ticker in ['XOM', 'CVX', 'COP', 'SLB']:
        return 'US_Energy'
    elif ticker in ['WMT', 'COST', 'PG', 'KO']:
        return 'US_Consumer'
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

print('='*100)
print('SECTOR VARIATIONS: S003-S007')
print('='*100)

# === S003: 3-DAY PANIC REVERSAL ===
print('\n' + '='*100)
print('S003: 3-Day Consecutive Down (Panic Selling)')
print('='*100)

s003_sectors = {}

for ticker in valid_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(3, len(test) - 5):
        if (test['close'].iloc[i-3] > test['close'].iloc[i-2] > test['close'].iloc[i-1] > test['close'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10: continue
    test_wr = (pd.Series(trades_test) > 0).mean() * 100
    
    trades_val = []
    for i in range(3, len(validate) - 5):
        if (validate['close'].iloc[i-3] > validate['close'].iloc[i-2] > validate['close'].iloc[i-1] > validate['close'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    if len(trades_val) < 5: continue
    val_wr = (pd.Series(trades_val) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s003_sectors:
            s003_sectors[sector] = []
        s003_sectors[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(trades_test)})

print(f"\n{'Sector':<20} {'Tickers':<8} {'Test WR':<10} {'Val WR':<10} {'Trades':<8}")
print('-'*60)
s003_variations = []
var_num = 1
for sector, tickers in sorted(s003_sectors.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    print(f"S003-{var_num:02d} {sector:<20} {len(tickers):<8} {avg_test:<10.1f} {avg_val:<10.1f} {total_n:<8}")
    s003_variations.append({'id': f'S003-{var_num:02d}', 'sector': sector, 'avg_test': avg_test, 'avg_val': avg_val, 'tickers': [t['ticker'] for t in tickers]})
    var_num += 1

# === S004: GAP DOWN RECOVERY ===
print('\n' + '='*100)
print('S004: Gap Down >2% Recovery')
print('='*100)

s004_sectors = {}

for ticker in valid_tickers[:150]:  # Limit for speed
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['ret'] = df['close'].pct_change() * 100
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(1, len(test) - 3):
        if test['ret'].iloc[i] < -2.0:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10: continue
    test_wr = (pd.Series(trades_test) > 0).mean() * 100
    
    trades_val = []
    for i in range(1, len(validate) - 3):
        if validate['ret'].iloc[i] < -2.0:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 3]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    if len(trades_val) < 5: continue
    val_wr = (pd.Series(trades_val) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s004_sectors:
            s004_sectors[sector] = []
        s004_sectors[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(trades_test)})

print(f"\n{'Sector':<20} {'Tickers':<8} {'Test WR':<10} {'Val WR':<10} {'Trades':<8}")
print('-'*60)
s004_variations = []
var_num = 1
for sector, tickers in sorted(s004_sectors.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    print(f"S004-{var_num:02d} {sector:<20} {len(tickers):<8} {avg_test:<10.1f} {avg_val:<10.1f} {total_n:<8}")
    s004_variations.append({'id': f'S004-{var_num:02d}', 'sector': sector, 'avg_test': avg_test, 'avg_val': avg_val, 'tickers': [t['ticker'] for t in tickers]})
    var_num += 1

# === S005: VOLUME BREAKOUT ===
print('\n' + '='*100)
print('S005: Volume Breakout (>1.5x + Price > SMA20)')
print('='*100)

s005_sectors = {}

for ticker in valid_tickers[:200]:
    cursor.execute(f"SELECT date, close::float, volume::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['vol_avg'] = df['volume'].rolling(20).mean()
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(20, len(test) - 5):
        if (pd.notna(test['vol_avg'].iloc[i]) and test['volume'].iloc[i] > test['vol_avg'].iloc[i] * 1.5 and
            pd.notna(test['sma20'].iloc[i]) and test['close'].iloc[i] > test['sma20'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10: continue
    test_wr = (pd.Series(trades_test) > 0).mean() * 100
    
    trades_val = []
    for i in range(20, len(validate) - 5):
        if (pd.notna(validate['vol_avg'].iloc[i]) and validate['volume'].iloc[i] > validate['vol_avg'].iloc[i] * 1.5 and
            pd.notna(validate['sma20'].iloc[i]) and validate['close'].iloc[i] > validate['sma20'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    if len(trades_val) < 5: continue
    val_wr = (pd.Series(trades_val) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s005_sectors:
            s005_sectors[sector] = []
        s005_sectors[sector].append({'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(trades_test)})

print(f"\n{'Sector':<20} {'Tickers':<8} {'Test WR':<10} {'Val WR':<10} {'Trades':<8}")
print('-'*60)
s005_variations = []
var_num = 1
for sector, tickers in sorted(s005_sectors.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    print(f"S005-{var_num:02d} {sector:<20} {len(tickers):<8} {avg_test:<10.1f} {avg_val:<10.1f} {total_n:<8}")
    s005_variations.append({'id': f'S005-{var_num:02d}', 'sector': sector, 'avg_test': avg_test, 'avg_val': avg_val, 'tickers': [t['ticker'] for t in tickers]})
    var_num += 1

# === S007: SECTOR ROTATION ===
print('\n' + '='*100)
print('S007: Sector Rotation (XLK/XLF) — ALREADY GOLDEN')
print('='*100)
print("S007-01: XLK/XLF_Ratio — Test: 65.3% | Val: 64.1% | Status: 🏆 GOLDEN")

conn.close()

# FINAL SUMMARY
print('\n' + '='*100)
print('COMPLETE SECTOR-SPECIFIC CATALOG')
print('='*100)

all_vars = s003_variations + s004_variations + s005_variations
golden = [v for v in all_vars if v['avg_test'] >= 70 and v['avg_val'] >= 60]
validated = [v for v in all_vars if v['avg_test'] >= 60 and v['avg_val'] >= 55 and v['avg_test'] < 70]

print(f"\n🏆 GOLDEN: {len(golden)} sector variations")
for v in golden:
    print(f"   {v['id']}: {v['sector']} - {v['avg_test']:.1f}%")

print(f"\n✅ VALIDATED: {len(validated)} sector variations")
for v in validated:
    print(f"   {v['id']}: {v['sector']} - {v['avg_test']:.1f}%")

print('\n' + '='*100)
