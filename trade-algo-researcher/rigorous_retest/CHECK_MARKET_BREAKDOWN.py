#!/usr/bin/env python3
"""
QUICK SECTOR CHECK — Which markets have best RSI performance
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
import pandas as pd

db = TradeAlgoDB()
conn = db.connect()

# Get all tickers with their markets
query = """
SELECT ticker, COUNT(*) as records,
    CASE 
        WHEN ticker LIKE '%.HK' THEN 'HK'
        WHEN ticker LIKE '%.SI' THEN 'SG'
        WHEN ticker LIKE '%.SS' OR ticker LIKE '%.SZ' THEN 'CN'
        WHEN ticker LIKE '%-USD' OR ticker IN ('BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'LINK') THEN 'CRYPTO'
        WHEN ticker LIKE '%=X' THEN 'FX'
        WHEN ticker LIKE '%=F' THEN 'FUTURES'
        ELSE 'US'
    END as market
FROM silver.unified_prices 
WHERE date >= '2021-01-01'
GROUP BY ticker
HAVING COUNT(*) >= 500
ORDER BY market, ticker
"""

df = pd.read_sql(query, conn)

print("=" * 80)
print("TICKER COUNT BY MARKET")
print("=" * 80)
print(df.groupby('market').size().sort_values(ascending=False))

print("\n" + "=" * 80)
print("SAMPLE TICKERS BY MARKET")
print("=" * 80)

for market in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
    sample = df[df['market'] == market]['ticker'].head(10).tolist()
    print(f"\n{market} ({len(df[df['market'] == market])} tickers):")
    print(f"  {', '.join(sample)}")

# Get a few tickers from each market to test
print("\n" + "=" * 80)
print("SELECTED TEST TICKERS (Top 5 from each market)")
print("=" * 80)

test_tickers = {}
for market in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
    market_tickers = df[df['market'] == market]['ticker'].head(5).tolist()
    test_tickers[market] = market_tickers
    print(f"\n{market}: {', '.join(market_tickers)}")

conn.close()
print(f"\n{'='*80}")
print("Ready to test these 25 tickers (5 per market)")
