#!/usr/bin/env python3
"""
TEST: 5 Hypotheses with NEW Technical Indicator Data
Data now available in silver.technical_indicators
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
print("TEST: 5 Hypotheses with NEW Technical Indicators")
print("Data from: silver.technical_indicators")
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

# Check available data
cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT ticker) FROM silver.technical_indicators')
tech_count = cursor.fetchone()[0]

print(f"Technical indicators available for {tech_count} tickers")
print()

# Get tickers with tech indicators
cursor.execute('SELECT DISTINCT ticker FROM silver.technical_indicators LIMIT 22')
tech_tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

# Get price data for these tickers
ticker_list = "','".join(tech_tickers)
query = f"""
SELECT t.date, t.ticker, t.close, t.high, t.low, t.volume,
       ti.macd_histogram, ti.stoch_k, ti.stoch_d, ti.adx, 
       ti.adx_plus_di, ti.adx_minus_di, ti.psar, ti.psar_direction, ti.vwap
FROM silver.historical_stock_data t
LEFT JOIN silver.technical_indicators ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') 
  AND t.date BETWEEN '2025-11-01' AND '2026-02-28'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# HYPOTHESIS 30: ADX Trend Strength
print("="*70)
print("H30: ADX Trend Strength")
print("Buy when ADX > 25 (strong trend) and +DI > -DI (bullish)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').dropna()
    if len(tdf) < 10:
        continue
    for i in range(1, len(tdf) - 5):
        if (tdf['adx'].iloc[i] > 25 and 
            tdf['adx_plus_di'].iloc[i] > tdf['adx_minus_di'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('30: ADX Trend', len(trades), wr, sh, status))
else:
    print(f"Insufficient trades: {len(trades)}")
    results.append(('30: ADX Trend', len(trades), 0, 0, '❌'))

# HYPOTHESIS 31: Stochastic Oversold
print("\n" + "="*70)
print("H31: Stochastic Oversold Mean Reversion")
print("Buy when Stoch K < 20 (oversold), exit when K > 50")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').dropna()
    if len(tdf) < 10:
        continue
    for i in range(1, len(tdf) - 10):
        if tdf['stoch_k'].iloc[i] < 20:  # Oversold
            entry = tdf['close'].iloc[i]
            # Exit when K > 50 or 10 days
            exit_price = None
            for j in range(i+1, min(i+11, len(tdf))):
                if tdf['stoch_k'].iloc[j] > 50:
                    exit_price = tdf['close'].iloc[j]
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+10, len(tdf)-1)]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('31: Stoch Oversold', len(trades), wr, sh, status))
else:
    print(f"Insufficient trades: {len(trades)}")
    results.append(('31: Stoch Oversold', len(trades), 0, 0, '❌'))

# HYPOTHESIS 32: MACD Histogram Divergence
print("\n" + "="*70)
print("H32: MACD Histogram Bullish Divergence")
print("Price makes lower low but MACD histogram makes higher low")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').dropna()
    if len(tdf) < 10:
        continue
    for i in range(5, len(tdf) - 5):
        # Look for divergence: price lower, histogram higher
        price_ll = tdf['close'].iloc[i] < tdf['close'].iloc[i-5:i].min()
        hist_hl = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-5:i].min()
        
        if price_ll and hist_hl and tdf['macd_histogram'].iloc[i] < 0:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('32: MACD Div', len(trades), wr, sh, status))
else:
    print(f"Insufficient trades: {len(trades)}")
    results.append(('32: MACD Div', len(trades), 0, 0, '❌'))

# HYPOTHESIS 33: PSAR Flip
print("\n" + "="*70)
print("H33: Parabolic SAR Direction Flip")
print("Buy when PSAR flips from bear to bull")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').dropna()
    if len(tdf) < 10:
        continue
    for i in range(1, len(tdf) - 5):
        # Previous bear, current bull
        prev_bear = tdf['psar_direction'].iloc[i-1] == 'bear'
        curr_bull = tdf['psar_direction'].iloc[i] == 'bull'
        
        if prev_bear and curr_bull:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('33: PSAR Flip', len(trades), wr, sh, status))
else:
    print(f"Insufficient trades: {len(trades)}")
    results.append(('33: PSAR Flip', len(trades), 0, 0, '❌'))

# HYPOTHESIS 37: VWAP Mean Reversion (Volume Profile simplified)
print("\n" + "="*70)
print("H37: VWAP Mean Reversion")
print("Buy when price 3% below VWAP (volume-weighted support)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').dropna()
    if len(tdf) < 10:
        continue
    for i in range(1, len(tdf) - 5):
        # Price below VWAP
        if tdf['close'].iloc[i] < tdf['vwap'].iloc[i] * 0.97:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('37: VWAP Reversion', len(trades), wr, sh, status))
else:
    print(f"Insufficient trades: {len(trades)}")
    results.append(('37: VWAP Reversion', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("SUMMARY: 5 Hypotheses with Technical Indicators")
print("="*70)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

validated = 0
for name, trades, wr, sh, status in results:
    if trades >= 10:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sh:<10.2f}")
        if status == '✅':
            validated += 1
    else:
        print(f"{status} {name:<23} {trades:<10} N/A       N/A")

print("-"*70)
print(f"Validated: {validated}/5")
print("="*70)
