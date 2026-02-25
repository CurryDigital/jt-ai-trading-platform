#!/usr/bin/env python3
"""
BATCH TEST 6: 10 New Hypotheses with Calculated Indicators
Using gold.technical_indicators_calculated
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
print("BATCH TEST 6: 10 New Hypotheses")
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

cursor.execute('''
SELECT DISTINCT ticker FROM gold.technical_indicators_calculated 
ORDER BY ticker LIMIT 100
''')
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

# H39: Bollinger Band Squeeze then Breakout
print("="*70)
print("H39: Bollinger Band Squeeze + Breakout")
print("BB width narrow, then breakout above upper band")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['bb_width'] = (tdf['bb_upper'] - tdf['bb_lower']) / tdf['bb_middle']
    tdf['bb_width_avg'] = tdf['bb_width'].rolling(20).mean()
    
    for i in range(25, len(tdf) - 5):
        squeeze = tdf['bb_width'].iloc[i-1] < tdf['bb_width_avg'].iloc[i-1] * 0.8
        breakout = tdf['close'].iloc[i] > tdf['bb_upper'].iloc[i]
        vol_spike = tdf['vol_ratio'].iloc[i] > 1.5
        
        if squeeze and breakout and vol_spike:
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
    results.append(('39: BB Squeeze', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('39: BB Squeeze', len(trades), 0, 0, '❌'))

# H40: RSI + MACD Combo
print("\n" + "="*70)
print("H40: RSI + MACD Combo")
print("RSI < 30 AND MACD histogram turning positive")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['rsi_14'].iloc[i] < 30 and 
            tdf['macd_histogram'].iloc[i-1] < 0 and 
            tdf['macd_histogram'].iloc[i] > 0):
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
    results.append(('40: RSI+MACD', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('40: RSI+MACD', len(trades), 0, 0, '❌'))

# H41: ATR Expansion Breakout
print("\n" + "="*70)
print("H41: ATR Expansion Breakout")
print("ATR spikes above 2x average + price breakout")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_avg'] = tdf['atr_14'].rolling(20).mean()
    
    for i in range(25, len(tdf) - 5):
        if (tdf['atr_14'].iloc[i] > tdf['atr_avg'].iloc[i] * 2 and
            tdf['close'].iloc[i] > tdf['close'].iloc[i-1] * 1.03 and
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
    results.append(('41: ATR Exp', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('41: ATR Exp', len(trades), 0, 0, '❌'))

# H42: Stochastic + RSI Extreme
print("\n" + "="*70)
print("H42: Stochastic + RSI Extreme")
print("Stoch K < 10 AND RSI < 15 (double extreme)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['stoch_k'].iloc[i] < 10 and tdf['rsi_14'].iloc[i] < 15:
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
    results.append(('42: Stoch+RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('42: Stoch+RSI', len(trades), 0, 0, '❌'))

# H43: BB Mean Reversion
print("\n" + "="*70)
print("H43: BB Mean Reversion")
print("Price below lower BB + volume spike")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and
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
    results.append(('43: BB MeanRev', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('43: BB MeanRev', len(trades), 0, 0, '❌'))

# H44: ADX + Volume Combo
print("\n" + "="*70)
print("H44: ADX + Volume Combo")
print("ADX > 30 (strong trend) + Volume > 2x + Price up > 2%")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['adx'].iloc[i] > 30 and
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['close'].iloc[i] > tdf['close'].iloc[i-1] * 1.02):
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
    results.append(('44: ADX+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('44: ADX+Vol', len(trades), 0, 0, '❌'))

# H45: VWAP + Volume Break
print("\n" + "="*70)
print("H45: VWAP + Volume Break")
print("Price above VWAP + Volume > 2.5x + Breakout > 3%")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['close'].iloc[i] > tdf['vwap'].iloc[i] and
            tdf['vol_ratio'].iloc[i] > 2.5 and
            tdf['close'].iloc[i] > tdf['close'].iloc[i-1] * 1.03):
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
    results.append(('45: VWAP+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('45: VWAP+Vol', len(trades), 0, 0, '❌'))

# H46: 3-Indicator Combo
print("\n" + "="*70)
print("H46: 3-Indicator Combo (RSI + MACD + Volume)")
print("RSI < 25 + MACD hist improving + Volume > 2x")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        rsi_ok = tdf['rsi_14'].iloc[i] < 25
        macd_improving = tdf['macd_histogram'].iloc[i] > tdf['macd_histogram'].iloc[i-1]
        vol_ok = tdf['vol_ratio'].iloc[i] > 2.0
        
        if rsi_ok and macd_improving and vol_ok:
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
    results.append(('46: 3-Ind Combo', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('46: 3-Ind Combo', len(trades), 0, 0, '❌'))

# H47: Momentum + Mean Reversion
print("\n" + "="*70)
print("H47: Extreme Bollinger Mean Reversion")
print("Price < BB lower - 2x ATR + Volume spike")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        extreme = tdf['close'].iloc[i] < (tdf['bb_lower'].iloc[i] - 2 * tdf['atr_14'].iloc[i])
        vol_spike = tdf['vol_ratio'].iloc[i] > 2.0
        
        if extreme and vol_spike:
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
    results.append(('47: BB Extreme', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('47: BB Extreme', len(trades), 0, 0, '❌'))

# H48: Trend + Volume Combo
print("\n" + "="*70)
print("H48: Trend + Volume Combo")
print("ADX > 20 with +DI > -DI + Volume > 3x + RSI 30-50")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        adx_ok = tdf['adx'].iloc[i] > 20
        trend_up = tdf['adx_plus_di'].iloc[i] > tdf['adx_minus_di'].iloc[i]
        vol_high = tdf['vol_ratio'].iloc[i] > 3.0
        rsi_mid = 30 < tdf['rsi_14'].iloc[i] < 50
        
        if adx_ok and trend_up and vol_high and rsi_mid:
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
    results.append(('48: Trend+Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('48: Trend+Vol', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 6 SUMMARY")
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
print(f"Total Hypotheses: 38 + {tested} = {38 + tested}")
print("="*70)
