#!/usr/bin/env python3
"""
QUICK TEST - SPY REGIME STRATEGIES WITH NEW INDICATORS
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print("="*70)
print("TESTING SPY REGIME STRATEGIES")
print("="*70)

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

# Load SPY with prices and indicators
print("\nLoading SPY data...")
spy_df = pd.read_sql('''
    SELECT t.date, t.close, t.volume, ti.rsi_14, ti.bb_upper, ti.bb_lower, ti.vol_ratio
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker = 'SPY' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY t.date
''', conn)

spy_df['sma50'] = spy_df['close'].rolling(50).mean()
spy_df['sma200'] = spy_df['close'].rolling(200).mean()
spy_df['return'] = spy_df['close'].pct_change()
spy_df['trend'] = np.where(spy_df['close'] > spy_df['sma50'], 'up', 'down')

print(f"SPY records: {len(spy_df)}")

# Load sample stocks with SPY merged
print("\nLoading stock data...")
stock_df = pd.read_sql('''
    SELECT t.date, t.ticker, t.close,
           ti.rsi_14, ti.vol_ratio, ti.bb_lower
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 
                       '0700.HK', '9988.HK', '0001.HK', '0005.HK')
      AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
''', conn)

print(f"Stock records: {len(stock_df)} ({stock_df['ticker'].nunique()} tickers)")

# Merge with SPY trend
stock_df = stock_df.merge(spy_df[['date', 'trend', 'sma200', 'return']].rename(
    columns={'trend': 'spy_trend', 'sma200': 'spy_sma200', 'return': 'spy_return', 'close': 'spy_close'}
), on='date', how='left')

results = []

# Test H89: RSI <20 + SPY Uptrend
print("\n--- H89: RSI <20 + SPY Uptrend ---")
trades = []
for ticker in stock_df['ticker'].unique():
    tdf = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if tdf['rsi_14'].iloc[i] < 20 and tdf['spy_trend'].iloc[i] == 'up':
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    avg_ret = r.mean()
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Avg: {avg_ret:.2f}% {status}")
    results.append(('H89: RSI+SPY Up', len(trades), wr, avg_ret, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H89: RSI+SPY Up', len(trades), 0, 0, '❌'))

# Test H90: RSI <15 + SPY Downtrend
print("\n--- H90: RSI <15 + SPY Downtrend ---")
trades = []
for ticker in stock_df['ticker'].unique():
    tdf = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if tdf['rsi_14'].iloc[i] < 15 and tdf['spy_trend'].iloc[i] == 'down':
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    avg_ret = r.mean()
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Avg: {avg_ret:.2f}% {status}")
    results.append(('H90: RSI+SPY Down', len(trades), wr, avg_ret, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H90: RSI+SPY Down', len(trades), 0, 0, '❌'))

# Test H91: Volume Breakout + SPY Uptrend
print("\n--- H91: Vol >2x + Price >4% + SPY Up ---")
trades = []
for ticker in stock_df['ticker'].unique():
    tdf = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    tdf['ret'] = tdf['close'].pct_change()
    for i in range(20, len(tdf) - 5):
        if pd.notna(tdf['vol_ratio'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if (tdf['vol_ratio'].iloc[i] > 2.0 and 
                tdf['ret'].iloc[i] > 0.04 and
                tdf['spy_trend'].iloc[i] == 'up'):
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 5]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    avg_ret = r.mean()
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Avg: {avg_ret:.2f}% {status}")
    results.append(('H91: VolBO+SPY Up', len(trades), wr, avg_ret, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H91: VolBO+SPY Up', len(trades), 0, 0, '❌'))

# Test H92: RSI <20 + SPY > 200-day SMA
print("\n--- H92: RSI <20 + SPY > 200-day SMA ---")
trades = []
for ticker in stock_df['ticker'].unique():
    tdf = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    for i in range(200, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_sma200'].iloc[i]):
            spy_price = spy_df[spy_df['date'] == tdf['date'].iloc[i]]['close'].values
            if len(spy_price) > 0 and spy_price[0] > tdf['spy_sma200'].iloc[i]:
                if tdf['rsi_14'].iloc[i] < 20:
                    entry = tdf['close'].iloc[i]
                    exit_price = tdf['close'].iloc[i + 10]
                    ret = (exit_price - entry) / entry * 100 - 0.1
                    trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    avg_ret = r.mean()
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Avg: {avg_ret:.2f}% {status}")
    results.append(('H92: RSI+GoldenCross', len(trades), wr, avg_ret, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H92: RSI+GoldenCross', len(trades), 0, 0, '❌'))

# Test H95: BB Lower + SPY Uptrend
print("\n--- H95: BB Lower + SPY Uptrend ---")
trades = []
for ticker in stock_df['ticker'].unique():
    tdf = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 10):
        if pd.notna(tdf['bb_lower'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and tdf['spy_trend'].iloc[i] == 'up':
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    avg_ret = r.mean()
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Avg: {avg_ret:.2f}% {status}")
    results.append(('H95: BB+SPY Up', len(trades), wr, avg_ret, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H95: BB+SPY Up', len(trades), 0, 0, '❌'))

# SUMMARY
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"{'Strategy':<25} {'Trades':<10} {'Win%':<10} {'Avg Ret':<10} {'Status'}")
print("-"*70)

validated = 0
for name, trades, wr, avg_ret, status in results:
    if trades >= 10:
        print(f"{name:<25} {trades:<10} {wr:<10.1f} {avg_ret:<10.2f} {status}")
        if status == '✅':
            validated += 1
    else:
        print(f"{name:<25} {trades:<10} N/A       N/A       {status}")

print("-"*70)
print(f"Validated: {validated}/{len([r for r in results if r[1] >= 10])}")
print("="*70)

if validated > 0:
    print(f"\n🎉 {validated} SPY regime strategies validated!")
else:
    print("\n📊 No strategies validated on this sample.")
    print("Need larger universe for meaningful results.")

conn.close()
