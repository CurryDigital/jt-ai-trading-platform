#!/usr/bin/env python3
"""
BATCH 15: CMV Multi-Factor Filter — FULL UNIVERSE TEST
Test on ALL tickers across US, CN, SG, HK markets
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# FULL UNIVERSE: 200+ tickers across all markets
FULL_UNIVERSE = {
    # HK Equities (60+ tickers)
    'HK': [
        # Banks
        '0005.HK', '0011.HK', '0023.HK', '0939.HK', '0998.HK', '1288.HK', '1398.HK', 
        '1963.HK', '2388.HK', '3328.HK', '3618.HK', '3968.HK', '3988.HK', '6190.HK',
        # Tech
        '0700.HK', '0762.HK', '0772.HK', '0885.HK', '0981.HK', '1024.HK', '1810.HK', 
        '2382.HK', '9888.HK', '9988.HK', '9999.HK',
        # Property
        '0001.HK', '0012.HK', '0016.HK', '0068.HK', '0083.HK', '0113.HK', '0688.HK',
        '1109.HK', '1113.HK', '2007.HK', '3333.HK',
        # Insurance
        '1299.HK', '2318.HK', '2628.HK', '6060.HK',
        # Energy/Utilities
        '0002.HK', '0003.HK', '0006.HK', '0270.HK', '0883.HK', '0941.HK', '1038.HK',
        '1088.HK', '2688.HK',
        # Consumer/Healthcare
        '0316.HK', '0598.HK', '1093.HK', '1177.HK', '1876.HK', '1929.HK', '2313.HK',
        '2319.HK', '2331.HK', '6098.HK', '6862.HK',
    ],
    
    # US Equities (80+ tickers)
    'US': [
        # Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD',
        # Semiconductors
        'INTC', 'AVGO', 'QCOM', 'TXN', 'MU', 'AMAT', 'LRCX', 'KLAC', 'SNPS', 'CDNS',
        # Software/SaaS
        'CRM', 'ADBE', 'ORCL', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'ZS', 'NET', 'DDOG',
        'OKTA', 'MDB', 'TWLO', 'ROKU', 'ZM', 'SHOP', 'UBER', 'LYFT', 'DASH', 'ABNB',
        # Banks/Financials
        'JPM', 'BAC', 'GS', 'MS', 'C', 'WFC', 'PNC', 'USB', 'COF', 'AXP', 'BLK',
        # Consumer
        'WMT', 'COST', 'HD', 'LOW', 'TGT', 'NKE', 'MCD', 'SBUX', 'BKNG', 'MAR',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY',
        # Industrial/Energy
        'GE', 'CAT', 'BA', 'RTX', 'LMT', 'NOC', 'XOM', 'CVX', 'COP', 'SLB',
        # ETFs
        'SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLU', 'XLI', 'XLP', 'ARKK',
        # Crypto/Spec
        'MSTR', 'COIN', 'HOOD', 'RIOT', 'MARA',
    ],
    
    # China A-Shares (40+ tickers)
    'CN': [
        # Banks
        '601288.SS', '601398.SS', '601939.SS', '601988.SS', '601328.SS', '601166.SS',
        '600036.SS', '600016.SS',
        # Insurance
        '601318.SS', '601628.SS', '601336.SS',
        # Energy
        '601088.SS', '600028.SS', '600938.SS',
        # Telecom
        '600941.SS', '600050.SS',
        # Tech/Semiconductors
        '688981.SS', '688008.SS', '688126.SS', '688012.SS',
        # Consumer/Staples
        '600519.SS', '000858.SZ', '000568.SZ', '000333.SZ', '000538.SZ',
        # EV/Auto
        '300750.SZ', '002594.SZ', '601127.SS', '601633.SS',
        # Healthcare
        '600276.SS', '603259.SS', '000661.SZ',
        # Property/Home
        '002271.SZ', '000002.SZ', '600048.SS',
    ],
    
    # Singapore REITs & Banks (20+ tickers)
    'SG': [
        # REITs
        'A17U.SI', 'C38U.SI', 'C61U.SI', 'J91U.SI', 'N2IU.SI', 
        'ME8U.SI', 'M44U.SI', 'BUOU.SI', 'CRPU.SI', 'K71U.SI',
        # Banks
        'D05.SI', 'O39.SI', 'U11.SI', 'S68.SI',
        # Telco
        'Z74.SI', 'CC3.SI',
        # Others
        'G13.SI', 'Y92.SI', 'S63.SI', 'C52.SI', 'U14.SI',
    ],
}

# Flatten universe
ALL_TICKERS = []
for market, tickers in FULL_UNIVERSE.items():
    ALL_TICKERS.extend([(t, market) for t in tickers])

print(f"Full Universe: {len(ALL_TICKERS)} tickers")
print(f"  HK: {len(FULL_UNIVERSE['HK'])} tickers")
print(f"  US: {len(FULL_UNIVERSE['US'])} tickers")
print(f"  CN: {len(FULL_UNIVERSE['CN'])} tickers")
print(f"  SG: {len(FULL_UNIVERSE['SG'])} tickers")
