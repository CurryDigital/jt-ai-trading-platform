#!/usr/bin/env python3
"""
BATCH TEST 7: Bitcoin/Crypto Hypotheses
Testing BTC-specific strategies
Note: MSTR not available in database, using BTC-USD and crypto proxies
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
print("BATCH TEST 7: Bitcoin/Crypto Hypotheses")
print("Note: MSTR not in DB. Testing BTC-USD standalone strategies.")
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

# Get BTC and ETH data
query = """
SELECT date, ticker, open, high, low, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('BTC-USD', 'ETH-USD') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {df['ticker'].nunique()} cryptos, {len(df)} records")
print(f"BTC records: {len(df[df['ticker']=='BTC-USD'])}")
print(f"ETH records: {len(df[df['ticker']=='ETH-USD'])}\n")

# Calculate indicators for BTC/ETH
def calculate_indicators(tdf):
    tdf = tdf.copy()
    tdf['return'] = tdf['close'].pct_change()
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['atr'] = tdf['range'].rolling(14).mean()
    
    # RSI
    delta = tdf['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    tdf['rsi'] = 100 - (100 / (1 + rs))
    
    # 24h change (crypto is 24/7)
    tdf['change_1d'] = tdf['close'].pct_change(1)
    tdf['change_3d'] = tdf['close'].pct_change(3)
    tdf['change_7d'] = tdf['close'].pct_change(7)
    
    return tdf

all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf = calculate_indicators(tdf)
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna()

results = []

# H49: BTC Extreme RSI Mean Reversion
print("="*70)
print("H49: BTC Extreme RSI Mean Reversion")
print("BTC RSI < 20 (extreme oversold), hold 7 days")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 7):
        if tdf['rsi'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999  # Weekly
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('49: BTC RSI<20', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('49: BTC RSI<20', len(trades), 0, 0, '❌'))

# H50: BTC Volume Spike Breakout
print("\n" + "="*70)
print("H50: BTC Volume Spike Breakout")
print("Volume > 3x average + Price up > 5% (crypto is more volatile)")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 7):
        if tdf['vol_ratio'].iloc[i] > 3.0 and tdf['return'].iloc[i] > 0.05:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('50: BTC Vol>3x', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('50: BTC Vol>3x', len(trades), 0, 0, '❌'))

# H51: BTC 3-Day Drop Bounce
print("\n" + "="*70)
print("H51: BTC 3-Day Drop Bounce")
print("3 consecutive down days > -5% each, then buy")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(10, len(tdf) - 7):
        if (tdf['return'].iloc[i] < -0.05 and 
            tdf['return'].iloc[i-1] < -0.05 and 
            tdf['return'].iloc[i-2] < -0.05):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('51: BTC 3DayDrop', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('51: BTC 3DayDrop', len(trades), 0, 0, '❌'))

# H52: ETH-BTC Ratio Trade
print("\n" + "="*70)
print("H52: ETH-BTC Ratio Mean Reversion")
print("When ETH/BTC ratio at 30-day low, buy ETH")
print("="*70)
trades = []
btc_df = df[df['ticker'] == 'BTC-USD'].sort_values('date').set_index('date')
eth_df = df[df['ticker'] == 'ETH-USD'].sort_values('date').set_index('date')

# Align dates
common_dates = btc_df.index.intersection(eth_df.index)
if len(common_dates) > 50:
    ratio = eth_df.loc[common_dates, 'close'] / btc_df.loc[common_dates, 'close']
    ratio_avg = ratio.rolling(30).mean()
    
    for i in range(30, len(ratio) - 7):
        if ratio.iloc[i] < ratio_avg.iloc[i] * 0.95:  # 5% below 30d avg
            entry = eth_df.loc[ratio.index[i], 'close']
            exit_price = eth_df.loc[ratio.index[i + 7], 'close']
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('52: ETH/BTC Ratio', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('52: ETH/BTC Ratio', len(trades), 0, 0, '❌'))

# H53: BTC ATR Expansion
print("\n" + "="*70)
print("H53: BTC ATR Expansion Breakout")
print("ATR > 2x average + Volume > 2x + Green candle")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_avg'] = tdf['atr'].rolling(20).mean()
    for i in range(25, len(tdf) - 7):
        if (tdf['atr'].iloc[i] > tdf['atr_avg'].iloc[i] * 2 and
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['close'].iloc[i] > tdf['open'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('53: BTC ATR Exp', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('53: BTC ATR Exp', len(trades), 0, 0, '❌'))

# H54: BTC Weekend Effect (if data has day of week)
print("\n" + "="*70)
print("H54: BTC Day-of-Week Pattern")
print("Buy on Sunday (if available), sell Friday - crypto 24/7")
print("Note: Skipping - need to check if day-of-week matters")
print("="*70)
print("⏭️ SKIP - Day-of-week analysis requires specific date parsing")
results.append(('54: BTC Weekend', 0, 0, 0, 'SKIP'))

# H55: BTC Volatility Contraction
print("\n" + "="*70)
print("H55: BTC Volatility Contraction + Expansion")
print("ATR at 20-day low, then volume spike")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['atr_low_20'] = tdf['atr'].rolling(20).min()
    for i in range(25, len(tdf) - 7):
        contraction = tdf['atr'].iloc[i-1] <= tdf['atr_low_20'].iloc[i-1] * 1.1
        expansion = tdf['vol_ratio'].iloc[i] > 2.5
        if contraction and expansion:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('55: BTC VolContract', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('55: BTC VolContract', len(trades), 0, 0, '❌'))

# H56: Crypto Momentum (BTC leads, ETH follows)
print("\n" + "="*70)
print("H56: BTC-ETH Momentum Lead-Lag")
print("BTC up >5% yesterday, buy ETH today (momentum spillover)")
print("="*70)
trades = []
if len(common_dates) > 50:
    for i in range(5, len(common_dates) - 1):
        btc_yesterday = btc_df.loc[common_dates[i-1], 'return']
        if btc_yesterday > 0.05:  # BTC up >5%
            entry = eth_df.loc[common_dates[i], 'close']
            exit_price = eth_df.loc[common_dates[i + 1], 'close']
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('56: BTC-ETH Lead', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('56: BTC-ETH Lead', len(trades), 0, 0, '❌'))

# H57: BTC Dip Buying (10% drop)
print("\n" + "="*70)
print("H57: BTC Dip Buying (-10% daily drop)")
print("Buy after -10% day, hold 7 days")
print("="*70)
trades = []
for ticker in ['BTC-USD']:
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(5, len(tdf) - 7):
        if tdf['return'].iloc[i] < -0.10:  # -10% day
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 7]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('57: BTC -10% Dip', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('57: BTC -10% Dip', len(trades), 0, 0, '❌'))

# H58: BTC + ETH Combined Volume Spike
print("\n" + "="*70)
print("H58: Combined Crypto Volume Spike")
print("BTC and ETH both have volume > 2.5x average same day")
print("Note: Requires checking both on same day")
print("="*70)
trades = []
if len(common_dates) > 50:
    btc_vol_ratio = btc_df['vol_ratio']
    eth_vol_ratio = eth_df['vol_ratio']
    
    for i in range(25, len(common_dates) - 7):
        if btc_vol_ratio.iloc[i] > 2.5 and eth_vol_ratio.iloc[i] > 2.5:
            entry = btc_df.loc[common_dates[i], 'close']
            exit_price = btc_df.loc[common_dates[i + 7], 'close']
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 10:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else -999
    status = "✅" if wr >= 55 and sh > 0.5 else "🧪" if wr >= 52 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('58: Combined Vol', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('58: Combined Vol', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 7: BTC/Crypto Summary")
print("="*70)
print(f"{'Hypothesis':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

validated = 0
tested = 0
skipped = 0

for name, trades, wr, sh, status in results:
    if status == 'SKIP':
        print(f"⏭️  {name:<23} {'N/A':<10} {'N/A':<10} {'N/A':<10} SKIP")
        skipped += 1
    elif trades >= 10:
        print(f"{status} {name:<23} {trades:<10} {wr:<10.1f} {sh:<10.2f}")
        tested += 1
        if status == '✅':
            validated += 1
    else:
        print(f"{status} {name:<23} {trades:<10} N/A       N/A")
        tested += 1

print("-"*70)
print(f"Tested: {tested}, Validated: {validated}, Skipped: {skipped}")
print(f"Total Hypotheses: 48 + {tested} = {48 + tested}")
print("="*70)
print()
print("Note: MSTR not available in database.")
print("Request JT to add: MSTR, COIN, MARA, RIOT for whale proxy testing.")
