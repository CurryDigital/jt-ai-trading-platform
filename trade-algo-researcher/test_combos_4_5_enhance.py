#!/usr/bin/env python3
"""
ENHANCE: Combo 4 and Combo 5 to 70%+
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
print("ENHANCE: Combos 4 & 5 - Push to 70%+")
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector IN ('Tech', 'Equity') LIMIT 50")
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

print(f"Data: {df['ticker'].nunique()} tickers\n")

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
    tdf['return'] = tdf['close'].pct_change()
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    tdf['rsi'] = calculate_rsi(tdf['close'])
    tdf['range'] = tdf['high'] - tdf['low']
    tdf['atr'] = tdf['range'].rolling(14).mean()
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi', 'atr'])

print("="*70)
print("COMBO 4: 3-Day Down + RSI + Volume")
print("="*70)

configs_4 = [
    (20, 1.5, 5, 'Base: RSI<20, Vol>1.5x'),
    (15, 1.5, 5, 'Tighter RSI: RSI<15'),
    (20, 2.0, 5, 'Tighter Vol: Vol>2x'),
    (15, 2.0, 5, 'Both Tighter'),
    (25, 1.5, 5, 'Looser RSI: RSI<25'),
]

print(f"{'Config':<30} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

for rsi_thresh, vol_mult, hold_days, name in configs_4:
    trades = []
    
    for ticker in df['ticker'].unique():
        tdf = df[df['ticker'] == ticker].sort_values('date')
        
        for i in range(10, len(tdf) - hold_days):
            if (tdf['return'].iloc[i] < 0 and 
                tdf['return'].iloc[i-1] < 0 and 
                tdf['return'].iloc[i-2] < 0 and
                tdf['rsi'].iloc[i] < rsi_thresh and
                tdf['vol_ratio'].iloc[i] > vol_mult):
                
                entry = tdf['close'].iloc[i]
                target = entry * 1.04
                
                exit_price = None
                for j in range(i+1, min(i+hold_days+1, len(tdf))):
                    if tdf['high'].iloc[j] >= target:
                        exit_price = target
                        break
                if exit_price is None:
                    exit_price = tdf['close'].iloc[min(i+hold_days, len(tdf)-1)]
                
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 20:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {name:<28} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
    else:
        print(f"❌ {name:<28} {len(trades):<10} INSUFFICIENT")

print("\n" + "="*70)
print("COMBO 5: Range Expansion + Volume + RSI")
print("="*70)

configs_5 = [
    (1.5, 2.0, 50, 5, 'Base: Range>1.5xATR, Vol>2x, RSI<50'),
    (1.5, 2.5, 50, 5, 'Tighter Vol: Vol>2.5x'),
    (2.0, 2.0, 50, 5, 'Tighter Range: Range>2xATR'),
    (1.5, 2.0, 40, 5, 'Tighter RSI: RSI<40'),
    (2.0, 2.5, 40, 5, 'All Tighter'),
]

print(f"{'Config':<35} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

for range_mult, vol_mult, rsi_thresh, hold_days, name in configs_5:
    trades = []
    
    for ticker in df['ticker'].unique():
        tdf = df[df['ticker'] == ticker].sort_values('date')
        
        for i in range(20, len(tdf) - hold_days):
            if (tdf['range'].iloc[i] > tdf['atr'].iloc[i] * range_mult and
                tdf['vol_ratio'].iloc[i] > vol_mult and
                tdf['rsi'].iloc[i] < rsi_thresh and
                tdf['close'].iloc[i] > tdf['open'].iloc[i]):
                
                entry = tdf['close'].iloc[i]
                target = entry * 1.04
                
                exit_price = None
                for j in range(i+1, min(i+hold_days+1, len(tdf))):
                    if tdf['high'].iloc[j] >= target:
                        exit_price = target
                        break
                if exit_price is None:
                    exit_price = tdf['close'].iloc[min(i+hold_days, len(tdf)-1)]
                
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 20:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
        status = "✅" if wr >= 70 else "🧪" if wr >= 60 else "❌"
        print(f"{status} {name:<33} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
    else:
        print(f"❌ {name:<33} {len(trades):<10} INSUFFICIENT")

print("="*70)
