#!/usr/bin/env python3
"""
RSI Enhancement - Extreme Filters to Reach 70%
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
print("ENHANCEMENT: RSI Extreme Filters - Target 70%")
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
cursor.execute("SELECT DISTINCT ticker FROM gold.stock_metrics WHERE sector = 'Tech' LIMIT 20")
tickers = [row[0] for row in cursor.fetchall()]
cursor.close()

ticker_list = "','".join(tickers)
price_query = f"""
SELECT date, ticker, close, volume
FROM silver.historical_stock_data
WHERE ticker IN ('{ticker_list}') AND date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY ticker, date
"""
df = pd.read_sql(price_query, conn)
conn.close()

print(f"Data: {len(df)} records, {df['ticker'].nunique()} tickers")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

all_data = []
for ticker in df['ticker'].unique():
    ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
    ticker_df['rsi_14'] = calculate_rsi(ticker_df['close'])
    ticker_df['vol_avg'] = ticker_df['volume'].rolling(20).mean()
    ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
    all_data.append(ticker_df)

df = pd.concat(all_data, ignore_index=True)
df = df.dropna(subset=['rsi_14'])

print(f"After calc: {len(df)} records")

# Test extreme combinations
configs = [
    # (rsi_threshold, require_consecutive, vol_min, exit_type)
    (15, False, 0, 'profit'),       # Baseline
    (15, True, 0, 'profit'),        # Require consecutive oversold
    (15, False, 1.5, 'profit'),     # Volume filter
    (15, True, 1.5, 'profit'),      # Both filters
    (12, False, 0, 'profit'),       # Extreme RSI
    (12, True, 0, 'profit'),        # Extreme + consecutive
    (10, False, 0, 'profit'),       # Very extreme
]

print("\n" + "="*70)
print("RSI EXTREME FILTER RESULTS")
print("="*70)
print(f"{'RSI':<6} {'Cons':<6} {'Vol':<6} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
print("-"*60)

results_summary = []

for rsi_thresh, require_cons, vol_min, exit_type in configs:
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 50:
            continue
        
        for i in range(25, len(ticker_df) - 15):
            rsi_val = ticker_df['rsi_14'].iloc[i]
            
            if pd.isna(rsi_val) or rsi_val >= rsi_thresh:
                continue
            
            # Check consecutive oversold
            if require_cons:
                if i < 2:
                    continue
                prev_rsi = ticker_df['rsi_14'].iloc[i-1]
                if prev_rsi >= rsi_thresh:
                    continue
            
            # Check volume
            if vol_min > 0:
                vol_ratio = ticker_df['vol_ratio'].iloc[i]
                if pd.isna(vol_ratio) or vol_ratio < vol_min:
                    continue
            
            entry_price = ticker_df['close'].iloc[i]
            
            if exit_type == 'profit':
                target = entry_price * 1.04
                exit_price = None
                for j in range(i+1, min(i+15, len(ticker_df))):
                    if ticker_df['close'].iloc[j] >= target:
                        exit_price = target
                        break
                if exit_price is None:
                    exit_price = ticker_df['close'].iloc[min(i+10, len(ticker_df)-1)]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)
    
    if len(trades) < 20:
        cons_str = "Yes" if require_cons else "No"
        vol_str = f"{vol_min}" if vol_min > 0 else "No"
        print(f"{rsi_thresh:<6} {cons_str:<6} {vol_str:<6} INSUFFICIENT ({len(trades)})")
        continue
    
    returns = pd.Series(trades)
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    cons_str = "Yes" if require_cons else "No"
    vol_str = f"{vol_min}" if vol_min > 0 else "No"
    status = "✅" if win_rate >= 70 else "🧪" if win_rate >= 65 else "❌"
    print(f"{status} {rsi_thresh:<4} {cons_str:<6} {vol_str:<6} {len(trades):<10} {win_rate:<10.1f} {sharpe:<10.2f}")
    
    results_summary.append({
        'rsi': rsi_thresh,
        'cons': require_cons,
        'vol': vol_min,
        'trades': len(trades),
        'win_rate': win_rate,
        'sharpe': sharpe
    })

print("="*70)

if results_summary:
    best = max(results_summary, key=lambda x: x['win_rate'])
    print(f"\n🏆 BEST: RSI <{best['rsi']}, Cons={best['cons']}, Vol={best['vol']}")
    print(f"    Win Rate: {best['win_rate']:.1f}%, Sharpe: {best['sharpe']:.2f}, Trades: {best['trades']}")
    
    if best['win_rate'] >= 70:
        print("\n🎉🎉🎉 TARGET ACHIEVED! RSI at 70%+ 🎉🎉🎉")
    elif best['win_rate'] >= 67:
        print("\n🧪 Very close to 70% - minor adjustments needed")
    else:
        print("\n❌ Still below target - need different approach")
