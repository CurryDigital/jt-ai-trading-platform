#!/usr/bin/env python3
"""
BATCH TEST 8: 10 New Hypotheses
Using calculated technical indicators
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
print("BATCH TEST 8: 10 New Hypotheses")
print("Using: gold.technical_indicators_calculated")
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

# Get data with calculated indicators
cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT ticker) FROM gold.technical_indicators_calculated')
tech_count = cursor.fetchone()[0]
print(f"Indicators available for {tech_count} tickers\n")

# Get tickers
cursor.execute('''
SELECT DISTINCT ticker FROM gold.technical_indicators_calculated 
ORDER BY ticker LIMIT 100
''')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT t.date, t.ticker, t.open, t.high, t.low, t.close, t.volume,
       ti.rsi_14, ti.stoch_k, ti.stoch_d, ti.macd_line, ti.macd_signal, ti.macd_histogram,
       ti.adx, ti.vwap, ti.bb_upper, ti.bb_lower, ti.bb_middle, ti.atr_14, ti.vol_ratio
FROM silver.historical_stock_data t
INNER JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# H59: Stochastic Crossover in Oversold
print("="*70)
print("H59: Stochastic Crossover (Oversold)")
print("Stoch K crosses above Stoch D when both < 20")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['stoch_k'].iloc[i-1] < tdf['stoch_d'].iloc[i-1] and  # Was below
            tdf['stoch_k'].iloc[i] > tdf['stoch_d'].iloc[i] and      # Crossed above
            tdf['stoch_k'].iloc[i] < 20 and                          # Still oversold
            tdf['stoch_d'].iloc[i] < 20):
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
    results.append(('59: Stoch Cross', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('59: Stoch Cross', len(trades), 0, 0, '❌'))

# H60: MACD Zero Line Cross
print("\n" + "="*70)
print("H60: MACD Zero Line Cross")
print("MACD line crosses above zero with volume > 1.5x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['macd_line'].iloc[i-1] < 0 and 
            tdf['macd_line'].iloc[i] > 0 and
            tdf['vol_ratio'].iloc[i] > 1.5):
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
    results.append(('60: MACD Zero Cross', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('60: MACD Zero Cross', len(trades), 0, 0, '❌'))

# H61: Bollinger Band Walk (Strong Trend)
print("\n" + "="*70)
print("H61: BB Walk (Strong Trend)")
print("3 consecutive closes near upper BB + volume > 2x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        bb_pos_1 = (tdf['close'].iloc[i-2] - tdf['bb_middle'].iloc[i-2]) / (tdf['bb_upper'].iloc[i-2] - tdf['bb_middle'].iloc[i-2])
        bb_pos_2 = (tdf['close'].iloc[i-1] - tdf['bb_middle'].iloc[i-1]) / (tdf['bb_upper'].iloc[i-1] - tdf['bb_middle'].iloc[i-1])
        bb_pos_3 = (tdf['close'].iloc[i] - tdf['bb_middle'].iloc[i]) / (tdf['bb_upper'].iloc[i] - tdf['bb_middle'].iloc[i])
        
        if (bb_pos_1 > 0.8 and bb_pos_2 > 0.8 and bb_pos_3 > 0.8 and
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
    results.append(('61: BB Walk', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('61: BB Walk', len(trades), 0, 0, '❌'))

# H62: RSI + Stochastic Combo
print("\n" + "="*70)
print("H62: RSI + Stochastic Combo")
print("RSI < 25 AND Stoch K < 20 AND both turning up")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['rsi_14'].iloc[i] < 25 and 
            tdf['stoch_k'].iloc[i] < 20 and
            tdf['rsi_14'].iloc[i] > tdf['rsi_14'].iloc[i-1] and  # Turning up
            tdf['stoch_k'].iloc[i] > tdf['stoch_k'].iloc[i-1]):
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
    results.append(('62: RSI+Stoch Combo', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('62: RSI+Stoch Combo', len(trades), 0, 0, '❌'))

# H63: Consecutive Inside Days
print("\n" + "="*70)
print("H63: Consecutive Inside Days Breakout")
print("2+ inside days then breakout with volume")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        # Check if yesterday and day before were inside days
        prev_high_2 = tdf['high'].iloc[i-3] if i >= 3 else tdf['high'].iloc[i-2]
        prev_low_2 = tdf['low'].iloc[i-3] if i >= 3 else tdf['low'].iloc[i-2]
        
        inside_day_1 = (tdf['high'].iloc[i-2] < prev_high_2 and 
                       tdf['low'].iloc[i-2] > prev_low_2)
        inside_day_2 = (tdf['high'].iloc[i-1] < tdf['high'].iloc[i-2] and 
                       tdf['low'].iloc[i-1] > tdf['low'].iloc[i-2])
        
        breakout = (tdf['close'].iloc[i] > tdf['high'].iloc[i-1] and
                   tdf['vol_ratio'].iloc[i] > 2.0)
        
        if inside_day_1 and inside_day_2 and breakout:
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
    results.append(('63: 2x Inside Days', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('63: 2x Inside Days', len(trades), 0, 0, '❌'))

# H64: VWAP Bounce
print("\n" + "="*70)
print("H64: VWAP Bounce")
print("Price drops below VWAP then bounces back above with volume")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        below_vwap = tdf['close'].iloc[i-1] < tdf['vwap'].iloc[i-1]
        above_vwap = tdf['close'].iloc[i] > tdf['vwap'].iloc[i]
        vol_spike = tdf['vol_ratio'].iloc[i] > 2.0
        
        if below_vwap and above_vwap and vol_spike:
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
    results.append(('64: VWAP Bounce', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('64: VWAP Bounce', len(trades), 0, 0, '❌'))

# H65: MACD Histogram Divergence
print("\n" + "="*70)
print("H65: MACD Histogram Divergence")
print("Price makes lower low but MACD hist makes higher low")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        # Look for 5-day divergence
        if i >= 5:
            price_lower = tdf['close'].iloc[i] < tdf['close'].iloc[i-5]
            hist_higher = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-5]
            oversold = tdf['rsi_14'].iloc[i] < 35
            
            if price_lower and hist_higher and oversold:
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
    results.append(('65: MACD Div', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('65: MACD Div', len(trades), 0, 0, '❌'))

# H66: Volume at Support (using VWAP as proxy)
print("\n" + "="*70)
print("H66: Volume at Support Level")
print("Price at/below VWAP support + Volume > 3x + RSI < 30")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        at_support = tdf['close'].iloc[i] <= tdf['vwap'].iloc[i] * 1.02
        high_vol = tdf['vol_ratio'].iloc[i] > 3.0
        oversold = tdf['rsi_14'].iloc[i] < 30
        
        if at_support and high_vol and oversold:
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
    results.append(('66: Vol at Support', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('66: Vol at Support', len(trades), 0, 0, '❌'))

# H67: BB Squeeze + RSI Filter
print("\n" + "="*70)
print("H67: BB Squeeze + RSI Filter")
print("BB width at 20-day low + RSI < 50 + breakout")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['bb_width'] = (tdf['bb_upper'] - tdf['bb_lower']) / tdf['bb_middle']
    tdf['bb_width_min'] = tdf['bb_width'].rolling(20).min()
    
    for i in range(25, len(tdf) - 5):
        squeeze = tdf['bb_width'].iloc[i-1] <= tdf['bb_width_min'].iloc[i-1] * 1.1
        rsi_ok = tdf['rsi_14'].iloc[i-1] < 50
        breakout = tdf['close'].iloc[i] > tdf['bb_upper'].iloc[i-1]
        vol_ok = tdf['vol_ratio'].iloc[i] > 1.5
        
        if squeeze and rsi_ok and breakout and vol_ok:
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
    results.append(('67: BB Squeeze+RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('67: BB Squeeze+RSI', len(trades), 0, 0, '❌'))

# H68: ATR Volatility Contraction
print("\n" + "="*70)
print("H68: ATR Volatility Contraction")
print("ATR at 10-day low + price compression + volume breakout")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_low_10'] = tdf['atr_14'].rolling(10).min()
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['range_avg'] = tdf['range'].rolling(10).mean()
    
    for i in range(25, len(tdf) - 5):
        atr_contracted = tdf['atr_14'].iloc[i-1] <= tdf['atr_low_10'].iloc[i-1] * 1.1
        price_compressed = tdf['range'].iloc[i-1] < tdf['range_avg'].iloc[i-1] * 0.8
        vol_breakout = tdf['vol_ratio'].iloc[i] > 2.5
        price_breakout = tdf['close'].iloc[i] > tdf['close'].iloc[i-1] * 1.02
        
        if atr_contracted and price_compressed and vol_breakout and price_breakout:
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
    results.append(('68: ATR Contract', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('68: ATR Contract', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 8 SUMMARY")
print("="*70)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

validated = 0
tested = 0

for name, trades, wr, sh, status in results:
    if trades >= 30:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sh:<10.2f}")
        tested += 1
        if status == '✅':
            validated += 1
    else:
        print(f"{status} {name:<23} {trades:<10} N/A       N/A")
        tested += 1

print("-"*70)
print(f"Tested: {tested}, Validated: {validated}")
print(f"Total Hypotheses: 57 + {tested} = {57 + tested}")
print("="*70)
