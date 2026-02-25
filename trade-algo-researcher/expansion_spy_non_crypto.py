#!/usr/bin/env python3
"""
EXPANSION CYCLE: SPY Regime Filters on Non-Crypto Assets
Test if SPY filter benefits generalize beyond crypto
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*70)
print('EXPANSION CYCLE: SPY Regime Filters on Non-Crypto Assets')
print('='*70)

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

# Test tickers across sectors
test_tickers = ['AAPL', 'MSFT', 'TSLA', 'JPM', 'XOM', 'NVDA', 'META', 'AMD']

# Get SPY data
cursor = conn.cursor()
cursor.execute('''
SELECT t.date, t.close::float
FROM silver.unified_prices t
WHERE t.ticker = 'SPY' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close'])
spy_df['spy_sma200'] = spy_df['spy_close'].rolling(200, min_periods=200).mean()
spy_df['spy_above_200d'] = spy_df['spy_close'] > spy_df['spy_sma200']
spy_df['spy_sma50'] = spy_df['spy_close'].rolling(50, min_periods=50).mean()
spy_df['spy_above_50d'] = spy_df['spy_close'] > spy_df['spy_sma50']

results = []

for ticker in test_tickers:
    print(f'\n--- Testing {ticker} ---')
    
    # Get ticker data with indicators
    cursor.execute(f'''
    SELECT t.date, t.close::float, ti.rsi_14
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker = '{ticker}' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY t.date
    ''')
    data = cursor.fetchall()
    
    if len(data) == 0:
        print(f'  No data available')
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close', 'rsi_14'])
    df = df.merge(spy_df, on='date', how='inner').dropna(subset=['spy_sma200'])
    
    if len(df) == 0:
        print(f'  No valid data after merge')
        continue
    
    # Test 3 variants
    variants = [
        ('RSI<25 only', 'no_filter'),
        ('RSI<25 + SPY>200d', 'above_200d'),
        ('RSI<25 + SPY>50d', 'above_50d'),
    ]
    
    ticker_results = []
    for name, filter_type in variants:
        trades = []
        for idx, row in df.iterrows():
            if pd.notna(row['rsi_14']):
                # Check condition
                if filter_type == 'no_filter':
                    condition = row['rsi_14'] < 25
                elif filter_type == 'above_200d':
                    condition = row['rsi_14'] < 25 and row['spy_above_200d']
                elif filter_type == 'above_50d':
                    condition = row['rsi_14'] < 25 and row['spy_above_50d']
                else:
                    condition = False
                
                if condition:
                    entry_idx = df.index.get_loc(idx)
                    exit_idx = entry_idx + 10
                    if exit_idx < len(df):
                        entry_price = row['close']
                        exit_price = df.iloc[exit_idx]['close']
                        ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
                        trades.append(ret)
        
        if len(trades) >= 5:
            win_rate = (pd.Series(trades) > 0).mean() * 100
            avg_ret = pd.Series(trades).mean()
            ticker_results.append((name, len(trades), win_rate, avg_ret))
            status = '✅' if win_rate >= 55 else '❌'
            print(f'  {status} {name}: {len(trades)} trades, {win_rate:.1f}% win, {avg_ret:.2f}% avg')
        else:
            print(f'  ⚠️  {name}: {len(trades)} trades (insufficient)')
    
    if ticker_results:
        results.append((ticker, ticker_results))

conn.close()

print('\n' + '='*70)
print('EXPANSION RESULTS SUMMARY')
print('='*70)

print('\n{:<10} {:<25} {:<10} {:<10} {:<12}'.format('Ticker', 'Strategy', 'Trades', 'Win%', 'Avg Return'))
print('-'*70)

for ticker, ticker_results in results:
    for name, trades, win_rate, avg_ret in ticker_results:
        print('{:<10} {:<25} {:<10} {:<10.1f} {:<12.2f}'.format(ticker, name, trades, win_rate, avg_ret))

print('\n' + '='*70)
print('ANALYSIS: Does SPY Filter Help Non-Crypto Assets?')
print('='*70)

for ticker, ticker_results in results:
    if len(ticker_results) >= 2:
        baseline = [r for r in ticker_results if 'only' in r[0]]
        with_filter = [r for r in ticker_results if '200d' in r[0]]
        
        if baseline and with_filter:
            improvement = with_filter[0][2] - baseline[0][2]
            print(f'{ticker}: SPY filter adds {improvement:+.1f}% win rate')

print('\n' + '='*70)
print('CONCLUSION:')
print('='*70)
print('Compare improvements to crypto:')
print('  MSTR: +18% with SPY filter (strong benefit)')
print('  COIN: +0% with SPY filter (no benefit)')
print('  RIOT: +8% with SPY filter (modest benefit)')
print('='*70)
