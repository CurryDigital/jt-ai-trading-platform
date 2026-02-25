#!/usr/bin/env python3
"""
GET FULL TICKER UNIVERSE FROM DATABASE
Check what's actually available across 4 markets
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
import pandas as pd

db = TradeAlgoDB()
conn = db.connect()

print("=" * 80)
print("CHECKING FULL TICKER UNIVERSE IN DATABASE")
print("=" * 80)

# Get all tickers
query = """
SELECT ticker, COUNT(*) as records, MIN(date) as start_date, MAX(date) as end_date
FROM silver.unified_prices
GROUP BY ticker
ORDER BY records DESC
"""

df = pd.read_sql(query, conn)

print(f"\nTotal tickers in database: {len(df)}")
print(f"\nTop 50 by record count:")
print(df.head(50).to_string(index=False))

# Categorize by market
print("\n" + "=" * 80)
print("MARKET BREAKDOWN")
print("=" * 80)

# HK tickers (ends with .HK)
hk = df[df['ticker'].str.endswith('.HK', na=False)]
print(f"\nHK (.HK): {len(hk)} tickers")
print(hk.head(20)['ticker'].tolist())

# Singapore tickers (ends with .SI)
sg = df[df['ticker'].str.endswith('.SI', na=False)]
print(f"\nSingapore (.SI): {len(sg)} tickers")
print(sg['ticker'].tolist() if len(sg) > 0 else "None")

# China A-shares (starts with 6, 0, 3)
cn = df[df['ticker'].str.match(r'^[603]\d{5}', na=False)]
print(f"\nChina A-shares: {len(cn)} tickers")
print(cn.head(10)['ticker'].tolist() if len(cn) > 0 else "None")

# US tickers (no suffix, or common US tickers)
us_keywords = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'SPY', 'QQQ', 'PLTR', 'COIN', 'MSTR']
us = df[df['ticker'].isin(us_keywords) | ~df['ticker'].str.contains(r'\.|=', na=False)]
print(f"\nUS (no suffix): {len(us)} tickers")
print(us.head(30)['ticker'].tolist())

# Crypto
crypto = df[df['ticker'].str.contains('BTC|ETH|SOL|ADA|DOT|COIN|MSTR', na=False)]
print(f"\nCrypto-related: {len(crypto)} tickers")
print(crypto['ticker'].tolist() if len(crypto) > 0 else "None")

conn.close()
print(f"\n{'='*80}")
