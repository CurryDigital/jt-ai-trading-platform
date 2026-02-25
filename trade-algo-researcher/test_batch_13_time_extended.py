#!/usr/bin/env python3
"""
BATCH TEST 13: Extended Time-Based Patterns
Exploring day-of-week, month-effects, quarterly patterns
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
print("BATCH TEST 13: Extended Time-Based Patterns")
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
cursor.execute('SELECT DISTINCT ticker FROM gold.technical_indicators_calculated ORDER BY ticker LIMIT 100')
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
query = f"""
SELECT t.date, t.ticker, t.close, t.volume,
       ti.rsi_14, ti.vol_ratio, ti.bb_lower
FROM silver.historical_stock_data t
INNER JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

# Add time features
df['date'] = pd.to_datetime(df['date'])
df['dayofweek'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
df['day'] = df['date'].dt.day
df['month'] = df['date'].dt.month
df['is_month_start'] = df['day'] <= 3
df['is_month_end'] = df['day'] >= 26
df['is_quarter_end'] = (df['month'].isin([3, 6, 9, 12])) & (df['day'] >= 25)
df['is_quarter_start'] = (df['month'].isin([1, 4, 7, 10])) & (df['day'] <= 5)
df['is_friday'] = df['dayofweek'] == 4

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# H109: Tuesday RSI Extreme
print("="*70)
print("H109: Tuesday RSI Extreme")
print("RSI < 20 on Tuesdays")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20 and tdf['dayofweek'].iloc[i] == 1:
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
    results.append(('109: Tue RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('109: Tue RSI', len(trades), 0, 0, '❌'))

# H110: Wednesday RSI Extreme
print("\n" + "="*70)
print("H110: Wednesday RSI Extreme")
print("RSI < 20 on Wednesdays")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20 and tdf['dayofweek'].iloc[i] == 2:
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
    results.append(('110: Wed RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('110: Wed RSI', len(trades), 0, 0, '❌'))

# H111: Turn of Month (Last 2 days + First 2 days)
print("\n" + "="*70)
print("H111: Turn of Month RSI Extreme")
print("RSI < 20 in last 2 days OR first 2 days of month")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        turn_of_month = tdf['day'].iloc[i] <= 2 or tdf['day'].iloc[i] >= 29
        if tdf['rsi_14'].iloc[i] < 20 and turn_of_month:
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
    results.append(('111: TurnMonth RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('111: TurnMonth RSI', len(trades), 0, 0, '❌'))

# H112: Quarter-End RSI Extreme
print("\n" + "="*70)
print("H112: Quarter-End RSI Extreme")
print("RSI < 20 in last 5 days of quarter (Mar, Jun, Sep, Dec)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20 and tdf['is_quarter_end'].iloc[i]:
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
    results.append(('112: QuarterEnd RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('112: QuarterEnd RSI', len(trades), 0, 0, '❌'))

# H113: Quarter-Start RSI Extreme
print("\n" + "="*70)
print("H113: Quarter-Start RSI Extreme")
print("RSI < 20 in first 5 days of quarter (Jan, Apr, Jul, Oct)")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20 and tdf['is_quarter_start'].iloc[i]:
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
    results.append(('113: QuarterStart RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('113: QuarterStart RSI', len(trades), 0, 0, '❌'))

# H114: Friday Volume Breakout
print("\n" + "="*70)
print("H114: Friday Volume Breakout")
print("Vol >2x + Price >4% on Friday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 5):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04 and
            tdf['dayofweek'].iloc[i] == 4):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('114: Friday VolBO', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('114: Friday VolBO', len(trades), 0, 0, '❌'))

# H115: Monday Volume Breakout
print("\n" + "="*70)
print("H115: Monday Volume Breakout")
print("Vol >2x + Price >4% on Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 5):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04 and
            tdf['dayofweek'].iloc[i] == 0):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('115: Monday VolBO', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('115: Monday VolBO', len(trades), 0, 0, '❌'))

# H116: Month-End Volume Breakout
print("\n" + "="*70)
print("H116: Month-End Volume Breakout")
print("Vol >2x + Price >4% in last 5 days of month")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 5):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04 and
            tdf['is_month_end'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅" if wr >= 55 else "❌"
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
    print(f"Status: {status}")
    results.append(('116: MonthEnd VolBO', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('116: MonthEnd VolBO', len(trades), 0, 0, '❌'))

# H117: BB Extreme + Monday
print("\n" + "="*70)
print("H117: BB Extreme + Monday")
print("Price < BB lower + RSI < 25 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['dayofweek'].iloc[i] == 0):
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
    results.append(('117: BB+Mon RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('117: BB+Mon RSI', len(trades), 0, 0, '❌'))

# H118: BB Extreme + Month-End
print("\n" + "="*70)
print("H118: BB Extreme + Month-End")
print("Price < BB lower + RSI < 25 + Last 5 days of month")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['is_month_end'].iloc[i]):
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
    results.append(('118: BB+MonthEnd RSI', len(trades), wr, sh, status))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('118: BB+MonthEnd RSI', len(trades), 0, 0, '❌'))

# Summary
print("\n" + "="*70)
print("BATCH 13: TIME-BASED PATTERNS SUMMARY")
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
print(f"Total Hypotheses: 107 + {tested} = {107 + tested}")
print("="*70)

if validated > 0:
    print("\n🎉 NEW TIME-BASED PATTERNS FOUND!")
else:
    print("\n📊 No new time-based patterns this batch.")
