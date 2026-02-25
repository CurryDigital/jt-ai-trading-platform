#!/usr/bin/env python3
"""
HK MARKET: Trend Following Test
Bull/Bear Regime Detection
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

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

print('='*90)
print('HK TREND FOLLOWING + BULL/BEAR REGIME')
print('='*90)

hk_stocks = ['0700.HK', '9988.HK', '3690.HK', '1810.HK']

for ticker in hk_stocks:
    print(f'\n--- {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['rsi'] = rsi(df['close'])
    
    # Bull market: price > SMA200
    # Bear market: price < SMA200
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    
    # Test trend following in BULL market
    bull_trades = []
    for i in range(200, len(test) - 5):
        if (pd.notna(test['sma200'].iloc[i]) and 
            test['close'].iloc[i] > test['sma200'].iloc[i] and  # Bull market
            test['close'].iloc[i] > test['sma50'].iloc[i]):  # Trend up
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            bull_trades.append(ret)
    
    # Test mean reversion in BEAR market
    bear_trades = []
    for i in range(200, len(test) - 5):
        if (pd.notna(test['sma200'].iloc[i]) and 
            test['close'].iloc[i] < test['sma200'].iloc[i] and  # Bear market
            pd.notna(test['rsi'].iloc[i]) and
            test['rsi'].iloc[i] < 30):  # Oversold
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            bear_trades.append(ret)
    
    if bull_trades:
        r = pd.Series(bull_trades)
        print(f'  BULL Trend: {len(bull_trades)} trades, {(r > 0).mean()*100:.1f}% win')
    
    if bear_trades:
        r = pd.Series(bear_trades)
        print(f'  BEAR MR: {len(bear_trades)} trades, {(r > 0).mean()*100:.1f}% win')

print('\n' + '='*90)
print('US COMPARISON: Bull/Bear Regime')
print('='*90)

us_stocks = [('QQQ', 'US'), ('SPY', 'US')]

for ticker, market in us_stocks:
    print(f'\n--- {ticker} ---')
    cursor.execute(f'''
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['rsi'] = rsi(df['close'])
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    
    bull_trades = []
    for i in range(200, len(test) - 5):
        if (pd.notna(test['sma200'].iloc[i]) and 
            test['close'].iloc[i] > test['sma200'].iloc[i] and
            test['close'].iloc[i] > test['sma50'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            bull_trades.append(ret)
    
    bear_trades = []
    for i in range(200, len(test) - 5):
        if (pd.notna(test['sma200'].iloc[i]) and 
            test['close'].iloc[i] < test['sma200'].iloc[i] and
            pd.notna(test['rsi'].iloc[i]) and
            test['rsi'].iloc[i] < 30):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 5]
            ret = (exit_p - entry) / entry * 100 - 0.1
            bear_trades.append(ret)
    
    if bull_trades:
        r = pd.Series(bull_trades)
        print(f'  BULL Trend: {len(bull_trades)} trades, {(r > 0).mean()*100:.1f}% win')
    
    if bear_trades:
        r = pd.Series(bear_trades)
        print(f'  BEAR MR: {len(bear_trades)} trades, {(r > 0).mean()*100:.1f}% win')

conn.close()
