#!/usr/bin/env python3
"""
SECTOR-SPECIFIC STRATEGY VARIATIONS: S001-S007
Create market-sector specific versions of each strategy
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

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def classify_sector(ticker):
    if ticker.endswith('.HK'):
        code = ticker.split('.')[0]
        if code in ['0001', '0002', '0003', '0016', '0012', '1113']:
            return 'HK_Property'
        elif code in ['0700', '9999', '9618', '9988', '3690', '1024', '1810', '2015']:
            return 'HK_Tech'
        elif code in ['1398', '0939', '3988', '2388', '3328', '0005', '0011']:
            return 'HK_Banks'
        elif code in ['2628', '2318', '2319', '1299']:
            return 'HK_Insurance'
        elif code in ['0883', '0386', '0857', '1088', '1171']:
            return 'HK_Energy'
        elif code in ['0006', '0004', '0019', '0083']:
            return 'HK_Utilities'
        elif code in ['1928', '2269', '9992', '2313', '2020']:
            return 'HK_Consumer'
        else:
            return 'HK_Other'
    elif ticker.endswith('.SZ') or ticker.endswith('.SS'):
        # China A-shares classification
        if ticker in ['601398.SS', '601939.SS', '601988.SS', '601288.SS', '601658.SS', '600036.SS']:
            return 'CN_Banks'
        elif ticker in ['601318.SS', '601628.SS', '601601.SS']:
            return 'CN_Insurance'
        elif ticker in ['000333.SZ', '000651.SZ', '000568.SZ', '000538.SZ', '600519.SS', '000858.SZ']:
            return 'CN_Consumer'
        elif ticker in ['300750.SZ', '002594.SZ', '601012.SS', '600438.SS']:
            return 'CN_EV_Energy'
        elif ticker in ['002415.SZ', '002230.SZ', '000063.SZ']:
            return 'CN_Tech'
        else:
            return 'CN_Other'
    elif ticker.endswith('.SI'):
        return 'Singapore_REITs'
    elif ticker in ['SPY', 'QQQ', 'IWM', 'DIA']:
        return 'US_ETF_Index'
    elif ticker in ['XLF', 'XLK', 'XLE', 'XLU', 'XLI', 'XLP', 'XLB', 'XLV']:
        return 'US_Sector_ETF'
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'NFLX', 'TSLA', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'AVGO', 'QCOM', 'TXN', 'MU', 'PLTR', 'SNOW', 'DDOG', 'CRWD', 'OKTA', 'SHOP', 'SQ', 'ROKU', 'ZM', 'UBER', 'ABNB']:
        return 'US_Tech'
    elif ticker in ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP', 'USB', 'PNC', 'COF', 'SCHW']:
        return 'US_Banks'
    elif ticker in ['JNJ', 'PFE', 'UNH', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'MRK', 'AMGN']:
        return 'US_Healthcare'
    elif ticker in ['WMT', 'COST', 'TGT', 'HD', 'LOW', 'NKE', 'MCD', 'SBUX', 'TJX']:
        return 'US_Consumer_Retail'
    elif ticker in ['PG', 'KO', 'PEP', 'KMB', 'CL', 'EL', 'GIS', 'K', 'CPB', 'HSY', 'MDLZ']:
        return 'US_Consumer_Staples'
    elif ticker in ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY', 'MPC', 'VLO', 'PSX', 'WMB']:
        return 'US_Energy'
    elif ticker in ['BA', 'CAT', 'GE', 'HON', 'RTX', 'LMT', 'NOC', 'GD', 'TDG', 'WM', 'RSG', 'CNI', 'UNP', 'CSX', 'FDX', 'UPS']:
        return 'US_Industrials'
    else:
        return 'US_Other'

cursor.execute('''
    SELECT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
''')
valid_tickers = [r[0] for r in cursor.fetchall()]

# STRATEGY VARIATIONS TO TEST
variations = []

print('='*100)
print('SECTOR-SPECIFIC STRATEGY VARIATIONS: S001-S007')
print('='*100)

# === S001 RSI MEAN REVERSION - SECTOR VARIATIONS ===
print('\n' + '='*100)
print('S001-01 to S001-10: RSI Mean Reversion by Sector')
print('='*100)

s001_sectors = {}

for ticker in valid_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(14, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 30:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10: continue
    test_wr = (pd.Series(trades_test) > 0).mean() * 100
    
    trades_val = []
    for i in range(14, len(validate) - 10):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 30:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    if len(trades_val) < 5: continue
    val_wr = (pd.Series(trades_val) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s001_sectors:
            s001_sectors[sector] = []
        s001_sectors[sector].append({
            'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr,
            'test_n': len(trades_test), 'val_n': len(trades_val)
        })

# Create S001 sector variations
s001_variations = []
var_num = 1
for sector, tickers in sorted(s001_sectors.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    
    if avg_test >= 70 and len(tickers) >= 3:
        status = '🏆 GOLDEN'
    elif avg_test >= 60:
        status = '✅ VALIDATED'
    else:
        status = '🟡 TIER 3'
    
    s001_variations.append({
        'id': f'S001-{var_num:02d}',
        'name': f'RSI_MR_{sector}',
        'sector': sector,
        'tickers': [t['ticker'] for t in tickers],
        'avg_test': avg_test,
        'avg_val': avg_val,
        'total_n': total_n,
        'ticker_count': len(tickers),
        'status': status
    })
    var_num += 1

print(f"\n{'ID':<10} {'Sector':<25} {'Tickers':<8} {'Test WR':<10} {'Val WR':<10} {'Trades':<8} {'Status':<12}")
print('-'*100)
for v in s001_variations:
    print(f"{v['id']:<10} {v['sector']:<25} {v['ticker_count']:<8} {v['avg_test']:<10.1f} {v['avg_val']:<10.1f} {v['total_n']:<8} {v['status']:<12}")

# === S002 TREND FOLLOWING - SECTOR VARIATIONS ===
print('\n' + '='*100)
print('S002-01 to S002-10: Trend Following by Sector')
print('='*100)

s002_sectors = {}

for ticker in valid_tickers:
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma50'] = df['close'].rolling(50).mean()
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(50, len(test) - 10):
        if pd.notna(test['sma50'].iloc[i]) and test['close'].iloc[i] > test['sma50'].iloc[i]:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10: continue
    test_wr = (pd.Series(trades_test) > 0).mean() * 100
    
    trades_val = []
    for i in range(50, len(validate) - 10):
        if pd.notna(validate['sma50'].iloc[i]) and validate['close'].iloc[i] > validate['sma50'].iloc[i]:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    if len(trades_val) < 5: continue
    val_wr = (pd.Series(trades_val) > 0).mean() * 100
    
    if test_wr >= 60 and val_wr >= 55:
        sector = classify_sector(ticker)
        if sector not in s002_sectors:
            s002_sectors[sector] = []
        s002_sectors[sector].append({
            'ticker': ticker, 'test_wr': test_wr, 'val_wr': val_wr,
            'test_n': len(trades_test), 'val_n': len(trades_val)
        })

s002_variations = []
var_num = 1
for sector, tickers in sorted(s002_sectors.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    
    if avg_test >= 70 and len(tickers) >= 3:
        status = '🏆 GOLDEN'
    elif avg_test >= 60:
        status = '✅ VALIDATED'
    else:
        status = '🟡 TIER 3'
    
    s002_variations.append({
        'id': f'S002-{var_num:02d}',
        'name': f'Trend_{sector}',
        'sector': sector,
        'tickers': [t['ticker'] for t in tickers],
        'avg_test': avg_test,
        'avg_val': avg_val,
        'total_n': total_n,
        'ticker_count': len(tickers),
        'status': status
    })
    var_num += 1

print(f"\n{'ID':<10} {'Sector':<25} {'Tickers':<8} {'Test WR':<10} {'Val WR':<10} {'Trades':<8} {'Status':<12}")
print('-'*100)
for v in s002_variations:
    print(f"{v['id']:<10} {v['sector']:<25} {v['ticker_count']:<8} {v['avg_test']:<10.1f} {v['avg_val']:<10.1f} {v['total_n']:<8} {v['status']:<12}")

conn.close()

# SUMMARY
print('\n' + '='*100)
print('SECTOR-SPECIFIC VARIATIONS SUMMARY')
print('='*100)

all_vars = s001_variations + s002_variations
golden = [v for v in all_vars if '🏆' in v['status']]
validated = [v for v in all_vars if '✅' in v['status']]
tier3 = [v for v in all_vars if '🟡' in v['status']]

print(f"\n🏆 GOLDEN Variations: {len(golden)}")
for v in golden:
    print(f"   {v['id']}: {v['name']} - {v['avg_test']:.1f}% ({v['ticker_count']} tickers, {v['total_n']} trades)")

print(f"\n✅ VALIDATED Variations: {len(validated)}")
for v in validated:
    print(f"   {v['id']}: {v['name']} - {v['avg_test']:.1f}% ({v['ticker_count']} tickers)")

print(f"\n🟡 TIER 3 Variations: {len(tier3)}")
for v in tier3:
    print(f"   {v['id']}: {v['name']} - {v['avg_test']:.1f}%")

print('\n' + '='*100)
print('TOP 5 SECTOR-SPECIFIC STRATEGIES TO DEPLOY:')
print('='*100)

top5 = sorted(all_vars, key=lambda x: x['avg_test'], reverse=True)[:5]
for i, v in enumerate(top5, 1):
    print(f"\n{i}. {v['id']}: {v['name']}")
    print(f"   Tickers: {', '.join(v['tickers'][:5])}{'...' if len(v['tickers']) > 5 else ''}")
    print(f"   Performance: {v['avg_test']:.1f}% test / {v['avg_val']:.1f}% validate")
    print(f"   Trades: {v['total_n']} | Status: {v['status']}")

print('\n' + '='*100)
