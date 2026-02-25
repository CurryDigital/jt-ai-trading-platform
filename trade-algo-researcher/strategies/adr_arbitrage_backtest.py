#!/usr/bin/env python3
"""
ADR-Local Arbitrage Backtest
Dual-listed stock deviation analysis

Uses yfinance only.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ADR to local mapping (simplified - assumes 1:1 or common ratio)
PAIRS = {
    'BABA': '9988.HK',    # Alibaba
    'TSM': '2330.TW',     # TSMC
    'JD': '9618.HK',      # JD.com
}

def get_prices(ticker, start='2020-01-01', end='2024-12-31'):
    """Download prices."""
    return yf.download(ticker, start=start, end=end, progress=False)['Close']

def analyze_deviation(adr_ticker, local_ticker):
    """Analyze ADR-local price deviation."""
    print(f"\nAnalyzing {adr_ticker} vs {local_ticker}...")
    
    try:
        adr = get_prices(adr_ticker)
        local = get_prices(local_ticker)
    except:
        print(f"  Error downloading {local_ticker}")
        return None
    
    if adr.empty or local.empty:
        return None
    
    # Align dates
    aligned = pd.concat([adr, local], axis=1).dropna()
    aligned.columns = ['adr', 'local']
    
    # Calculate deviation (simplified - assumes FX-adjusted)
    # Real implementation needs FX rate conversion
    deviation = (aligned['adr'] - aligned['local']) / aligned['local']
    
    return {
        'mean_dev': deviation.mean(),
        'std_dev': deviation.std(),
        'max_dev': deviation.abs().max(),
        'days_analyzed': len(aligned)
    }

def main():
    print("ADR-Local Arbitrage Analysis")
    print("="*50)
    print("Note: Simplified analysis (no FX adjustment)")
    print("Real implementation requires USD/HKD, USD/TWD rates")
    
    results = []
    for adr, local in PAIRS.items():
        result = analyze_deviation(adr, local)
        if result:
            results.append({
                'adr': adr,
                'local': local,
                **result
            })
    
    if not results:
        print("\nNo data available")
        return
    
    df = pd.DataFrame(results)
    print("\nResults:")
    print(df.to_string(index=False))
    
    print(f"\n{'='*50}")
    print("Key Findings:")
    for _, row in df.iterrows():
        if row['max_dev'] > 0.05:  # 5%
            print(f"✅ {row['adr']}: Max deviation {row['max_dev']:.1%} - Tradeable")
        else:
            print(f"⚠️ {row['adr']}: Max deviation {row['max_dev']:.1%} - Too small")
    
    print("\nNext: Implement with FX adjustment and intraday data")

if __name__ == '__main__':
    main()
