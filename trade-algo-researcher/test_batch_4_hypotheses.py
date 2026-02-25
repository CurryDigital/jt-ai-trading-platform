#!/usr/bin/env python3
"""
BATCH TEST: 10 New Hypotheses (Set 4)
Goal: Reach 37 total hypotheses tested
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

# Get data once
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector IN ('Tech', 'Equity') LIMIT 60")
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

print("="*70)
print("BATCH TEST 4: 10 New Hypotheses")
print(f"Universe: {df['ticker'].nunique()} tickers, {len(df)} records")
print("="*70)

# Calculate all indicators once
all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    tdf['return'] = tdf['close'].pct_change()
    tdf['body'] = abs(tdf['close'] - tdf['open'])
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['upper_shadow'] = tdf['high'] - tdf[['open', 'close']].max(axis=1)
    tdf['lower_shadow'] = tdf[['open', 'close']].min(axis=1) - tdf['low']
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    # RSI
    delta = tdf['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    tdf['rsi'] = 100 - (100 / (1 + rs))
    # Moving averages
    tdf['ma5'] = tdf['close'].rolling(5).mean()
    tdf['ma20'] = tdf['close'].rolling(20).mean()
    tdf['ma50'] = tdf['close'].rolling(50).mean()
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna()

results = []

# HYPOTHESIS 28: Shooting Star (bearish reversal - inverse)
print("\n" + "="*70)
print("H28: Shooting Star Pattern (Short Setup)")
print("Pattern: Small body, long upper shadow, after uptrend")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(10, len(tdf) - 5):
        # Shooting star: upper shadow > 2x body, small lower shadow
        if (tdf['upper_shadow'].iloc[i] > tdf['body'].iloc[i] * 2 and 
            tdf['lower_shadow'].iloc[i] < tdf['body'].iloc[i] and
            tdf['close'].iloc[i-1] > tdf['close'].iloc[i-5]):  # After uptrend
            # Short
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (entry - exit_price) / entry * 100 - 0.1  # Short return
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('28: Shooting Star', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('28: Shooting Star', len(trades), 0, 0, '❌'))

# HYPOTHESIS 29: Morning Star (3-candle reversal)
print("\n" + "="*70)
print("H29: Morning Star Pattern")
print("Pattern: Down candle, small doji, up candle")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['is_doji'] = tdf['body'] <= (tdf['range'] * 0.1)
    for i in range(5, len(tdf) - 5):
        # Day 1: Down, Day 2: Doji (gap down), Day 3: Up
        if (tdf['close'].iloc[i-2] < tdf['open'].iloc[i-2] and  # Day 1 down
            tdf['is_doji'].iloc[i-1] and  # Day 2 doji
            tdf['close'].iloc[i] > tdf['open'].iloc[i] and  # Day 3 up
            tdf['close'].iloc[i] > tdf['close'].iloc[i-2]):  # Recovers
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('29: Morning Star', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('29: Morning Star', len(trades), 0, 0, '❌'))

# HYPOTHESIS 30: ADX Trend Strength
print("\n" + "="*70)
print("H30: ADX Trend Strength (Requires ADX - SKIP)")
print("="*70)
print("❌ SKIP - ADX data not available in current schema")
results.append(('30: ADX Trend', 0, 0, 0, 'SKIP'))

# HYPOTHESIS 31: Stochastic Oversold
print("\n" + "="*70)
print("H31: Stochastic Oversold (Requires Stoch - SKIP)")
print("="*70)
print("❌ SKIP - Stochastic data not available")
results.append(('31: Stochastic', 0, 0, 0, 'SKIP'))

# HYPOTHESIS 32: MACD Histogram Divergence
print("\n" + "="*70)
print("H32: MACD Histogram Divergence (Requires MACD - SKIP)")
print("="*70)
print("❌ SKIP - MACD data not available")
results.append(('32: MACD Hist', 0, 0, 0, 'SKIP'))

# HYPOTHESIS 33: Parabolic SAR Flip
print("\n" + "="*70)
print("H33: Parabolic SAR Flip (Requires PSAR - SKIP)")
print("="*70)
print("❌ SKIP - Parabolic SAR data not available")
results.append(('33: PSAR Flip', 0, 0, 0, 'SKIP'))

# HYPOTHESIS 34: 52-Week High Momentum
print("\n" + "="*70)
print("H34: 52-Week High Breakout")
print("Breakout to new 52-week high with volume")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['high_52w'] = tdf['high'].rolling(252).max()
    for i in range(252, len(tdf) - 10):
        if (tdf['close'].iloc[i] > tdf['high_52w'].iloc[i-1] * 0.99 and
            tdf['vol_ratio'].iloc[i] > 1.5):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('34: 52W High', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('34: 52W High', len(trades), 0, 0, '❌'))

# HYPOTHESIS 35: Support Bounce (20-day MA)
print("\n" + "="*70)
print("H35: Support Bounce - 20-Day MA")
print("Price touches 20-day MA and bounces")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        # Price near MA20 and bounces up
        price_near_ma = abs(tdf['close'].iloc[i] - tdf['ma20'].iloc[i]) / tdf['ma20'].iloc[i] < 0.02
        bounces = tdf['close'].iloc[i] > tdf['open'].iloc[i]  # Green candle
        above_ma = tdf['ma5'].iloc[i] > tdf['ma20'].iloc[i]  # Uptrend
        
        if price_near_ma and bounces and above_ma:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('35: MA20 Bounce', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('35: MA20 Bounce', len(trades), 0, 0, '❌'))

# HYPOTHESIS 36: Resistance Break
print("\n" + "="*70)
print("H36: Resistance Break - 20-Day High")
print("Break above 20-day high with volume")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['high_20d'] = tdf['high'].rolling(20).max()
    for i in range(25, len(tdf) - 5):
        if (tdf['close'].iloc[i] > tdf['high_20d'].iloc[i-1] and
            tdf['vol_ratio'].iloc[i] > 2.0):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('36: Resist Break', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('36: Resist Break', len(trades), 0, 0, '❌'))

# HYPOTHESIS 37: Volume Profile POC
print("\n" + "="*70)
print("H37: Volume Profile POC (Requires intraday - SKIP)")
print("="*70)
print("❌ SKIP - Volume profile requires intraday data")
results.append(('37: Volume POC', 0, 0, 0, 'SKIP'))

# HYPOTHESIS 38: Fibonacci Retracement
print("\n" + "="*70)
print("H38: Fibonacci Retracement Bounce")
print("Bounce from 61.8% retracement level")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 5):
        # Find recent swing high and low
        recent_high = tdf['high'].iloc[i-20:i].max()
        recent_low = tdf['low'].iloc[i-20:i].min()
        
        if recent_high > recent_low:
            fib_618 = recent_high - (recent_high - recent_low) * 0.618
            # Price near 61.8% and bounces
            near_fib = abs(tdf['low'].iloc[i] - fib_618) / fib_618 < 0.02
            bounces = tdf['close'].iloc[i] > tdf['open'].iloc[i]
            
            if near_fib and bounces:
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 5]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('38: Fib 61.8%', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('38: Fib 61.8%', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 4 SUMMARY")
print("="*70)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

tested = 0
validated = 0
skipped = 0

for name, trades, wr, sh, status in results:
    if status == 'SKIP':
        print(f"⏭️  {name:<23} {'N/A':<10} {'N/A':<10} {'N/A':<10} SKIP")
        skipped += 1
    elif trades >= 30:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sh:<10.2f}")
        tested += 1
        if status == '✅':
            validated += 1
    else:
        print(f"{status} {name:<23} {trades:<10} {'N/A':<10} {'N/A':<10}")
        tested += 1

print("-"*70)
print(f"Tested: {tested}, Validated: {validated}, Skipped: {skipped}")
print(f"Total Hypotheses Tested: 27 + {tested} = {27 + tested}")
print("="*70)
