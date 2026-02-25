#!/usr/bin/env python3
"""
TEST UNLOCKED STRATEGIES - SPY + Crypto Data Now Available!
Testing 9+ previously blocked strategies
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
print("TESTING UNLOCKED STRATEGIES - SPY + CRYPTO DATA AVAILABLE!")
print("Previously blocked - now testing with new data")
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

# Get SPY data
print("\n=== Loading SPY Data ===")
cursor = conn.cursor()
cursor.execute("""
SELECT date, ticker, open, high, low, close, volume
FROM silver.unified_prices
WHERE ticker = 'SPY' AND date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY date
""")
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
spy_df['spy_sma50'] = spy_df['close'].rolling(50).mean()
spy_df['spy_sma200'] = spy_df['close'].rolling(200).mean()
spy_df['spy_trend'] = np.where(spy_df['close'] > spy_df['spy_sma50'], 'up', 'down')
spy_df['spy_return'] = spy_df['close'].pct_change()
print(f"SPY data: {len(spy_df)} records")

# Get stock data
print("\n=== Loading Stock Data ===")
cursor.execute('''
SELECT DISTINCT ticker FROM gold.technical_indicators_calculated 
WHERE ticker IN (SELECT DISTINCT ticker FROM silver.unified_prices)
ORDER BY ticker LIMIT 80
''')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

# Get data from unified_prices for stocks
ticker_list = "','".join(tickers[:50])
query = f"""
SELECT t.date, t.ticker, t.close, t.volume,
       ti.rsi_14, ti.vol_ratio, ti.bb_lower, ti.bb_upper
FROM silver.unified_prices t
LEFT JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') 
  AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

# Merge with SPY data
spy_df = spy_df.rename(columns={'close': 'spy_close'})
df = df.merge(spy_df[['date', 'spy_close', 'spy_sma50', 'spy_sma200', 'spy_trend', 'spy_return']], 
              on='date', how='left')

print(f"Stock data: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# ============================================
# PART 1: SPY MARKET REGIME STRATEGIES
# ============================================

print("="*70)
print("PART 1: SPY MARKET REGIME STRATEGIES")
print("="*70)

# H89: RSI Mean Reversion in SPY Uptrend
print("\n--- H89: RSI <20 + SPY Uptrend ---")
trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if tdf['rsi_14'].iloc[i] < 20 and tdf['spy_trend'].iloc[i] == 'up':
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H89: RSI+SPY Up', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H89: RSI+SPY Up', len(trades), 0, 0, '❌'))

# H90: RSI Mean Reversion in SPY Downtrend (contrarian)
print("\n--- H90: RSI <15 + SPY Downtrend ---")
trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
            if tdf['rsi_14'].iloc[i] < 15 and tdf['spy_trend'].iloc[i] == 'down':
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H90: RSI+SPY Down', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H90: RSI+SPY Down', len(trades), 0, 0, '❌'))

# H91: Volume Breakout in SPY Uptrend
print("\n--- H91: Volume Breakout + SPY Uptrend ---")
trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 5):
        if pd.notna(tdf['vol_ratio'].iloc[i]) and pd.notna(tdf['spy_trend'].iloc[i]):
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
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H91: VolBO+SPY Up', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H91: VolBO+SPY Up', len(trades), 0, 0, '❌'))

# H92: RSI + SPY Golden Cross
print("\n--- H92: RSI <20 + SPY > 200-day SMA ---")
trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(200, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_sma200'].iloc[i]):
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
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H92: RSI+GoldenCross', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H92: RSI+GoldenCross', len(trades), 0, 0, '❌'))

# H93: High Volume + SPY Volume Confirmation
print("\n--- H93: Volume Breakout + SPY Volume >1.5x ---")
spy_df['spy_vol_avg'] = spy_df['volume'].rolling(20).mean()
spy_df['spy_vol_ratio'] = spy_df['volume'] / spy_df['spy_vol_avg']
df = df.merge(spy_df[['date', 'spy_vol_ratio']], on='date', how='left')

trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if pd.notna(tdf['vol_ratio'].iloc[i]) and pd.notna(tdf['spy_vol_ratio'].iloc[i]):
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
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H93: Vol+SPY Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H93: Vol+SPY Vol', len(trades), 0, 0, '❌'))

# H94: RSI Extreme + SPY Pullback
print("\n--- H94: RSI <15 + SPY down >2% ---")
trades = []
for ticker in df['ticker'].dropna().unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if pd.notna(tdf['rsi_14'].iloc[i]) and pd.notna(tdf['spy_return'].iloc[i]):
            if tdf['rsi_14'].iloc[i] < 15 and tdf['spy_return'].iloc[i] < -0.02:
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('H94: RSI+SPY Drop', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('H94: RSI+SPY Drop', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("SPY MARKET REGIME RESULTS")
print("="*70)
print(f"{'Strategy':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

validated = 0
for name, trades, wr, sh, status in results:
    if trades >= 30:
        print(f"{name:<25} {trades:<10} {wr:<10.1f} {sh:<10.2f} {status}")
        if status == '✅':
            validated += 1
    else:
        print(f"{name:<25} {trades:<10} N/A       N/A       {status}")

print("-"*70)
print(f"Validated: {validated}/{len(results)}")
print("="*70)

if validated > 0:
    print(f"\n🎉 {validated} SPY strategies validated!")
else:
    print("\n📊 No SPY strategies validated this test.")
