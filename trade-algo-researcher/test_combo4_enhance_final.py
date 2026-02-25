#!/usr/bin/env python3
"""
ENHANCE Combo 4: 3-Day Down + RSI + Volume
Target: Push from 68.4% to 70%+
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
print("ENHANCE: Combo 4 - 3-Day Down + RSI + Volume")
print("Target: Push from 68.4% to 70%+ win rate")
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
SELECT date, ticker, close, volume, high
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data: {df['ticker'].nunique()} tickers\n")

# Calculate indicators
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
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi'])

# Test different configurations
configs = [
    # (rsi_thresh, vol_mult, hold_days, exit_type, name)
    (20, 2.0, 5, 'time', 'Base: RSI<20, Vol>2x, Time'),
    (15, 2.0, 5, 'time', 'Tighter RSI: RSI<15'),
    (20, 2.5, 5, 'time', 'Tighter Vol: Vol>2.5x'),
    (15, 2.5, 5, 'time', 'Both Tighter'),
    (20, 2.0, 10, 'time', 'Longer Hold: 10 days'),
    (20, 2.0, 5, 'profit4', 'Profit Target: +4%'),
    (20, 2.0, 5, 'profit5', 'Profit Target: +5%'),
    (18, 2.0, 5, 'profit4', 'RSI 18 + Profit 4%'),
    (15, 2.0, 5, 'profit4', 'RSI 15 + Profit 4%'),
    (20, 1.5, 5, 'profit4', 'Looser Vol + Profit'),
]

print("TESTING CONFIGURATIONS:")
print("-"*70)
print(f"{'Config':<35} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

results = []

for rsi_thresh, vol_mult, hold_days, exit_type, name in configs:
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
                
                if exit_type == 'time':
                    exit_price = tdf['close'].iloc[i + hold_days]
                else:
                    profit_pct = 0.04 if exit_type == 'profit4' else 0.05
                    target = entry * (1 + profit_pct)
                    
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
        sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
        
        status = "✅" if wr >= 70 else "🧪" if wr >= 65 else "❌"
        print(f"{status} {name:<33} {len(trades):<10} {wr:<10.1f} {sh:<10.2f}")
        results.append((name, len(trades), wr, sh))
    else:
        print(f"❌ {name:<33} {len(trades):<10} INSUFFICIENT")

print("-"*70)

if results:
    best = max(results, key=lambda x: x[2])
    print(f"\n🏆 BEST: {best[0]}")
    print(f"    Win Rate: {best[2]:.1f}%, Sharpe: {best[3]:.2f}, Trades: {best[1]}")
    
    if best[2] >= 70:
        print("\n🎉 TARGET ACHIEVED! New Golden Strategy!")
    elif best[2] >= 68:
        print(f"\n🧪 Very close! Only {70 - best[2]:.1f}% away from 70%")
    else:
        print(f"\n❌ Still {70 - best[2]:.1f}% away from target")

print("="*70)
