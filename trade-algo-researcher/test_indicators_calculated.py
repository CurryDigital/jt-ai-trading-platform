#!/usr/bin/env python3
"""
CALCULATE Technical Indicators from Price Data
Use existing silver.historical_stock_data to compute all indicators
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
print("CALCULATE: Technical Indicators from Price Data")
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

# Get tickers with sufficient data
cursor = conn.cursor()
cursor.execute('''
SELECT ticker, COUNT(*) as count 
FROM silver.historical_stock_data 
WHERE date >= '2022-01-01'
GROUP BY ticker 
HAVING COUNT(*) > 300
ORDER BY count DESC
LIMIT 50
''')
tickers_data = cursor.fetchall()
cursor.close()

tickers = [t[0] for t in tickers_data]
print(f"Testing on {len(tickers)} tickers with 300+ days of data")

ticker_list = "','".join(tickers[:30])  # Test on 30
query = f"""
SELECT date, ticker, open, high, low, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {df['ticker'].nunique()} tickers, {len(df)} records\n")

# Calculate all indicators
def calculate_indicators(tdf):
    """Calculate all technical indicators"""
    tdf = tdf.copy()
    
    # 1. Stochastic Oscillator (14, 3)
    lowest_low = tdf['low'].rolling(window=14).min()
    highest_high = tdf['high'].rolling(window=14).max()
    tdf['stoch_k'] = 100 * (tdf['close'] - lowest_low) / (highest_high - lowest_low)
    tdf['stoch_d'] = tdf['stoch_k'].rolling(window=3).mean()
    
    # 2. MACD (12, 26, 9)
    ema_12 = tdf['close'].ewm(span=12, adjust=False).mean()
    ema_26 = tdf['close'].ewm(span=26, adjust=False).mean()
    tdf['macd_line'] = ema_12 - ema_26
    tdf['macd_signal'] = tdf['macd_line'].ewm(span=9, adjust=False).mean()
    tdf['macd_histogram'] = tdf['macd_line'] - tdf['macd_signal']
    
    # 3. ADX (14) - Simplified calculation
    tr1 = tdf['high'] - tdf['low']
    tr2 = abs(tdf['high'] - tdf['close'].shift(1))
    tr3 = abs(tdf['low'] - tdf['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_dm = tdf['high'].diff()
    minus_dm = -tdf['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    atr = tr.rolling(window=14).mean()
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    tdf['adx'] = dx.rolling(window=14).mean()
    tdf['adx_plus_di'] = plus_di
    tdf['adx_minus_di'] = minus_di
    
    # 4. VWAP
    typical_price = (tdf['high'] + tdf['low'] + tdf['close']) / 3
    tdf['vwap'] = (typical_price * tdf['volume']).cumsum() / tdf['volume'].cumsum()
    
    return tdf

all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf = calculate_indicators(tdf)
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna()

print(f"After indicator calculation: {len(df)} records\n")

# Now test 5 hypotheses
results = []

# H30: ADX Trend Strength
print("="*70)
print("H30: ADX Trend Strength (ADX > 25, +DI > -DI)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 10):
        if (tdf['adx'].iloc[i] > 25 and 
            tdf['adx_plus_di'].iloc[i] > tdf['adx_minus_di'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('30: ADX Trend', len(trades), wr, sh, status))
else:
    print(f"Insufficient: {len(trades)}")
    results.append(('30: ADX Trend', len(trades), 0, 0, '❌'))

# H31: Stochastic Oversold
print("\n" + "="*70)
print("H31: Stochastic Oversold (K < 20)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 10):
        if tdf['stoch_k'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('31: Stoch Oversold', len(trades), wr, sh, status))
else:
    print(f"Insufficient: {len(trades)}")
    results.append(('31: Stoch Oversold', len(trades), 0, 0, '❌'))

# H32: MACD Histogram Divergence
print("\n" + "="*70)
print("H32: MACD Histogram Bullish Divergence")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 10):
        price_ll = tdf['close'].iloc[i] < tdf['close'].iloc[i-5:i].min()
        hist_hl = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-5:i].min()
        if price_ll and hist_hl and tdf['macd_histogram'].iloc[i] < 0:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('32: MACD Div', len(trades), wr, sh, status))
else:
    print(f"Insufficient: {len(trades)}")
    results.append(('32: MACD Div', len(trades), 0, 0, '❌'))

# H33: MACD Crossover (using histogram turning positive)
print("\n" + "="*70)
print("H33: MACD Histogram Turn (Negative to Positive)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 10):
        prev_neg = tdf['macd_histogram'].iloc[i-1] < 0
        curr_pos = tdf['macd_histogram'].iloc[i] > 0
        if prev_neg and curr_pos:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('33: MACD Cross', len(trades), wr, sh, status))
else:
    print(f"Insufficient: {len(trades)}")
    results.append(('33: MACD Cross', len(trades), 0, 0, '❌'))

# H37: VWAP Mean Reversion
print("\n" + "="*70)
print("H37: VWAP Mean Reversion (Price 3% below VWAP)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(30, len(tdf) - 10):
        if tdf['close'].iloc[i] < tdf['vwap'].iloc[i] * 0.97:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('37: VWAP Rev', len(trades), wr, sh, status))
else:
    print(f"Insufficient: {len(trades)}")
    results.append(('37: VWAP Rev', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("SUMMARY: 5 Technical Indicator Strategies")
print("="*70)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

validated = 0
for name, trades, wr, sh, status in results:
    if trades >= 30:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sh:<10.2f}")
        if status == '✅':
            validated += 1
    else:
        print(f"{status} {name:<23} {trades:<10} N/A")

print("-"*70)
print(f"Validated: {validated}/5")
print("="*70)
