#!/usr/bin/env python3
"""
Check current SPY regime
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
import pandas as pd

db = TradeAlgoDB()
conn = db.connect()

# Get latest SPY data
query = """
SELECT date, close FROM silver.unified_prices
WHERE ticker = 'SPY' ORDER BY date DESC LIMIT 250
"""

df = pd.read_sql(query, conn)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Calculate 200d MA
df['sma200'] = df['close'].rolling(200).mean()
df['regime'] = df['close'] > df['sma200']

latest = df.iloc[-1]
regime = "BULL 🐂" if latest['regime'] else "BEAR 🐻"

print("=" * 60)
print("CURRENT SPY REGIME CHECK")
print("=" * 60)
print(f"\nLatest Date: {latest['date'].strftime('%Y-%m-%d')}")
print(f"SPY Close: ${latest['close']:.2f}")
print(f"200d MA: ${latest['sma200']:.2f}")
print(f"\nCURRENT REGIME: {regime}")

if latest['regime']:
    print(f"\n→ Deploy BULL portfolio (15 strategies)")
else:
    print(f"\n→ Deploy BEAR portfolio (11 strategies)")

# Show recent regime history
print(f"\n{'='*60}")
print("Recent Regime History (Last 10 days):")
print(f"{'='*60}")
recent = df.tail(10)[['date', 'close', 'sma200', 'regime']].copy()
recent['regime_str'] = recent['regime'].map({True: 'BULL', False: 'BEAR'})
for _, row in recent.iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d')}: SPY=${row['close']:.2f}, 200d=${row['sma200']:.2f} → {row['regime_str']}")

conn.close()
print(f"\n{'='*60}")
