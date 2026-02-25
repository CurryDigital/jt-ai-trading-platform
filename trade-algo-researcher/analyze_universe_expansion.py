#!/usr/bin/env python3
"""
UNIVERSE EXPANSION: Add S&P 500, Dow, Nasdaq Components
Plus Real Estate sector analysis
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd

print("="*70)
print("UNIVERSE EXPANSION ANALYSIS")
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

# Current universe
cursor.execute('''
SELECT DISTINCT ticker, sector 
FROM gold.stock_metrics 
WHERE sector IS NOT NULL
ORDER BY sector, ticker
''')
classified = cursor.fetchall()

print(f"CURRENT UNIVERSE: {len(classified)} tickers")
print(f"  - Tech: {sum(1 for t, s in classified if s == 'Tech')}")
print(f"  - Equity: {sum(1 for t, s in classified if s == 'Equity')}")

# Available US tickers NOT classified
cursor.execute('''
SELECT DISTINCT s.ticker 
FROM silver.historical_stock_data s
LEFT JOIN gold.stock_metrics g ON s.ticker = g.ticker
WHERE g.ticker IS NULL
AND s.ticker NOT LIKE '%.HK'
AND s.ticker NOT LIKE '%.SS'
AND s.ticker NOT LIKE '%.SZ'
AND s.ticker NOT LIKE '^%'
AND s.ticker NOT LIKE '%=%'
AND s.ticker NOT LIKE '%-%'
ORDER BY s.ticker
''')
unclassified_us = [row[0] for row in cursor.fetchall()]

print(f"\nUNCLASSIFIED US STOCKS: {len(unclassified_us)}")
print("Tickers available for classification:")
for i, ticker in enumerate(unclassified_us[:30]):
    print(f"  {ticker}", end="")
    if (i+1) % 5 == 0:
        print()
if len(unclassified_us) % 5 != 0:
    print()

if len(unclassified_us) > 30:
    print(f"  ... and {len(unclassified_us) - 30} more")

# All US stocks (classified + unclassified)
cursor.execute('''
SELECT DISTINCT ticker 
FROM silver.historical_stock_data 
WHERE ticker NOT LIKE '%.HK' 
  AND ticker NOT LIKE '%.SS' 
  AND ticker NOT LIKE '%.SZ'
  AND ticker NOT LIKE '^%'
  AND ticker NOT LIKE '%=%'
  AND ticker NOT LIKE '%-%'
ORDER BY ticker
''')
all_us = [row[0] for row in cursor.fetchall()]

print(f"\n\nTOTAL US STOCKS AVAILABLE: {len(all_us)}")
print("Sample:", all_us[:20])

# Check for Real Estate/REIT candidates
cursor.execute('''
SELECT DISTINCT ticker 
FROM silver.historical_stock_data 
WHERE ticker NOT LIKE '%.HK' 
  AND ticker NOT LIKE '%.SS' 
  AND ticker NOT LIKE '%.SZ'
  AND ticker NOT LIKE '^%'
  AND ticker NOT LIKE '%=%'
  AND ticker NOT LIKE '%-%'
ORDER BY ticker
''')
all_stocks = [row[0] for row in cursor.fetchall()]

# Known REITs and Real Estate stocks to check
reit_candidates = ['O', 'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'WELL', 'DLR', 
                   'AVB', 'EXR', 'VTR', 'BXP', 'ARE', 'HCP', 'ESS', 'MAA', 'UDR', 
                   'KIM', 'FRT', 'REG', 'CPT', 'AIV', 'PEAK']

available_reits = [t for t in reit_candidates if t in all_stocks]

print(f"\n\nREAL ESTATE/REIT CANDIDATES:")
print(f"Available in database: {available_reits}")

# Major index components to check
sp500_candidates = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'BRK-B', 'META', 'TSLA', 
                    'UNH', 'LLY', 'JPM', 'V', 'XOM', 'JNJ', 'WMT', 'MA', 'PG', 'AVGO',
                    'HD', 'CVX', 'MRK', 'ABBV', 'PEP', 'COST', 'KO', 'ADBE', 'WFC',
                    'TMO', 'ACN', 'MCD', 'CSCO', 'VZ', 'DIS', 'ABT', 'BMY', 'TXN',
                    'CMCSA', 'NEE', 'PFE', 'CRM', 'PM', 'RTX', 'NKE', 'QCOM']

nasdaq_candidates = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'TSLA', 'AVGO',
                     'PEP', 'COST', 'CSCO', 'TMUS', 'ADBE', 'TXN', 'HON', 'INTC',
                     'QCOM', 'AMGN', 'SBUX', 'INTU', 'BKNG', 'LRCX', 'MDLZ', 'GILD',
                     'ADI', 'VRTX', 'ISRG', 'MU', 'ADP', 'REGN', 'PANW', 'SNPS',
                     'KLAC', 'FTNT', 'CDNS', 'ASML', 'NXPI', 'ENPH', 'JD', 'ZM']

# Check availability
available_sp500 = [t for t in sp500_candidates if t in all_stocks]
available_nasdaq = [t for t in nasdaq_candidates if t in all_stocks]

print(f"\n\nS&P 500 COMPONENTS AVAILABLE: {len(available_sp500)}/{len(sp500_candidates)}")
print(available_sp500[:20], "..." if len(available_sp500) > 20 else "")

print(f"\nNASDAQ COMPONENTS AVAILABLE: {len(available_nasdaq)}/{len(nasdaq_candidates)}")
print(available_nasdaq[:20], "..." if len(available_nasdaq) > 20 else "")

# Proposed expansion
print("\n" + "="*70)
print("PROPOSED UNIVERSE EXPANSION")
print("="*70)

print(f"\nCURRENT: 179 tickers (30 Tech + 149 Equity)")
print(f"\nPROPOSED: ~250-300 tickers")
print(f"  - Add 30-50 more US Large Cap (S&P 500)")
print(f"  - Add Real Estate sector (~20 REITs)")
print(f"  - Classify remaining unclassified tickers")

conn.close()

print("\n" + "="*70)
