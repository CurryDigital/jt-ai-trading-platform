#!/usr/bin/env python3
"""
Universe Coverage Analysis
Review representativeness of tickers across all asset classes
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Define full universe
UNIVERSE = {
    'US': {
        'tickers': ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLU', 'XLI', 'XLP', 'XLB', 
                   'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
                   'JNJ', 'UNH', 'XOM', 'LLY', 'AVGO', 'T', 'MA', 'HD', 'PG', 'CVX',
                   'MRK', 'ABBV', 'PEP', 'KO', 'BAC', 'COST', 'CSCO', 'MCD', 'ADBE', 'WFC',
                   'CRM', 'PFE', 'ACN', 'DIS', 'ABT', 'LIN', 'NKE', 'TXN', 'VZ', 'DHR',
                   'BMY', 'RTX', 'HON', 'AMGN', 'QCOM', 'SPGI', 'UPS', 'NEE', 'SCHW', 'LOW'],
        'sectors': ['Tech', 'Healthcare', 'Finance', 'Consumer', 'Energy', 'Industrials'],
        'market_caps': ['Large', 'Mega']
    },
    'HK': {
        'tickers': ['0001.HK', '0002.HK', '0003.HK', '0005.HK', '0006.HK', '0011.HK', '0012.HK',
                   '0016.HK', '0017.HK', '0027.HK', '0066.HK', '0101.HK', '0175.HK', '0241.HK',
                   '0267.HK', '0293.HK', '0386.HK', '0388.HK', '0688.HK', '0700.HK',
                   '0762.HK', '0836.HK', '0857.HK', '0883.HK', '0939.HK', '0998.HK', '1038.HK',
                   '1044.HK', '1093.HK', '1109.HK', '1113.HK', '1177.HK', '1211.HK', '1299.HK',
                   '1398.HK', '1658.HK', '1810.HK', '1876.HK', '1928.HK', '1997.HK',
                   '2313.HK', '2318.HK', '2319.HK', '2382.HK', '2388.HK', '2628.HK', '2688.HK',
                   '2888.HK', '2899.HK', '3690.HK', '9633.HK', '9988.HK', '9999.HK'],
        'sectors': ['Conglomerates', 'Property', 'Finance', 'Utilities', 'Tech'],
        'market_caps': ['Large Cap', 'Mid Cap']
    },
    'CN': {
        'tickers': ['BABA', 'JD', 'PDD', 'NIO', 'LI', 'XPEV', 'BIDU', 'TCEHY', 'BEKE', 'ZTO',
                   'TAL', 'GOTU', 'FUTU', 'LU', 'ZH', 'IQ', 'HUYA', 'DOYU', 'WB', 'VIPS',
                   'MOMO', 'YY', 'MCHI', 'KWEB', 'ASHR', 'FXI', 'CXSE', 'CQQQ', 'CHIQ', 'CHIX',
                   'YINN', 'CHAU', 'PGJ', 'GXC'],
        'sectors': ['Tech', 'E-commerce', 'EVs', 'Education', 'Social Media'],
        'market_caps': ['Large Cap', 'Mid Cap'],
        'note': 'ADRs only - no direct A-shares access'
    },
    'SG': {
        'tickers': ['EWS', 'U11.SI', 'Z74.SI', 'D05.SI', 'G13.SI', 'S63.SI',
                   'O39.SI', 'M44U.SI', 'A17U.SI', 'C38U.SI', 'S58.SI', 'Y92.SI',
                   'BS6.SI', 'C61U.SI', 'H78.SI', 'N2IU.SI', 'T82U.SI', 'U14.SI',
                   'C09.SI', 'S51.SI', 'CC3.SI', 'F34.SI', 'Q0F.SI', 'S68.SI',
                   'RW0U.SI', 'AJBU.SI', 'BUOU.SI', 'ME8U.SI', 'CRPU.SI', 'MINT', 'CRT'],
        'sectors': ['Banks', 'REITs', 'Industrials', 'Telco'],
        'market_caps': ['Large Cap', 'Mid Cap'],
        'note': 'STI components + REITs'
    },
    'FX': {
        'tickers': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 
                   'USDCHF=X', 'NZDUSD=X', 'USDCNY=X', 'USDHKD=X', 'USDSGD=X',
                   'EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X'],
        'pairs': ['G10 majors', 'Asian pairs', 'Crosses'],
        'note': 'Spot FX via yfinance (delayed)'
    },
    'Crypto': {
        'tickers': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD',
                   'MATIC-USD', 'LINK-USD', 'UNI-USD', 'AAVE-USD', 'CRV-USD',
                   'SUSHI-USD', 'COMP-USD', 'MKR-USD', 'YFI-USD', 'SNX-USD'],
        'categories': ['Layer 1', 'DeFi', 'Infrastructure'],
        'note': 'USD denominated spot prices'
    },
    'Commodities': {
        'tickers': ['GLD', 'SLV', 'IAU', 'PPLT', 'CPER',  # Precious metals
                   'USO', 'BNO', 'DBO', 'OILK',  # Oil
                   'UNG', 'UNL',  # Nat gas
                   'DBA', 'RJA',  # Agriculture
                   'DBC', 'GSG', 'PDBC'],  # Broad commodity ETFs
        'categories': ['Precious Metals', 'Energy', 'Agriculture', 'Broad'],
        'note': 'ETF proxies - futures data needed for real backtests'
    }
}

def test_ticker(ticker):
    """Test if ticker works."""
    try:
        data = yf.download(ticker, start='2024-01-01', end='2024-02-01', progress=False)
        return not data.empty
    except:
        return False

def analyze_coverage():
    print("=" * 80)
    print("UNIVERSE COVERAGE ANALYSIS")
    print("=" * 80)
    
    results = {}
    
    for market, config in UNIVERSE.items():
        print(f"\n{'='*40}")
        print(f"{market} MARKET")
        print('='*40)
        
        tickers = config['tickers']
        print(f"Planned tickers: {len(tickers)}")
        
        # Test first 10 to estimate success rate
        test_sample = tickers[:min(10, len(tickers))]
        working_sample = sum([test_ticker(t) for t in test_sample])
        
        estimated_working = int(working_sample / len(test_sample) * len(tickers))
        print(f"Sample success: {working_sample}/{len(test_sample)}")
        print(f"Estimated working: ~{estimated_working}")
        
        if 'sectors' in config:
            print(f"Sectors covered: {', '.join(config['sectors'])}")
        if 'categories' in config:
            print(f"Categories: {', '.join(config['categories'])}")
        if 'note' in config:
            print(f"Note: {config['note']}")
        
        results[market] = {
            'planned': len(tickers),
            'estimated_working': estimated_working,
            'sample_rate': working_sample / len(test_sample)
        }
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_planned = sum(r['planned'] for r in results.values())
    total_estimated = sum(r['estimated_working'] for r in results.values())
    
    print(f"\nTotal tickers (planned): {total_planned}")
    print(f"Total tickers (estimated working): {total_estimated}")
    
    print("\nBy Market:")
    for market, data in results.items():
        status = "✅" if data['estimated_working'] >= 30 else "⚠️"
        print(f"  {market:12} | {data['estimated_working']:3d} tickers | {data['sample_rate']:.0%} success {status}")
    
    return results, UNIVERSE

def check_representativeness(universe):
    print("\n" + "=" * 80)
    print("REPRESENTATIVENESS ANALYSIS")
    print("=" * 80)
    
    print("\n📊 EQUITIES (US + HK + CN + SG)")
    print("-" * 40)
    
    concerns = []
    
    # US Analysis
    us_large_cap = len([t for t in universe['US']['tickers'] if t not in ['SPY', 'QQQ', 'IWM']])
    print(f"\nUS:")
    print(f"  - Large/Mega caps: {us_large_cap} (good coverage)")
    print(f"  - ETFs included: SPY, QQQ, IWM (sector exposure)")
    print(f"  - Missing: Small-caps, micro-caps")
    
    # HK Analysis
    print(f"\nHong Kong:")
    print(f"  - HSI constituents: ~50 tickers")
    print(f"  - Sectors: Property heavy, Finance, Tech (Tencent, Alibaba)")
    print(f"  - Missing: Small caps, GEM board stocks")
    concerns.append("HK: Heavy property weighting (~30%)")
    
    # CN Analysis
    print(f"\nChina:")
    print(f"  - ADRs only: {len(universe['CN']['tickers'])} tickers")
    print(f"  - Sectors: Tech, E-commerce, EVs dominant")
    print(f"  - Missing: A-shares (direct access not available via yfinance)")
    concerns.append("CN: ADRs only - no A-shares (80% of market cap missing)")
    
    # SG Analysis
    print(f"\nSingapore:")
    print(f"  - STI components: ~30 tickers")
    print(f"  - Heavy REITs weighting: ~40%")
    print(f"  - Missing: Small caps, ASEAN exposure")
    concerns.append("SG: REIT-heavy (40%), limited tech exposure")
    
    print("\n📊 FX")
    print("-" * 40)
    print(f"Pairs: {len(universe['FX']['tickers'])}")
    print(f"Coverage: G10 majors ✅, Asian pairs ✅, Crosses ✅")
    print(f"Limitation: yfinance provides delayed spot prices, not interbank rates")
    concerns.append("FX: Delayed prices, no interbank spreads")
    
    print("\n📊 Crypto")
    print("-" * 40)
    print(f"Assets: {len(universe['Crypto']['tickers'])}")
    print(f"Categories: Layer 1 (BTC, ETH, SOL), DeFi (UNI, AAVE, MKR)")
    print(f"Limitation: Only USD pairs, no funding rates, no perps")
    concerns.append("Crypto: No funding rate data, no perp prices")
    
    print("\n📊 Commodities")
    print("-" * 40)
    print(f"ETFs: {len(universe['Commodities']['tickers'])}")
    print(f"Coverage: Gold, Silver, Oil, Nat Gas, Agriculture")
    print(f"Limitation: ETF proxies, not futures (roll yield issues)")
    concerns.append("Commodities: ETF proxies only - need futures for accuracy")
    
    print("\n" + "=" * 80)
    print("CONCERNS")
    print("=" * 80)
    for i, concern in enumerate(concerns, 1):
        print(f"{i}. {concern}")
    
    return concerns

if __name__ == '__main__':
    results, universe = analyze_coverage()
    concerns = check_representativeness(universe)
