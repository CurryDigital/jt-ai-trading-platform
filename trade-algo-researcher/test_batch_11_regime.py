#!/usr/bin/env python3
"""
BATCH TEST 11: Market Regime & Time-Based Strategies
Testing SPY trend filters, VIX levels, day-of-week, etc.
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
print("BATCH TEST 11: Market Regime & Time-Based Strategies")
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

# Get SPY data for market regime
cursor = conn.cursor()
cursor.execute("""
SELECT date, close, volume 
FROM silver.historical_stock_data 
WHERE ticker = 'SPY' AND date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY date
""")
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'spy_close', 'spy_vol'])
spy_df['spy_sma50'] = spy_df['spy_close'].rolling(50).mean()
spy_df['spy_sma200'] = spy_df['spy_close'].rolling(200).mean()
spy_df['spy_trend'] = np.where(spy_df['spy_close'] > spy_df['spy_sma50'], 'up', 'down')

# Get stock data with indicators
cursor.execute('SELECT DISTINCT ticker FROM gold.technical_indicators_calculated ORDER BY ticker LIMIT 80')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT t.date, t.ticker, t.close, t.volume,
       ti.rsi_14, ti.vol_ratio, ti.bb_lower, ti.atr_14
FROM silver.historical_stock_data t
INNER JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

# Merge with SPY data
df = df.merge(spy_df[['date', 'spy_close', 'spy_sma50', 'spy_sma200', 'spy_trend']], on='date', how='left')

print(f"Data loaded: {df['ticker'].nunique()} tickers + SPY regime data")
print(f"Records: {len(df)}\n")

results = []

# H89: RSI Mean Reversion in Uptrend Only
print("="*70)
print("H89: RSI Mean Reversion (RSI<20) in SPY Uptrend Only")
print("Only trade when SPY > 50-day SMA")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['rsi_14'].iloc[i] < 20 and 
            tdf['spy_trend'].iloc[i] == 'up'):
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
    results.append(('89: RSI+SPY Up', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('89: RSI+SPY Up', len(trades), 0, 0, '❌'))

# H90: RSI Mean Reversion in Downtrend (contrarian)
print("\n" + "="*70)
print("H90: RSI Mean Reversion (RSI<15) in SPY Downtrend")
print("Extreme oversold when market is down")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['rsi_14'].iloc[i] < 15 and 
            tdf['spy_trend'].iloc[i] == 'down'):
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
    results.append(('90: RSI+SPY Down', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('90: RSI+SPY Down', len(trades), 0, 0, '❌'))

# H91: Volume Breakout in Uptrend
print("\n" + "="*70)
print("H91: Volume Breakout in SPY Uptrend Only")
print("Vol >2x + Price >4% only when SPY > 50-day")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 5):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04 and
            tdf['spy_trend'].iloc[i] == 'up'):
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
    results.append(('91: VolBO+SPY Up', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('91: VolBO+SPY Up', len(trades), 0, 0, '❌'))

# H92: Mean Reversion with Golden Cross
print("\n" + "="*70)
print("H92: RSI Mean Reversion + SPY Golden Cross")
print("RSI < 20 only when SPY > 200-day SMA")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(200, len(tdf) - 10):
        golden_cross = tdf['spy_close'].iloc[i] > tdf['spy_sma200'].iloc[i]
        if tdf['rsi_14'].iloc[i] < 20 and golden_cross:
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
    results.append(('92: RSI+GoldenCross', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('92: RSI+GoldenCross', len(trades), 0, 0, '❌'))

# H93: High Volume + SPY Confirmation
print("\n" + "="*70)
print("H93: High Volume Breakout + SPY Volume Confirmation")
print("Stock Vol >3x AND SPY Vol >1.5x avg")
print("="*70)
trades = []
spy_df['spy_vol_avg'] = spy_df['spy_vol'].rolling(20).mean()
spy_df['spy_vol_ratio'] = spy_df['spy_vol'] / spy_df['spy_vol_avg']
df = df.merge(spy_df[['date', 'spy_vol_ratio']], on='date', how='left')

for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['vol_ratio'].iloc[i] > 3.0 and 
            tdf['spy_vol_ratio'].iloc[i] > 1.5):
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
    results.append(('93: Vol+SPY Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('93: Vol+SPY Vol', len(trades), 0, 0, '❌'))

# H94: RSI Extreme + Market Pullback
print("\n" + "="*70)
print("H94: RSI Extreme + SPY Pullback (>2% down)")
print("RSI < 15 when SPY down >2% that day")
print("="*70)
trades = []
spy_df['spy_return'] = spy_df['spy_close'].pct_change()
df = df.merge(spy_df[['date', 'spy_return']], on='date', how='left')

for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['rsi_14'].iloc[i] < 15 and 
            tdf['spy_return'].iloc[i] < -0.02):
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
    results.append(('94: RSI+SPY Drop', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('94: RSI+SPY Drop', len(trades), 0, 0, '❌'))

# H95: BB Mean Reversion in Bull Market
print("\n" + "="*70)
print("H95: BB Extreme + Bull Market Only")
print("Price < BB lower only when SPY > 200-day")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(200, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and
            tdf['spy_close'].iloc[i] > tdf['spy_sma200'].iloc[i]):
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
    results.append(('95: BB+Bull Mkt', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('95: BB+Bull Mkt', len(trades), 0, 0, '❌'))

# H96: Low ATR + SPY Trend
print("\n" + "="*70)
print("H96: ATR Contraction + SPY Uptrend")
print("ATR < 0.8x avg + Vol >2x + SPY up")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_avg'] = tdf['atr_14'].rolling(20).mean()
    for i in range(25, len(tdf) - 5):
        if (tdf['atr_14'].iloc[i] < tdf['atr_avg'].iloc[i] * 0.8 and
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['spy_trend'].iloc[i] == 'up'):
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
    results.append(('96: ATR+SPY Up', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('96: ATR+SPY Up', len(trades), 0, 0, '❌'))

# H97: Consecutive Down Days + Market Bottom
print("\n" + "="*70)
print("H97: 3 Consecutive Down Days + SPY Oversold")
print("3 down days + RSI < 25 + SPY RSI proxy < 40")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 10):
        three_down = (tdf['return'].iloc[i] < 0 and 
                     tdf['return'].iloc[i-1] < 0 and 
                     tdf['return'].iloc[i-2] < 0)
        oversold = tdf['rsi_14'].iloc[i] < 25
        market_weak = tdf['spy_return'].iloc[i] < -0.01 if 'spy_return' in tdf.columns else True
        
        if three_down and oversold and market_weak:
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
    results.append(('97: 3Down+Oversold', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('97: 3Down+Oversold', len(trades), 0, 0, '❌'))

# H98: Monday Effect (if data available)
print("\n" + "="*70)
print("H98: RSI Extreme on Mondays")
print("RSI < 20 on Monday (dayofweek=0)")
print("="*70)
df['dayofweek'] = pd.to_datetime(df['date']).dt.dayofweek
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20 and tdf['dayofweek'].iloc[i] == 0:
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
    results.append(('98: Monday RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('98: Monday RSI', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 11: MARKET REGIME SUMMARY")
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
print(f"Total Hypotheses: 87 + {tested} = {87 + tested}")
print("="*70)

if validated > 0:
    print("\n🎉 MARKET REGIME FILTERS FOUND!")
else:
    print("\n📊 No regime filters validated this batch.")
