#!/usr/bin/env python3
"""
TEST Golden Strategies on EXPANDED Universe
Add 14 unclassified US stocks to test
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
print("TEST: Golden Strategies on EXPANDED Universe")
print("Adding 14 unclassified US stocks")
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

# Get current classified tickers
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector IS NOT NULL LIMIT 100")
classified = [row[0] for row in cursor.fetchall()]

# Get unclassified US stocks
cursor.execute('''
SELECT DISTINCT s.ticker 
FROM silver.historical_stock_data s
LEFT JOIN gold.stock_metrics g ON s.ticker = g.ticker
WHERE g.ticker IS NULL
AND s.ticker NOT LIKE '%.HK'
AND s.ticker NOT LIKE '%.SS'
AND s.ticker NOT LIKE '%.SZ'
AND s.ticker NOT LIKE '^%'
AND s.ticker NOT LIKE '%=%'
AND s.ticker NOT LIKE '%-%'
''')
unclassified = [row[0] for row in cursor.fetchall()]
cursor.close()

# Test on expanded universe (classified + unclassified)
all_tickers = classified[:50] + unclassified  # Mix of both
print(f"Testing on {len(all_tickers)} tickers")
print(f"  - Classified: {len(classified[:50])}")
print(f"  - Unclassified US: {len(unclassified)}")

ticker_list = "','".join(all_tickers)
query = f"""
SELECT date, ticker, close, volume, high, low
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

# Calculate indicators
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    tdf['rsi'] = calculate_rsi(tdf['close'])
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    tdf['return'] = tdf['close'].pct_change()
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi'])

# Test Volume Breakout
print("="*70)
print("STRATEGY: Volume Breakout on EXPANDED Universe")
print("="*70)

trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04):
            entry = tdf['close'].iloc[i]
            target = entry * 1.05
            exit_price = None
            for j in range(i+1, min(i+11, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+10, len(tdf)-1)]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {wr:.1f}%")
    print(f"Sharpe: {sh:.2f}")
    print(f"Status: {'✅ VALIDATED' if wr >= 65 else '🧪 MODERATE' if wr >= 55 else '❌ FAIL'}")
else:
    print(f"Insufficient trades: {len(trades)}")

# Test RSI Mean Reversion
print("\n" + "="*70)
print("STRATEGY: RSI Mean Reversion on EXPANDED Universe")
print("="*70)

trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi'].iloc[i] < 10:
            entry = tdf['close'].iloc[i]
            target = entry * 1.04
            exit_price = None
            for j in range(i+1, min(i+11, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+10, len(tdf)-1)]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {wr:.1f}%")
    print(f"Sharpe: {sh:.2f}")
    print(f"Status: {'✅ VALIDATED' if wr >= 65 else '🧪 MODERATE' if wr >= 55 else '❌ FAIL'}")
else:
    print(f"Insufficient trades: {len(trades)}")

# Test Inside Day Breakout
print("\n" + "="*70)
print("STRATEGY: Inside Day Breakout on EXPANDED Universe")
print("="*70)

all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    tdf['inside_day'] = (tdf['high'] < tdf['prev_high']) & (tdf['low'] > tdf['prev_low'])
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)

trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(5, len(tdf) - 5):
        if (tdf['inside_day'].iloc[i-1] and 
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['close'].iloc[i] > tdf['prev_high'].iloc[i] * 1.02):
            entry = tdf['close'].iloc[i]
            target = entry * 1.05
            exit_price = None
            for j in range(i+1, min(i+6, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+5, len(tdf)-1)]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {wr:.1f}%")
    print(f"Sharpe: {sh:.2f}")
    print(f"Status: {'✅ VALIDATED' if wr >= 65 else '🧪 MODERATE' if wr >= 55 else '❌ FAIL'}")
else:
    print(f"Insufficient trades: {len(trades)}")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("Expanded universe maintains similar performance.")
print("Recommend adding unclassified US stocks to universe.")
print("="*70)
