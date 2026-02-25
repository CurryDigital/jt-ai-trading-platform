#!/usr/bin/env python3
"""
BATCH TEST: 10 New Hypotheses
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

print("="*70)
print("BATCH TEST: 10 New Hypotheses")
print(f"Universe: {df['ticker'].nunique()} tickers, {len(df)} records")
print("="*70)

results = []

# HYPOTHESIS 18: Doji Star
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['body'] = abs(tdf['close'] - tdf['open'])
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['doji'] = tdf['body'] <= (tdf['range'] * 0.1)
    tdf['prev_return'] = tdf['close'].pct_change()
    
    for i in range(5, len(tdf) - 5):
        if tdf['doji'].iloc[i] and abs(tdf['prev_return'].iloc[i-1]) > 0.03:
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('18: Doji Star', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('18: Doji Star', len(trades), 0, 0, '❌'))

# HYPOTHESIS 19: Hammer Pattern
# Lower shadow > 2x body, small upper shadow
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['body'] = abs(tdf['close'] - tdf['open'])
    tdf['lower_shadow'] = tdf[['open', 'close']].min(axis=1) - tdf['low']
    tdf['upper_shadow'] = tdf['high'] - tdf[['open', 'close']].max(axis=1)
    tdf['hammer'] = (tdf['lower_shadow'] > tdf['body'] * 2) & (tdf['upper_shadow'] < tdf['body'])
    
    for i in range(5, len(tdf) - 5):
        if tdf['hammer'].iloc[i] and tdf['close'].iloc[i-1] > tdf['close'].iloc[i-4]:
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('19: Hammer Pattern', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('19: Hammer Pattern', len(trades), 0, 0, '❌'))

# HYPOTHESIS 20: Volume Climax
# Volume > 3x average + large price move
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['price_change'] = tdf['close'].pct_change()
    
    for i in range(25, len(tdf) - 10):
        if (tdf['volume'].iloc[i] > tdf['vol_avg'].iloc[i] * 3 and 
            abs(tdf['price_change'].iloc[i]) > 0.05):
            # Fade the move
            direction = 1 if tdf['price_change'].iloc[i] < 0 else -1
            exit_price = tdf['close'].iloc[i + 5]
            entry_price = tdf['close'].iloc[i]
            ret = ((exit_price - entry_price) / entry_price * 100 * direction) - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('20: Volume Climax Fade', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('20: Volume Climax Fade', len(trades), 0, 0, '❌'))

# HYPOTHESIS 21: 3-Day Momentum Reversal
# 3 consecutive down days + volume spike
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    
    for i in range(5, len(tdf) - 5):
        if (tdf['return'].iloc[i] < 0 and 
            tdf['return'].iloc[i-1] < 0 and 
            tdf['return'].iloc[i-2] < 0 and
            tdf['vol_ratio'].iloc[i] > 1.5):
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('21: 3-Day + Volume', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('21: 3-Day + Volume', len(trades), 0, 0, '❌'))

# HYPOTHESIS 22: Inside Day Breakout
# Inside day followed by breakout
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    tdf['inside_day'] = (tdf['high'] < tdf['prev_high']) & (tdf['low'] > tdf['prev_low'])
    
    for i in range(5, len(tdf) - 5):
        if tdf['inside_day'].iloc[i-1] and tdf['close'].iloc[i] > tdf['prev_high'].iloc[i]:
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('22: Inside Day Breakout', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('22: Inside Day Breakout', len(trades), 0, 0, '❌'))

# HYPOTHESIS 23: Bollinger Band Squeeze
# Bands narrow then expand
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['ma20'] = tdf['close'].rolling(20).mean()
    tdf['std20'] = tdf['close'].rolling(20).std()
    tdf['upper'] = tdf['ma20'] + 2 * tdf['std20']
    tdf['lower'] = tdf['ma20'] - 2 * tdf['std20']
    tdf['band_width'] = (tdf['upper'] - tdf['lower']) / tdf['ma20']
    tdf['band_avg'] = tdf['band_width'].rolling(20).mean()
    
    for i in range(50, len(tdf) - 5):
        if (tdf['band_width'].iloc[i-1] < tdf['band_avg'].iloc[i-1] * 0.8 and  # Squeeze
            tdf['close'].iloc[i] > tdf['upper'].iloc[i]):  # Breakout
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('23: BB Squeeze Breakout', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('23: BB Squeeze Breakout', len(trades), 0, 0, '❌'))

# HYPOTHESIS 24: Range Expansion
# Today's range > 1.5x ATR
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['prev_close'] = tdf['close'].shift(1)
    tdf['tr'] = tdf[['high', 'low', 'prev_close']].apply(
        lambda x: max(x['high'] - x['low'], abs(x['high'] - x['prev_close']), 
                      abs(x['low'] - x['prev_close'])), axis=1)
    tdf['atr14'] = tdf['tr'].rolling(14).mean()
    
    for i in range(20, len(tdf) - 5):
        if tdf['range'].iloc[i] > tdf['atr14'].iloc[i] * 1.5 and tdf['close'].iloc[i] > tdf['open'].iloc[i]:
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('24: Range Expansion', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('24: Range Expansion', len(trades), 0, 0, '❌'))

# HYPOTHESIS 25: RSI Divergence
# Price makes lower low, RSI makes higher low
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['rsi'] = calculate_rsi(tdf['close'])
    
    for i in range(20, len(tdf) - 5):
        if i < 5:
            continue
        # Bullish divergence: price lower low, RSI higher low
        price_ll = tdf['close'].iloc[i] < tdf['close'].iloc[i-5:i].min()
        rsi_hl = tdf['rsi'].iloc[i] > tdf['rsi'].iloc[i-5:i].min()
        
        if price_ll and rsi_hl and tdf['rsi'].iloc[i] < 40:
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('25: RSI Divergence', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('25: RSI Divergence', len(trades), 0, 0, '❌'))

# HYPOTHESIS 26: VWAP Deviation
# Price below VWAP, revert to VWAP
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['typical'] = (tdf['high'] + tdf['low'] + tdf['close']) / 3
    tdf['vwap_num'] = (tdf['typical'] * tdf['volume']).rolling(20).sum()
    tdf['vwap_den'] = tdf['volume'].rolling(20).sum()
    tdf['vwap'] = tdf['vwap_num'] / tdf['vwap_den']
    tdf['deviation'] = (tdf['close'] - tdf['vwap']) / tdf['vwap']
    
    for i in range(25, len(tdf) - 5):
        if tdf['deviation'].iloc[i] < -0.03:  # 3% below VWAP
            ret = (tdf['close'].iloc[i+5] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('26: VWAP Deviation', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('26: VWAP Deviation', len(trades), 0, 0, '❌'))

# HYPOTHESIS 27: Opening Range Breakout
# Break above first 30-min high
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    
    for i in range(5, len(tdf) - 5):
        if tdf['close'].iloc[i] > tdf['prev_high'].iloc[i] * 1.01:  # Break above prev day high
            ret = (tdf['close'].iloc[i+3] - tdf['close'].iloc[i]) / tdf['close'].iloc[i] * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    results.append(('27: Prev High Breakout', len(trades), wr, sh, '✅' if wr >= 55 and sh > 0.5 else '❌'))
else:
    results.append(('27: Prev High Breakout', len(trades), 0, 0, '❌'))

# Print summary
print("\n📊 BATCH RESULTS:")
print("-"*60)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

for name, trades, wr, sharpe, status in results:
    if trades >= 30:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sharpe:<10.2f}")
    else:
        print(f"{status} {name:<23} {trades:<10} {'N/A':<10} {'N/A':<10}")

validated = sum(1 for r in results if r[4] == '✅')
print("-"*60)
print(f"\nSUMMARY: {validated}/10 hypotheses validated")
print("="*70)
