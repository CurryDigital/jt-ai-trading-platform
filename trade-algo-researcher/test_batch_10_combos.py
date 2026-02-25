#!/usr/bin/env python3
"""
BATCH TEST 10: Combination Matrix - Testing New Indicator Combos
Testing various 3, 4, and 5 indicator combinations
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
print("BATCH TEST 10: Combination Matrix - New Indicator Combos")
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

# H79: 4-Indicator Super Combo
print("="*70)
print("H79: 4-Indicator Super Combo")
print("RSI < 20 + Stoch < 20 + MACD improving + Volume > 2.5x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        rsi_ok = tdf['rsi_14'].iloc[i] < 20
        stoch_ok = tdf['stoch_k'].iloc[i] < 20
        macd_ok = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-1]
        vol_ok = tdf['vol_ratio'].iloc[i] > 2.5
        
        if rsi_ok and stoch_ok and macd_ok and vol_ok:
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
    results.append(('79: 4-Ind Super', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('79: 4-Ind Super', len(trades), 0, 0, '❌'))

# H80: BB + RSI + Volume Triple
print("\n" + "="*70)
print("H80: BB + RSI + Volume Triple")
print("Price < BB lower + RSI < 20 + Volume > 3x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        bb_ok = tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i]
        rsi_ok = tdf['rsi_14'].iloc[i] < 20
        vol_ok = tdf['vol_ratio'].iloc[i] > 3.0
        
        if bb_ok and rsi_ok and vol_ok:
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
    results.append(('80: BB+RSI+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('80: BB+RSI+Vol', len(trades), 0, 0, '❌'))

# H81: VWAP + RSI + ATR Combo
print("\n" + "="*70)
print("H81: VWAP + RSI + ATR Combo")
print("Price < VWAP + RSI < 25 + ATR contraction (< 0.8x avg)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_avg'] = tdf['atr_14'].rolling(20).mean()
    for i in range(25, len(tdf) - 10):
        vwap_ok = tdf['close'].iloc[i] < tdf['vwap'].iloc[i]
        rsi_ok = tdf['rsi_14'].iloc[i] < 25
        atr_ok = tdf['atr_14'].iloc[i] < tdf['atr_avg'].iloc[i] * 0.8
        
        if vwap_ok and rsi_ok and atr_ok:
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
    results.append(('81: VWAP+RSI+ATR', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('81: VWAP+RSI+ATR', len(trades), 0, 0, '❌'))

# H82: Stoch + MACD + Volume
print("\n" + "="*70)
print("H82: Stoch + MACD + Volume")
print("Stoch K < 15 + MACD hist > 0 + Volume > 2.5x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        stoch_ok = tdf['stoch_k'].iloc[i] < 15
        macd_ok = tdf['macd_histogram'].iloc[i] > 0
        vol_ok = tdf['vol_ratio'].iloc[i] > 2.5
        
        if stoch_ok and macd_ok and vol_ok:
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
    results.append(('82: Stoch+MACD+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('82: Stoch+MACD+Vol', len(trades), 0, 0, '❌'))

# H83: ADX + RSI + Stoch Trend
print("\n" + "="*70)
print("H83: ADX + RSI + Stoch Trend")
print("ADX > 20 + RSI 25-40 + Stoch turning up")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        adx_ok = tdf['adx'].iloc[i] > 20
        rsi_range = 25 < tdf['rsi_14'].iloc[i] < 40
        stoch_up = tdf['stoch_k'].iloc[i] > tdf['stoch_k'].iloc[i-1]
        
        if adx_ok and rsi_range and stoch_up:
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
    results.append(('83: ADX+RSI+Stoch', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('83: ADX+RSI+Stoch', len(trades), 0, 0, '❌'))

# H84: BB Squeeze + Stoch + Volume
print("\n" + "="*70)
print("H84: BB Squeeze + Stoch + Volume")
print("BB width < 5% of price + Stoch < 20 + Vol > 2.5x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['bb_width'] = (tdf['bb_upper'] - tdf['bb_lower']) / tdf['bb_middle']
    for i in range(25, len(tdf) - 10):
        squeeze = tdf['bb_width'].iloc[i] < 0.05
        stoch_ok = tdf['stoch_k'].iloc[i] < 20
        vol_ok = tdf['vol_ratio'].iloc[i] > 2.5
        
        if squeeze and stoch_ok and vol_ok:
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
    results.append(('84: BB+Stoch+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('84: BB+Stoch+Vol', len(trades), 0, 0, '❌'))

# H85: ATR + RSI + Volume Spike
print("\n" + "="*70)
print("H85: ATR + RSI + Volume Spike")
print("ATR > 1.5x avg + RSI < 30 + Volume > 3x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_avg'] = tdf['atr_14'].rolling(20).mean()
    for i in range(25, len(tdf) - 10):
        atr_ok = tdf['atr_14'].iloc[i] > tdf['atr_avg'].iloc[i] * 1.5
        rsi_ok = tdf['rsi_14'].iloc[i] < 30
        vol_ok = tdf['vol_ratio'].iloc[i] > 3.0
        
        if atr_ok and rsi_ok and vol_ok:
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
    results.append(('85: ATR+RSI+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('85: ATR+RSI+Vol', len(trades), 0, 0, '❌'))

# H86: MACD + RSI + BB %B
print("\n" + "="*70)
print("H86: MACD + RSI + BB %B")
print("MACD hist improving + RSI < 25 + %B < 0.1")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        macd_ok = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-1]
        rsi_ok = tdf['rsi_14'].iloc[i] < 25
        bb_range = tdf['bb_upper'].iloc[i] - tdf['bb_lower'].iloc[i]
        bb_b = (tdf['close'].iloc[i] - tdf['bb_lower'].iloc[i]) / bb_range if bb_range > 0 else 0.5
        bb_ok = bb_b < 0.1
        
        if macd_ok and rsi_ok and bb_ok:
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
    results.append(('86: MACD+RSI+BB', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('86: MACD+RSI+BB', len(trades), 0, 0, '❌'))

# H87: 5-Indicator MEGA Combo
print("\n" + "="*70)
print("H87: 5-Indicator MEGA Combo")
print("RSI<20 + Stoch<15 + MACD>0 + Vol>2x + Price<BB lower")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        rsi_ok = tdf['rsi_14'].iloc[i] < 20
        stoch_ok = tdf['stoch_k'].iloc[i] < 15
        macd_ok = tdf['macd_histogram'].iloc[i] > 0
        vol_ok = tdf['vol_ratio'].iloc[i] > 2.0
        bb_ok = tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i]
        
        if rsi_ok and stoch_ok and macd_ok and vol_ok and bb_ok:
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
    results.append(('87: 5-Ind MEGA', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('87: 5-Ind MEGA', len(trades), 0, 0, '❌'))

# H88: VWAP Deviation + RSI + Stoch
print("\n" + "="*70)
print("H88: VWAP Deviation + RSI + Stoch")
print("Price < 0.95x VWAP + RSI < 25 + Stoch < 15")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        vwap_dev = tdf['close'].iloc[i] < tdf['vwap'].iloc[i] * 0.95
        rsi_ok = tdf['rsi_14'].iloc[i] < 25
        stoch_ok = tdf['stoch_k'].iloc[i] < 15
        
        if vwap_dev and rsi_ok and stoch_ok:
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
    results.append(('88: VWAP+RSI+Stoch', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('88: VWAP+RSI+Stoch', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 10: COMBINATION MATRIX SUMMARY")
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
print(f"Total Hypotheses: 77 + {tested} = {77 + tested}")
print("="*70)

if validated > 0:
    print("\n🎉 NEW COMBINATIONS FOUND!")
else:
    print("\n📊 No new combinations validated this batch.")
    print("💡 Insight: May have reached limits of indicator combinations.")
