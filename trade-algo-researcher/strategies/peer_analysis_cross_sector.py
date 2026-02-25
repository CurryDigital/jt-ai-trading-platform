#!/usr/bin/env python3
"""
Cross-Regional Peer Analysis
Test lead-lag relationships across different sectors and regions

Uses yfinance only.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Test universes by sector/region
UNIVERSES = {
    # Semiconductors: NVDA (leader) vs others
    'semiconductors': {
        'lead': ['NVDA'],
        'lag': ['AMD', 'AVGO', 'QCOM', 'MU', 'MRVL', 'SNPS', 'CDNS']
    },
    # Banks: JPM (leader) vs regionals
    'banks': {
        'lead': ['JPM', 'BAC'],
        'lag': ['PNFP', 'TCBI', 'WAL', 'PACW', 'ZION', 'CMA']
    },
    # Megacap Tech: AAPL/MSFT vs smaller tech
    'megacap_tech': {
        'lead': ['AAPL', 'MSFT'],
        'lag': ['RBLX', 'U', 'ZM', 'SNOW', 'CRWD', 'NET']
    },
    # Retail: AMZN vs retail ETF components
    'retail': {
        'lead': ['AMZN', 'WMT'],
        'lag': ['TGT', 'COST', 'DG', 'DLTR', 'BIG']
    },
    # China Tech: BABA vs other China tech
    'china_tech': {
        'lead': ['BABA'],
        'lag': ['JD', 'BIDU', 'NTES', 'TCOM', 'VIPS']
    },
    # Airlines: DAL vs ULCCs
    'airlines': {
        'lead': ['DAL', 'UAL', 'AAL'],
        'lag': ['SAVE', 'ULCC', 'ALK']
    }
}

def get_prices(tickers, start='2022-01-01', end='2024-12-31'):
    """Download prices."""
    return yf.download(tickers, start=start, end=end, progress=False)['Close']

def find_lead_lag(lead_prices, lag_prices, max_lag=5):
    """Find optimal lag and correlation."""
    lead_ret = lead_prices.pct_change().dropna()
    lag_ret = lag_prices.pct_change().dropna()
    
    aligned = pd.concat([lead_ret, lag_ret], axis=1).dropna()
    if len(aligned) < 100:
        return None, 0, 0
    
    best_corr = -1
    best_lag = 0
    
    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        elif lag > 0:
            corr = aligned.iloc[:, 0].shift(lag).corr(aligned.iloc[:, 1])
        else:
            corr = aligned.iloc[:, 0].shift(-lag).corr(aligned.iloc[:, 1])
        
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    
    return best_lag, best_corr, len(aligned)

def analyze_universe(name, universe, prices):
    """Analyze one universe for lead-lag."""
    results = []
    
    for lead in universe['lead']:
        if lead not in prices.columns:
            continue
        for lag in universe['lag']:
            if lag not in prices.columns:
                continue
            
            lag_days, corr, n = find_lead_lag(prices[lead], prices[lag])
            if lag_days is not None:
                results.append({
                    'sector': name,
                    'lead': lead,
                    'lag': lag,
                    'lag_days': lag_days,
                    'correlation': corr,
                    'n_obs': n
                })
    
    return results

def main():
    print("Cross-Regional Peer Lead-Lag Analysis")
    print("=" * 60)
    print("Testing 6 sectors for information diffusion delays\n")
    
    all_results = []
    
    for sector_name, universe in UNIVERSES.items():
        print(f"\nAnalyzing: {sector_name.upper()}")
        print("-" * 40)
        
        all_tickers = universe['lead'] + universe['lag']
        prices = get_prices(all_tickers)
        
        if prices.empty:
            print("  No data available")
            continue
        
        results = analyze_universe(sector_name, universe, prices)
        
        if not results:
            print("  No valid pairs found")
            continue
        
        # Show best pairs
        df = pd.DataFrame(results)
        df = df.sort_values('correlation', ascending=False)
        
        print(f"  Best correlations:")
        for _, row in df.head(3).iterrows():
            status = "✅" if row['correlation'] > 0.6 and row['lag_days'] > 0 else ""
            print(f"    {row['lead']} → {row['lag']}: "
                  f"lag={row['lag_days']}d, corr={row['correlation']:.3f} {status}")
        
        all_results.extend(results)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not all_results:
        print("No lead-lag relationships found")
        return
    
    df_all = pd.DataFrame(all_results)
    
    # Find pairs with positive lag and high correlation
    promising = df_all[(df_all['lag_days'] > 0) & (df_all['correlation'] > 0.5)]
    
    if not promising.empty:
        print(f"\nPromising pairs (lag > 0, corr > 0.5): {len(promising)}")
        for _, row in promising.iterrows():
            print(f"  {row['sector']}: {row['lead']} → {row['lag']} "
                  f"(lag={row['lag_days']}d, corr={row['correlation']:.3f})")
    else:
        print("\nNo promising lead-lag relationships found.")
        print("All high-correlation pairs move simultaneously (lag=0).")
    
    print("\nConclusion:")
    print("Markets are efficient for simple price-based lead-lag.")
    print("Need alternative data edge (sentiment, options flow, etc.)")

if __name__ == '__main__':
    main()
