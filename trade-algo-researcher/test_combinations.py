#!/usr/bin/env python3
"""
COMBINATION TEST: Can combining failed signals improve accuracy?
Test confluence of multiple signals
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
print("COMBINATION TEST: Multi-Signal Confluence")
print("Testing if combining weak signals creates strong signals")
print("="*70)

# Get data
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector IN ('Tech', 'Equity') LIMIT 40")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT date, ticker, open, high, low, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Universe: {df['ticker'].nunique()} tickers, {len(df)} records\n")

# Calculate all indicators once
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Prepare data with all indicators
all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    
    # Basic
    tdf['return'] = tdf['close'].pct_change()
    tdf['body'] = abs(tdf['close'] - tdf['open'])
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['upper_shadow'] = tdf['high'] - tdf[['open', 'close']].max(axis=1)
    tdf['lower_shadow'] = tdf[['open', 'close']].min(axis=1) - tdf['low']
    
    # Volume
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    
    # RSI
    tdf['rsi'] = calculate_rsi(tdf['close'])
    
    # Moving averages
    tdf['ma20'] = tdf['close'].rolling(20).mean()
    
    # Patterns
    tdf['doji'] = tdf['body'] <= (tdf['range'] * 0.1)
    tdf['hammer'] = (tdf['lower_shadow'] > tdf['body'] * 2) & (tdf['upper_shadow'] < tdf['body'])
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    tdf['inside_day'] = (tdf['high'] < tdf['prev_high']) & (tdf['low'] > tdf['prev_low'])
    
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi', 'ma20'])

print(f"After indicators: {len(df)} records\n")

# Test combinations
results = []

# COMBO 1: Doji + RSI Oversold + Volume Spike
print("Testing COMBO 1: Doji + RSI < 30 + Volume > 1.5x")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 5):
        if (tdf['doji'].iloc[i] and 
            tdf['rsi'].iloc[i] < 30 and 
            tdf['vol_ratio'].iloc[i] > 1.5):
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('Combo 1: Doji+RSI+Vol', len(trades), wr, sh))
    print(f"  Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}\n")

# COMBO 2: Hammer + RSI < 40
print("Testing COMBO 2: Hammer + RSI < 40")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 5):
        if (tdf['hammer'].iloc[i] and 
            tdf['rsi'].iloc[i] < 40 and
            tdf['close'].iloc[i] < tdf['ma20'].iloc[i]):  # Below MA
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('Combo 2: Hammer+RSI+BelowMA', len(trades), wr, sh))
    print(f"  Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}\n")

# COMBO 3: Inside Day + Volume + Breakout
print("Testing COMBO 3: Inside Day Yesterday + Volume > 2x + Breakout Today")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 5):
        if (tdf['inside_day'].iloc[i-1] and 
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['close'].iloc[i] > tdf['prev_high'].iloc[i]):
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('Combo 3: Inside+Vol+Break', len(trades), wr, sh))
    print(f"  Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}\n")

# COMBO 4: 3-Day Down + RSI Extreme + Volume
print("Testing COMBO 4: 3-Day Down + RSI < 20 + Volume > 1.5x")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(20, len(tdf) - 5):
        if (tdf['return'].iloc[i] < 0 and 
            tdf['return'].iloc[i-1] < 0 and 
            tdf['return'].iloc[i-2] < 0 and
            tdf['rsi'].iloc[i] < 20 and
            tdf['vol_ratio'].iloc[i] > 1.5):
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('Combo 4: 3Day+RSI20+Vol', len(trades), wr, sh))
    print(f"  Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}\n")

# COMBO 5: Range Expansion + Volume + RSI
print("Testing COMBO 5: Range Expansion + Volume > 2x + RSI < 50")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr'] = tdf['range'].rolling(14).mean()
    for i in range(20, len(tdf) - 5):
        if (tdf['range'].iloc[i] > tdf['atr'].iloc[i] * 1.5 and
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['rsi'].iloc[i] < 50 and
            tdf['close'].iloc[i] > tdf['open'].iloc[i]):
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('Combo 5: Range+Vol+RSI', len(trades), wr, sh))
    print(f"  Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}\n")

# Summary
print("="*70)
print("COMBINATION TEST RESULTS")
print("="*70)
print(f"{'Combination':<30} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

for name, trades, wr, sh in results:
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"{status} {name:<28} {trades:<10} {wr:<10.1f} {sh:<10.2f}")

print("-"*70)
best = max(results, key=lambda x: x[2]) if results else None
if best:
    print(f"\n🏆 BEST: {best[0]} - {best[2]:.1f}% win rate")
    if best[2] >= 60:
        print("🧪 Shows promise - test with tighter filters")
    elif best[2] >= 55:
        print("✅ Validated combination!")
    else:
        print("❌ Even combinations don't provide edge")

print("="*70)
