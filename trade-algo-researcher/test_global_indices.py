#!/usr/bin/env python3
"""
TEST: Golden Strategies on Global Indices
Universe: S&P 500, Dow, Nasdaq, Russell, VIX, HSI, Nikkei, FTSE, DAX, CAC
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
print("TEST: Golden Strategies on GLOBAL INDICES")
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

# Global indices
indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^HSI', '^N225', '^FTSE', '^GDAXI', '^FCHI']
indices_str = "','".join(indices)

query = f"""
SELECT date, ticker, open, high, low, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('{indices_str}') AND date BETWEEN '2020-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Indices: {df['ticker'].nunique()}")
print(f"Records: {len(df)}\n")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    tdf['rsi'] = calculate_rsi(tdf['close'])
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    tdf['return'] = tdf['close'].pct_change()
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    tdf['inside_day'] = (tdf['high'] < tdf['prev_high']) & (tdf['low'] > tdf['prev_low'])
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi'])

print("="*70)
print("STRATEGY 1: Volume Breakout on INDICES")
print("="*70)
print(f"{'Index':<15} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

results_vb = []
for idx in df['ticker'].unique():
    tdf = df[df['ticker'] == idx].sort_values('date')
    trades = []
    
    for i in range(25, len(tdf) - 10):
        if (tdf['vol_ratio'].iloc[i] > 2.0 and 
            tdf['return'].iloc[i] > 0.04):
            
            entry = tdf['close'].iloc[i]
            target = entry * 1.05
            
            exit_price = None
            for j in range(i+1, min(i+11, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+10, len(tdf)-1)]
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) >= 5:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {idx:<13} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
        results_vb.append((idx, len(trades), wr, sh))
    else:
        print(f"❌ {idx:<13} {len(trades):<10} INSUFFICIENT")

if results_vb:
    avg_wr = np.mean([r[2] for r in results_vb])
    print(f"\n📊 Average Win Rate: {avg_wr:.1f}%")

print("\n" + "="*70)
print("STRATEGY 2: RSI Mean Reversion on INDICES")
print("="*70)
print(f"{'Index':<15} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

results_rsi = []
for idx in df['ticker'].unique():
    tdf = df[df['ticker'] == idx].sort_values('date')
    trades = []
    
    for i in range(25, len(tdf) - 10):
        if tdf['rsi'].iloc[i] < 10:
            entry = tdf['close'].iloc[i]
            target = entry * 1.04
            
            exit_price = None
            for j in range(i+1, min(i+11, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+10, len(tdf)-1)]
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) >= 5:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {idx:<13} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
        results_rsi.append((idx, len(trades), wr, sh))
    else:
        print(f"❌ {idx:<13} {len(trades):<10} INSUFFICIENT")

if results_rsi:
    avg_wr = np.mean([r[2] for r in results_rsi])
    print(f"\n📊 Average Win Rate: {avg_wr:.1f}%")

print("\n" + "="*70)
print("STRATEGY 3: Inside Day Breakout on INDICES")
print("="*70)
print(f"{'Index':<15} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

results_id = []
for idx in df['ticker'].unique():
    tdf = df[df['ticker'] == idx].sort_values('date')
    trades = []
    
    for i in range(5, len(tdf) - 5):
        if (tdf['inside_day'].iloc[i-1] and 
            tdf['vol_ratio'].iloc[i] > 2.0 and
            tdf['close'].iloc[i] > tdf['prev_high'].iloc[i] * 1.02):
            
            entry = tdf['close'].iloc[i]
            target = entry * 1.05
            
            exit_price = None
            for j in range(i+1, min(i+6, len(tdf))):
                if tdf['high'].iloc[j] >= target:
                    exit_price = target
                    break
            if exit_price is None:
                exit_price = tdf['close'].iloc[min(i+5, len(tdf)-1)]
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) >= 3:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {idx:<13} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
        results_id.append((idx, len(trades), wr, sh))
    else:
        print(f"❌ {idx:<13} {len(trades):<10} INSUFFICIENT")

if results_id:
    avg_wr = np.mean([r[2] for r in results_id])
    print(f"\n📊 Average Win Rate: {avg_wr:.1f}%")

print("\n" + "="*70)
print("SUMMARY: Golden Strategies on Global Indices")
print("="*70)

all_results = []
if results_vb:
    all_results.append(("Volume Breakout", np.mean([r[2] for r in results_vb])))
if results_rsi:
    all_results.append(("RSI Mean Reversion", np.mean([r[2] for r in results_rsi])))
if results_id:
    all_results.append(("Inside Day Breakout", np.mean([r[2] for r in results_id])))

if all_results:
    print(f"\n{'Strategy':<25} {'Avg Win%':<15} {'Status'}")
    print("-"*45)
    for name, wr in all_results:
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {name:<23} {wr:<15.1f}")

print("="*70)
