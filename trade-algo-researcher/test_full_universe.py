#!/usr/bin/env python3
"""
PROPER UNIVERSE TESTING: S001-S005
Test each strategy across FULL universe (US + HK + SG)
Report which tickers pass/fail
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

def test_strategy_full(df, entry_func, exit_days=5):
    """Test on full 3-period and return results"""
    train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    results = {}
    for period_name, period_df in [('Train', train), ('Test', test), ('Validate', validate)]:
        trades = []
        for i in range(50, len(period_df) - exit_days):
            if entry_func(period_df, i):
                entry = period_df['close'].iloc[i]
                exit_p = period_df['close'].iloc[i + exit_days]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        
        if len(trades) >= 5:
            r = pd.Series(trades)
            results[period_name] = {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}
        else:
            results[period_name] = {'trades': 0, 'win_rate': 0}
    
    return results

def classify_strategy(train_wr, test_wr, val_wr):
    if train_wr >= 55 and test_wr >= 60 and val_wr >= 55:
        return 'GOLDEN'
    elif test_wr >= 60 and val_wr >= 55:
        return 'VALIDATED'
    elif test_wr >= 55 and val_wr >= 50:
        return 'BORDERLINE'
    else:
        return 'FAILED'

# Get full universe
print('='*100)
print('FULL UNIVERSE AUDIT')
print('='*100)

# US Stocks
cursor.execute('''
    SELECT DISTINCT ticker FROM silver.unified_prices 
    WHERE ticker IN ('SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD')
''')
us_stocks = [r[0] for r in cursor.fetchall()]

# HK Stocks
cursor.execute('''
    SELECT DISTINCT ticker FROM silver.unified_prices 
    WHERE ticker LIKE '%.HK' AND ticker IN ('0700.HK', '9988.HK', '3690.HK', '1810.HK', '9999.HK', '9618.HK', '1024.HK')
''')
hk_stocks = [r[0] for r in cursor.fetchall()]

# China A-Shares
cursor.execute('''
    SELECT DISTINCT ticker FROM silver.unified_prices 
    WHERE ticker LIKE '%.SZ' AND ticker IN ('000858.SZ', '000333.SZ', '000651.SZ', '002142.SZ')
''')
cn_stocks = [r[0] for r in cursor.fetchall()]

print(f"US Universe: {len(us_stocks)} tickers - {us_stocks}")
print(f"HK Universe: {len(hk_stocks)} tickers - {hk_stocks}")
print(f"CN Universe: {len(cn_stocks)} tickers - {cn_stocks}")

all_tickers = us_stocks + hk_stocks + cn_stocks

# S001: RSI Mean Reversion - Full Universe Test
print('\n' + '='*100)
print('S001: RSI Mean Reversion (<30) - FULL UNIVERSE TEST')
print('='*100)

def entry_rsi30(df, i):
    return pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30

s001_results = {'GOLDEN': [], 'VALIDATED': [], 'BORDERLINE': [], 'FAILED': []}

for ticker in all_tickers:
    table = 'silver.unified_prices'
    if '.SZ' in ticker:
        table = 'silver.unified_prices'  # China A-shares
    
    cursor.execute(f'''
        SELECT date, close::float FROM {table} 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    
    if len(data) < 200:
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    res = test_strategy_full(df, entry_rsi30, 10)
    train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
    
    status = classify_strategy(train_wr, test_wr, val_wr)
    s001_results[status].append((ticker, test_wr, val_wr))
    
    print(f"{ticker}: Train {train_wr:.1f}% | Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")

print(f"\nS001 SUMMARY: GOLDEN {len(s001_results['GOLDEN'])}, VALIDATED {len(s001_results['VALIDATED'])}, BORDERLINE {len(s001_results['BORDERLINE'])}, FAILED {len(s001_results['FAILED'])}")

# S002: Trend Following - Full Universe Test
print('\n' + '='*100)
print('S002: Trend Following (Price > SMA50) - FULL UNIVERSE TEST')
print('='*100)

def entry_trend(df, i):
    return pd.notna(df['sma50'].iloc[i]) and df['close'].iloc[i] > df['sma50'].iloc[i]

s002_results = {'GOLDEN': [], 'VALIDATED': [], 'BORDERLINE': [], 'FAILED': []}

for ticker in all_tickers:
    table = 'silver.unified_prices'
    cursor.execute(f'''
        SELECT date, close::float FROM {table} 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    
    if len(data) < 200:
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma50'] = df['close'].rolling(50).mean()
    
    res = test_strategy_full(df, entry_trend, 10)
    train_wr, test_wr, val_wr = res['Train']['win_rate'], res['Test']['win_rate'], res['Validate']['win_rate']
    
    status = classify_strategy(train_wr, test_wr, val_wr)
    s002_results[status].append((ticker, test_wr, val_wr))
    
    print(f"{ticker}: Test {test_wr:.1f}% | Val {val_wr:.1f}% | {status}")

print(f"\nS002 SUMMARY: GOLDEN {len(s002_results['GOLDEN'])}, VALIDATED {len(s002_results['VALIDATED'])}, BORDERLINE {len(s002_results['BORDERLINE'])}, FAILED {len(s002_results['FAILED'])}")

conn.close()

print('\n' + '='*100)
print('FINAL SUMMARY - PROPER UNIVERSE TESTING')
print('='*100)
print(f"\nS001: RSI Mean Reversion - Works on {len(s001_results['GOLDEN']) + len(s001_results['VALIDATED'])}/{len(all_tickers)} tickers")
print(f"  GOLDEN: {[t[0] for t in s001_results['GOLDEN']]}")
print(f"  VALIDATED: {[t[0] for t in s001_results['VALIDATED']]}")

print(f"\nS002: Trend Following - Works on {len(s002_results['GOLDEN']) + len(s002_results['VALIDATED'])}/{len(all_tickers)} tickers")
print(f"  GOLDEN: {[t[0] for t in s002_results['GOLDEN']]}")
print(f"  VALIDATED: {[t[0] for t in s002_results['VALIDATED']]}")

print(f"\nTOTAL UNIQUE STRATEGIES: 2 (not {len(all_tickers)})")
