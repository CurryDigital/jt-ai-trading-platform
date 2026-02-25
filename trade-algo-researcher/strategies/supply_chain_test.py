#!/usr/bin/env python3
"""
Supply Chain Test - NVDA vs AMD
Quick test of customer-supplier relationship

Uses yfinance only.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def get_prices(ticker, start='2019-01-01', end='2024-12-31'):
    return yf.download(ticker, start=start, end=end, progress=False)['Close']

def analyze_lead_lag(lead, lag, max_lag=5):
    """Analyze lead-lag relationship."""
    lead_ret = lead.pct_change().dropna()
    lag_ret = lag.pct_change().dropna()
    
    aligned = pd.concat([lead_ret, lag_ret], axis=1).dropna()
    
    if len(aligned) < 100:
        return None
    
    best_corr = -1
    best_lag = 0
    
    for lag_days in range(-max_lag, max_lag + 1):
        if lag_days == 0:
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        elif lag_days > 0:
            corr = aligned.iloc[:, 0].shift(lag_days).corr(aligned.iloc[:, 1])
        else:
            corr = aligned.iloc[:, 0].shift(-lag_days).corr(aligned.iloc[:, 1])
        
        if corr > best_corr:
            best_corr = corr
            best_lag = lag_days
    
    return best_lag, best_corr

def main():
    print("Supply Chain Test: NVDA vs AMD")
    print("=" * 50)
    print("Testing if NVDA leads AMD (both GPU players)\n")
    
    nvda = get_prices('NVDA')
    amd = get_prices('AMD')
    
    if nvda.empty or amd.empty:
        print("Error downloading data")
        return
    
    result = analyze_lead_lag(nvda, amd)
    
    if result:
        lag, corr = result
        print(f"Best lag: {lag} days")
        print(f"Correlation: {corr:.3f}")
        
        if lag > 0 and corr > 0.6:
            print(f"\n✅ NVDA leads AMD by {lag} days (corr={corr:.3f})")
            print("Potential supply chain signal!")
        elif lag == 0:
            print(f"\n❌ Simultaneous movement (lag=0)")
            print("Market too efficient - no tradable lag")
        else:
            print(f"\n⚠️ Weak or negative relationship")
    
    # Test other pairs
    print("\n" + "=" * 50)
    print("Testing other pairs:\n")
    
    pairs = [
        ('MSFT', 'NVDA'),  # Cloud → GPU
        ('AMZN', 'UPS'),   # E-commerce → Logistics
        ('NFLX', 'PARA'),  # Streaming → Studio
    ]
    
    for lead_ticker, lag_ticker in pairs:
        try:
            lead = get_prices(lead_ticker)
            lag = get_prices(lag_ticker)
            
            if lead.empty or lag.empty:
                continue
            
            result = analyze_lead_lag(lead, lag)
            if result:
                lag_days, corr = result
                status = "✅" if lag_days > 0 and corr > 0.5 else "❌"
                print(f"{lead_ticker} → {lag_ticker}: lag={lag_days}d, corr={corr:.3f} {status}")
        except:
            continue

if __name__ == '__main__':
    main()
