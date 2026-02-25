#!/usr/bin/env python3
"""
ENHANCE Combo 3: Inside Day + Volume + Breakout
Target: Push from 65.2% to 70%+
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
print("ENHANCE: Inside Day + Volume + Breakout")
print("Target: Push from 65.2% to 70%+ win rate")
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

print(f"Data: {df['ticker'].nunique()} tickers, {len(df)} records\n")

# Calculate indicators
all_data = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date').copy()
    tdf['prev_high'] = tdf['high'].shift(1)
    tdf['prev_low'] = tdf['low'].shift(1)
    tdf['inside_day'] = (tdf['high'] < tdf['prev_high']) & (tdf['low'] > tdf['prev_low'])
    tdf['vol_avg'] = tdf['volume'].rolling(20).mean()
    tdf['vol_ratio'] = tdf['volume'] / tdf['vol_avg']
    tdf['return'] = tdf['close'].pct_change()
    all_data.append(tdf)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['vol_ratio'])

# Test different combinations
configs = [
    # (vol_mult, breakout_pct, hold_days, name)
    (2.0, 0.01, 5, 'Base: Vol>2x, Break >1%'),
    (2.5, 0.01, 5, 'Tighter Vol: Vol>2.5x'),
    (2.0, 0.02, 5, 'Tighter Break: Break >2%'),
    (2.5, 0.02, 5, 'Both Tighter'),
    (3.0, 0.02, 5, 'Very Tight: Vol>3x, Break >2%'),
    (2.5, 0.02, 10, 'Longer Hold: 10 days'),
    (2.0, 0.015, 5, 'Medium: Vol>2x, Break >1.5%'),
]

print("TESTING CONFIGURATIONS:")
print("-"*70)
print(f"{'Config':<35} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*70)

results = []

for vol_mult, break_pct, hold_days, name in configs:
    trades = []
    
    for ticker in df['ticker'].unique():
        tdf = df[df['ticker'] == ticker].sort_values('date')
        
        for i in range(5, len(tdf) - hold_days):
            if (tdf['inside_day'].iloc[i-1] and 
                tdf['vol_ratio'].iloc[i] > vol_mult and
                tdf['close'].iloc[i] > tdf['prev_high'].iloc[i] * (1 + break_pct)):
                
                entry = tdf['close'].iloc[i]
                target = entry * 1.05  # 5% profit target
                
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
    elif best[2] >= 65:
        print("\n🧪 Very close to 70% - minor adjustments needed")
    else:
        print("\n❌ Could not reach 70% with these filters")

print("="*70)
