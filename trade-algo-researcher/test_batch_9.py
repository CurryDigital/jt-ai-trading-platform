#!/usr/bin/env python3
"""
BATCH TEST 9: 10 New Hypotheses
Continuation of systematic testing
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
print("BATCH TEST 9: 10 New Hypotheses")
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

cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT ticker) FROM gold.technical_indicators_calculated')
tech_count = cursor.fetchone()[0]
print(f"Indicators available for {tech_count} tickers\n")

cursor.execute('SELECT DISTINCT ticker FROM gold.technical_indicators_calculated ORDER BY ticker LIMIT 100')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT t.date, t.ticker, t.open, t.high, t.low, t.close, t.volume,
       ti.rsi_14, ti.stoch_k, ti.stoch_d, ti.macd_histogram,
       ti.adx, ti.adx_plus_di, ti.adx_minus_di, ti.vwap,
       ti.bb_upper, ti.bb_lower, ti.bb_middle, ti.atr_14, ti.vol_ratio
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

# H69: Doji + Volume Spike (Indecision breakout)
print("="*70)
print("H69: Doji + Volume Spike")
print("Doji candle (body < 10% of range) + volume > 3x + next day breakout")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        body = abs(tdf['close'].iloc[i-1] - tdf['open'].iloc[i-1])
        range_val = tdf['high'].iloc[i-1] - tdf['low'].iloc[i-1]
        doji = body < range_val * 0.1 if range_val > 0 else False
        high_vol = tdf['vol_ratio'].iloc[i-1] > 3.0
        breakout = tdf['close'].iloc[i] > tdf['high'].iloc[i-1]
        
        if doji and high_vol and breakout:
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
    results.append(('69: Doji+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('69: Doji+Vol', len(trades), 0, 0, '❌'))

# H70: RSI Divergence (Price lower low, RSI higher low)
print("\n" + "="*70)
print("H70: RSI Bullish Divergence")
print("Price makes lower low over 5 days but RSI makes higher low")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        price_lower = tdf['close'].iloc[i] < tdf['close'].iloc[i-5]
        rsi_higher = tdf['rsi_14'].iloc[i] > tdf['rsi_14'].iloc[i-5]
        oversold = tdf['rsi_14'].iloc[i] < 40
        
        if price_lower and rsi_higher and oversold:
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
    results.append(('70: RSI Divergence', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('70: RSI Divergence', len(trades), 0, 0, '❌'))

# H71: Volume Profile (High volume node bounce)
print("\n" + "="*70)
print("H71: Volume Climax")
print("Highest volume in 20 days + RSI < 35 (capitulation)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['vol_max_20'] = tdf['volume'].rolling(20).max()
    for i in range(25, len(tdf) - 5):
        climax = tdf['volume'].iloc[i] >= tdf['vol_max_20'].iloc[i] * 0.95
        oversold = tdf['rsi_14'].iloc[i] < 35
        
        if climax and oversold:
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
    results.append(('71: Volume Climax', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('71: Volume Climax', len(trades), 0, 0, '❌'))

# H72: Three White Soldiers (with volume)
print("\n" + "="*70)
print("H72: Three White Soldiers + Volume")
print("3 consecutive green candles with increasing volume")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        green1 = tdf['close'].iloc[i-2] > tdf['open'].iloc[i-2]
        green2 = tdf['close'].iloc[i-1] > tdf['open'].iloc[i-1]
        green3 = tdf['close'].iloc[i] > tdf['open'].iloc[i]
        vol_increasing = (tdf['volume'].iloc[i-1] > tdf['volume'].iloc[i-2] and 
                         tdf['volume'].iloc[i] > tdf['volume'].iloc[i-1])
        
        if green1 and green2 and green3 and vol_increasing:
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
    results.append(('72: 3 White Soldiers', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('72: 3 White Soldiers', len(trades), 0, 0, '❌'))

# H73: Hammer Pattern (with RSI oversold)
print("\n" + "="*70)
print("H73: Hammer Pattern + Oversold")
print("Lower shadow > 2x body + RSI < 30")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        body = abs(tdf['close'].iloc[i] - tdf['open'].iloc[i])
        lower_shadow = min(tdf['open'].iloc[i], tdf['close'].iloc[i]) - tdf['low'].iloc[i]
        hammer = lower_shadow > body * 2 if body > 0 else lower_shadow > 0
        oversold = tdf['rsi_14'].iloc[i] < 30
        
        if hammer and oversold:
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
    results.append(('73: Hammer+Oversold', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('73: Hammer+Oversold', len(trades), 0, 0, '❌'))

# H74: ADX Trend Strength Entry
print("\n" + "="*70)
print("H74: ADX Trend Strength Entry")
print("ADX > 25 + +DI > -DI + volume > 2x + pullback to VWAP")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        adx_strong = tdf['adx'].iloc[i] > 25
        trend_up = tdf['adx_plus_di'].iloc[i] > tdf['adx_minus_di'].iloc[i]
        high_vol = tdf['vol_ratio'].iloc[i] > 2.0
        at_vwap = abs(tdf['close'].iloc[i] - tdf['vwap'].iloc[i]) / tdf['vwap'].iloc[i] < 0.02
        
        if adx_strong and trend_up and high_vol and at_vwap:
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
    results.append(('74: ADX+VWAP', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('74: ADX+VWAP', len(trades), 0, 0, '❌'))

# H75: BB %B Extreme
print("\n" + "="*70)
print("H75: BB %B Extreme Mean Reversion")
print("%B < 0 (below lower band) + volume spike + RSI < 25")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        bb_b = (tdf['close'].iloc[i] - tdf['bb_lower'].iloc[i]) / (tdf['bb_upper'].iloc[i] - tdf['bb_lower'].iloc[i]) if (tdf['bb_upper'].iloc[i] - tdf['bb_lower'].iloc[i]) > 0 else 0.5
        extreme = bb_b < 0
        high_vol = tdf['vol_ratio'].iloc[i] > 2.0
        oversold = tdf['rsi_14'].iloc[i] < 25
        
        if extreme and high_vol and oversold:
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
    results.append(('75: BB %B Extreme', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('75: BB %B Extreme', len(trades), 0, 0, '❌'))

# H76: Volume Weighted RSI
print("\n" + "="*70)
print("H76: Volume-Weighted RSI Signal")
print("RSI < 20 + volume > 2.5x + close in upper half of range")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        rsi_extreme = tdf['rsi_14'].iloc[i] < 20
        high_vol = tdf['vol_ratio'].iloc[i] > 2.5
        range_val = tdf['high'].iloc[i] - tdf['low'].iloc[i]
        upper_half = (tdf['close'].iloc[i] - tdf['low'].iloc[i]) / range_val > 0.5 if range_val > 0 else False
        
        if rsi_extreme and high_vol and upper_half:
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
    results.append(('76: Vol-Weighted RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('76: Vol-Weighted RSI', len(trades), 0, 0, '❌'))

# H77: Consecutive Range Compression
print("\n" + "="*70)
print("H77: Consecutive Range Compression")
print("3 days of decreasing range + then volume breakout")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['range'] = tdf['high'] - tdf['low']
    for i in range(25, len(tdf) - 5):
        compressing = (tdf['range'].iloc[i-3] > tdf['range'].iloc[i-2] > 
                      tdf['range'].iloc[i-1])
        breakout = tdf['vol_ratio'].iloc[i] > 2.5
        price_up = tdf['close'].iloc[i] > tdf['close'].iloc[i-1]
        
        if compressing and breakout and price_up:
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
    results.append(('77: Range Compress', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('77: Range Compress', len(trades), 0, 0, '❌'))

# H78: Stochastic + Volume Combo
print("\n" + "="*70)
print("H78: Stochastic + Volume Combo")
print("Stoch K < 15 + Volume > 3x + price reversal (hammer or engulfing)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        stoch_extreme = tdf['stoch_k'].iloc[i] < 15
        high_vol = tdf['vol_ratio'].iloc[i] > 3.0
        # Hammer check
        body = abs(tdf['close'].iloc[i] - tdf['open'].iloc[i])
        lower_shadow = min(tdf['open'].iloc[i], tdf['close'].iloc[i]) - tdf['low'].iloc[i]
        hammer = lower_shadow > body * 1.5 if body > 0 else False
        
        if stoch_extreme and high_vol and hammer:
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
    results.append(('78: Stoch+Vol Combo', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('78: Stoch+Vol Combo', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 9 SUMMARY")
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
print(f"Total Hypotheses: 67 + {tested} = {67 + tested}")
print("="*70)
