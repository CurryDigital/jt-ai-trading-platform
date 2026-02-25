#!/usr/bin/env python3
"""
ENHANCE BB EXTREME + MONDAY TO GOLDEN STATUS (66.0% → 70%+)
Testing variations to push win rate to 70%+
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
print("ENHANCING: BB Extreme + Monday to Golden Status")
print("Target: 66.0% → 70%+ (need +4% improvement)")
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
       ti.rsi_14, ti.vol_ratio, ti.bb_lower, ti.bb_upper, ti.bb_middle
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
df['dayofweek'] = df['date'].dt.dayofweek
df['is_monday'] = df['dayofweek'] == 0

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# BASELINE: Original BB Extreme + Monday (66.0%)
print("="*70)
print("BASELINE: BB Extreme + Monday (Original)")
print("Config: Price < BB lower + RSI < 25 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f}")
results.append(('Baseline (RSI<25)', len(trades), wr, sh))

# ENHANCEMENT 1: Tighter RSI (RSI < 20)
print("\n" + "="*70)
print("ENHANCEMENT 1: Tighter RSI Threshold")
print("Config: Price < BB lower + RSI < 20 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 20 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 1: RSI<20', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 1: RSI<20', len(trades), 0, 0))

# ENHANCEMENT 2: Add Volume Filter (Vol > 1.5x)
print("\n" + "="*70)
print("ENHANCEMENT 2: Add Volume Filter >1.5x")
print("Config: Price < BB lower + RSI < 25 + Vol >1.5x + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['vol_ratio'].iloc[i] > 1.5 and
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 2: +Vol>1.5x', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 2: +Vol>1.5x', len(trades), 0, 0))

# ENHANCEMENT 3: Tighter RSI + Volume (RSI < 20 + Vol > 1.5x)
print("\n" + "="*70)
print("ENHANCEMENT 3: RSI<20 + Volume >1.5x")
print("Config: Price < BB lower + RSI < 20 + Vol >1.5x + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 20 and 
            tdf['vol_ratio'].iloc[i] > 1.5 and
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 3: RSI<20+Vol>1.5', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 3: RSI<20+Vol>1.5', len(trades), 0, 0))

# ENHANCEMENT 4: Even Tighter RSI (RSI < 15)
print("\n" + "="*70)
print("ENHANCEMENT 4: Ultra Tight RSI < 15")
print("Config: Price < BB lower + RSI < 15 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 15 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 4: RSI<15', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 4: RSI<15', len(trades), 0, 0))

# ENHANCEMENT 5: Deeper BB (Price < BB lower - 1%)
print("\n" + "="*70)
print("ENHANCEMENT 5: Deeper Below BB")
print("Config: Price < BB lower * 0.99 + RSI < 25 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] * 0.99 and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 5: BB-1%', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 5: BB-1%', len(trades), 0, 0))

# ENHANCEMENT 6: Shorter Hold (5 days vs 10 days)
print("\n" + "="*70)
print("ENHANCEMENT 6: Shorter Hold Period (5 days)")
print("Config: Price < BB lower + RSI < 25 + Monday, hold 5 days")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]  # 5 days instead of 10
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 6: 5-day hold', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 6: 5-day hold', len(trades), 0, 0))

# ENHANCEMENT 7: RSI < 20 + 5-day hold
print("\n" + "="*70)
print("ENHANCEMENT 7: RSI<20 + 5-day Hold")
print("Config: Price < BB lower + RSI < 20 + Monday, hold 5 days")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 20 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 7: RSI<20+5day', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 7: RSI<20+5day', len(trades), 0, 0))

# ENHANCEMENT 8: BB %B < -0.1 (extreme)
print("\n" + "="*70)
print("ENHANCEMENT 8: Extreme BB %B < -0.1")
print("Config: %B < -0.1 + RSI < 25 + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        bb_b = (tdf['close'].iloc[i] - tdf['bb_lower'].iloc[i]) / (tdf['bb_upper'].iloc[i] - tdf['bb_lower'].iloc[i]) if (tdf['bb_upper'].iloc[i] - tdf['bb_lower'].iloc[i]) > 0 else 0.5
        if (bb_b < -0.1 and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 8: %B<-0.1', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 8: %B<-0.1', len(trades), 0, 0))

# ENHANCEMENT 9: All Combined (RSI<20 + Vol>1.5x + 5-day hold)
print("\n" + "="*70)
print("ENHANCEMENT 9: ALL FILTERS (RSI<20 + Vol>1.5x + 5-day)")
print("Config: Price < BB lower + RSI < 20 + Vol >1.5x + Monday, hold 5 days")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 20 and 
            tdf['vol_ratio'].iloc[i] > 1.5 and
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 9: ALL COMBINED', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 9: ALL COMBINED', len(trades), 0, 0))

# ENHANCEMENT 10: Volume > 2.0x (stronger confirmation)
print("\n" + "="*70)
print("ENHANCEMENT 10: Strong Volume > 2.0x")
print("Config: Price < BB lower + RSI < 25 + Vol >2.0x + Monday")
print("="*70)
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 25 and 
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 20:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE!" if wr >= 67 else ""
    print(f"Trades: {len(trades)}, Win%: {wr:.1f}, Sharpe: {sh:.2f} {status}")
    results.append(('Enh 10: Vol>2.0x', len(trades), wr, sh))
else:
    print(f"Trades: {len(trades)} - Insufficient")
    results.append(('Enh 10: Vol>2.0x', len(trades), 0, 0))

# Summary
print("\n" + "="*70)
print("ENHANCEMENT SUMMARY - BB EXTREME + MONDAY")
print("="*70)
print(f"{'Enhancement':<25} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

best_wr = 0
best_config = ""

for name, trades, wr, sh in results:
    if trades >= 20:
        status = "✅ GOLDEN!" if wr >= 70 else "🧪 CLOSE" if wr >= 67 else ""
        print(f"{name:<25} {trades:<10} {wr:<10.1f} {sh:<10.2f} {status}")
        if wr > best_wr:
            best_wr = wr
            best_config = name
    else:
        print(f"{name:<25} {trades:<10} N/A       N/A")

print("-"*70)
print(f"\n🏆 BEST CONFIGURATION: {best_config}")
print(f"🎯 Win Rate: {best_wr:.1f}%")

if best_wr >= 70:
    print("\n🎉🎉🎉 GOLDEN STATUS ACHIEVED! 🎉🎉🎉")
elif best_wr >= 67:
    print("\n🧪 Close to Golden! Need just {:.1f}% more".format(70 - best_wr))
else:
    print("\n📊 Need {:.1f}% more to reach Golden status".format(70 - best_wr))
print("="*70)
