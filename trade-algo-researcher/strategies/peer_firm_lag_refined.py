#!/usr/bin/env python3
"""
Peer Firm Lag - REFINED
Use US E&Ps instead of Chinese ADRs (delisted)

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

# US Majors -> US E&Ps (all liquid on yfinance)
LEADERS = ['XOM', 'CVX', 'COP']  # Exxon, Chevron, Conoco
LAGGARDS = ['OXY', 'DVN', 'MRO', 'FANG', 'PXD']  # E&Ps

def get_prices(tickers, start='2019-01-01', end='2024-12-31'):
    return yf.download(tickers, start=start, end=end, progress=False)['Close']

def calculate_correlation(leader, laggard, prices, max_lag=5):
    """Find optimal lag and correlation."""
    l_ret = prices[leader].pct_change().dropna()
    g_ret = prices[laggard].pct_change().dropna()
    
    aligned = pd.concat([l_ret, g_ret], axis=1).dropna()
    
    corrs = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            corrs[lag] = aligned[leader].corr(aligned[laggard])
        elif lag > 0:
            corrs[lag] = aligned[leader].shift(lag).corr(aligned[laggard])
        else:
            corrs[lag] = aligned[leader].shift(-lag).corr(aligned[laggard])
    
    best_lag = max(corrs, key=corrs.get)
    return best_lag, corrs[best_lag]

def backtest_strategy(leader, laggard, prices, threshold=0.03, hold_days=3):
    """Trade when leader moves >threshold."""
    l_ret = prices[leader].pct_change()
    
    trades = []
    for i in range(len(prices) - hold_days):
        if abs(l_ret.iloc[i]) < threshold:
            continue
        
        direction = 1 if l_ret.iloc[i] > 0 else -1
        entry = prices[laggard].iloc[i]
        exit_p = prices[laggard].iloc[i + hold_days]
        pnl = (exit_p / entry - 1) * direction
        
        trades.append({'date': prices.index[i], 'pnl': pnl})
    
    return pd.DataFrame(trades)

def main():
    print("Peer Firm Lag - REFINED (US E&Ps)")
    print("="*50)
    
    all_tickers = LEADERS + LAGGARDS
    print(f"Downloading {len(all_tickers)} tickers...")
    prices = get_prices(all_tickers)
    
    if prices.empty:
        print("Error: No data")
        return
    
    # Correlation analysis
    print("\nLead-Lag Analysis:")
    print("-"*50)
    
    results = []
    for leader in LEADERS:
        if leader not in prices:
            continue
        for laggard in LAGGARDS:
            if laggard not in prices:
                continue
            
            lag, corr = calculate_correlation(leader, laggard, prices)
            results.append({
                'lead': leader,
                'lag': laggard,
                'best_lag': lag,
                'correlation': corr
            })
            
            if corr > 0.3:
                print(f"{leader} → {laggard}: lag={lag}d, corr={corr:.3f}")
    
    # Backtest best pair
    df = pd.DataFrame(results)
    if not df.empty:
        best = df.loc[df['correlation'].idxmax()]
        print(f"\nBest pair: {best['lead']} → {best['lag']} (corr={best['correlation']:.3f})")
        
        trades = backtest_strategy(best['lead'], best['lag'], prices)
        if not trades.empty:
            sharpe = trades['pnl'].mean() / trades['pnl'].std() * np.sqrt(252/3)
            win_rate = (trades['pnl'] > 0).mean()
            
            print(f"\nBacktest:")
            print(f"Trades: {len(trades)}")
            print(f"Win Rate: {win_rate:.1%}")
            print(f"Sharpe: {sharpe:.2f}")
            
            if sharpe >= 0.8:
                print("✅ PASS")
            else:
                print(f"⚠️ Sharpe {sharpe:.2f}")

if __name__ == '__main__':
    main()
