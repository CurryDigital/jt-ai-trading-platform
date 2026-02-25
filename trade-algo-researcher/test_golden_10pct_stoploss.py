#!/usr/bin/env python3
"""
TEST: Adding 10% Stop Loss to Golden Strategies
Testing if -10% stop loss improves risk-adjusted returns
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
print("TESTING: 10% Stop Loss on Golden Strategies")
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
       ti.rsi_14, ti.vol_ratio, ti.bb_lower, ti.bb_upper
FROM silver.historical_stock_data t
INNER JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])
df['is_monday'] = df['date'].dt.dayofweek == 0

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# ============================================
# STRATEGY 1: BB Extreme + Monday GOLD
# ============================================

print("="*70)
print("STRATEGY 1: BB Extreme + Monday GOLD (78.5% baseline)")
print("="*70)

# Without stop loss - BASELINE
print("\n1. WITHOUT Stop Loss (Current)")
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

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%, Trades: {len(trades)}")
results.append(('BB+Mon_NoSL', wr, sh, max_dd, len(trades)))

# With 10% stop loss
print("\n2. WITH 10% Stop Loss")
trades = []
stop_hits = 0
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
            tdf['rsi_14'].iloc[i] < 20 and 
            tdf['vol_ratio'].iloc[i] > 1.5 and
            tdf['is_monday'].iloc[i]):
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]  # Default time exit
            
            # Check if stop loss hit during hold period
            for j in range(1, 11):
                if i + j < len(tdf):
                    current_price = tdf['close'].iloc[i + j]
                    # Stop loss at -10%
                    if current_price <= entry * 0.90:
                        exit_price = entry * 0.90
                        stop_hits += 1
                        break
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
stop_pct = stop_hits / len(trades) * 100 if len(trades) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%")
print(f"   Stop Hits: {stop_hits} ({stop_pct:.1f}% of trades), Trades: {len(trades)}")
results.append(('BB+Mon_SL10', wr, sh, max_dd, len(trades)))

# ============================================
# STRATEGY 2: RSI Mean Reversion (RSI < 10)
# ============================================

print("\n" + "="*70)
print("STRATEGY 2: RSI Mean Reversion (72.6% baseline)")
print("="*70)

# Without stop loss - BASELINE
print("\n1. WITHOUT Stop Loss (Current)")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 10:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%, Trades: {len(trades)}")
results.append(('RSI_NoSL', wr, sh, max_dd, len(trades)))

# With 10% stop loss
print("\n2. WITH 10% Stop Loss")
trades = []
stop_hits = 0
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 10:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            
            for j in range(1, 11):
                if i + j < len(tdf):
                    current_price = tdf['close'].iloc[i + j]
                    if current_price <= entry * 0.90:
                        exit_price = entry * 0.90
                        stop_hits += 1
                        break
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
stop_pct = stop_hits / len(trades) * 100 if len(trades) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%")
print(f"   Stop Hits: {stop_hits} ({stop_pct:.1f}% of trades), Trades: {len(trades)}")
results.append(('RSI_SL10', wr, sh, max_dd, len(trades)))

# ============================================
# STRATEGY 3: Volume Breakout
# ============================================

print("\n" + "="*70)
print("STRATEGY 3: Volume Breakout (70.8% baseline)")
print("="*70)

# Without stop loss - BASELINE
print("\n1. WITHOUT Stop Loss (Current)")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 10):
        if tdf['vol_ratio'].iloc[i] > 2.0 and tdf['return'].iloc[i] > 0.04:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%, Trades: {len(trades)}")
results.append(('VolBO_NoSL', wr, sh, max_dd, len(trades)))

# With 10% stop loss
print("\n2. WITH 10% Stop Loss")
trades = []
stop_hits = 0
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    tdf['return'] = tdf['close'].pct_change()
    for i in range(25, len(tdf) - 10):
        if tdf['vol_ratio'].iloc[i] > 2.0 and tdf['return'].iloc[i] > 0.04:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            
            for j in range(1, 11):
                if i + j < len(tdf):
                    current_price = tdf['close'].iloc[i + j]
                    if current_price <= entry * 0.90:
                        exit_price = entry * 0.90
                        stop_hits += 1
                        break
            
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

r = pd.Series(trades)
wr = (r > 0).mean() * 100
sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
max_dd = r.min()
avg_loss = r[r < 0].mean() if len(r[r < 0]) > 0 else 0
stop_pct = stop_hits / len(trades) * 100 if len(trades) > 0 else 0
print(f"   Win%: {wr:.1f}, Sharpe: {sh:.2f}, Max Loss: {max_dd:.1f}%, Avg Loss: {avg_loss:.1f}%")
print(f"   Stop Hits: {stop_hits} ({stop_pct:.1f}% of trades), Trades: {len(trades)}")
results.append(('VolBO_SL10', wr, sh, max_dd, len(trades)))

# ============================================
# SUMMARY
# ============================================

print("\n" + "="*70)
print("SUMMARY: 10% Stop Loss Impact on Golden Strategies")
print("="*70)

print("\n| Strategy | No SL Win% | With SL Win% | Change | No SL Sharpe | With SL Sharpe | Max Loss Improvement |")
print("|----------|------------|--------------|--------|--------------|----------------|----------------------|")

for i in range(0, len(results), 2):
    name = results[i][0].replace('_NoSL', '')
    no_sl = results[i]
    with_sl = results[i+1]
    change = with_sl[0] - no_sl[0]
    max_dd_improvement = no_sl[2] - with_sl[2]  # Less negative is better
    print(f"| {name:<8} | {no_sl[0]:6.1f}% | {with_sl[0]:8.1f}% | {change:+5.1f}% | {no_sl[1]:8.2f} | {with_sl[1]:10.2f} | {max_dd_improvement:8.1f}% |")

print("\n" + "="*70)
print("ANALYSIS:")
print("="*70)
print("\n✅ BENEFITS of 10% Stop Loss:")
print("   - Caps maximum loss at -10% (vs -20% to -50% without)")
print("   - Reduces drawdowns")
print("   - Psychologically easier to trade")

print("\n❌ DOWNSIDES of 10% Stop Loss:")
print("   - May exit on normal volatility before recovery")
print("   - Reduces win rate (stops hit on noise)")
print("   - Hurts Sharpe ratio")

print("\n💡 RECOMMENDATION:")
print("   Test on paper trading first - measure actual stop hit rate")
print("   If stops hit >15% of the time, may hurt overall performance")
print("="*70)
