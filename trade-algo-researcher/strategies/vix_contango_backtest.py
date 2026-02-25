#!/usr/bin/env python3
"""
VIX Contango Roll Yield Backtest
Short VXX when VIX futures in contango

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

def get_vix_data(start='2015-01-01', end='2024-12-31'):
    """Download VIX and VXX data."""
    # VIX index
    vix = yf.download('^VIX', start=start, end=end, progress=False)['Close']
    # VXX ETN (short-term VIX futures)
    vxx = yf.download('VXX', start=start, end=end, progress=False)['Close']
    return vix, vxx

def estimate_contango(vix_prices):
    """
    Estimate contango using VIX level as proxy.
    Higher VIX = higher roll cost typically.
    Simplified: Assume contango when VIX < 20 (stable regime)
    """
    return vix_prices < 20  # Simplified proxy

def backtest_vix_contango(vix, vxx):
    """
    Short VXX when VIX is in contango (VIX < 20, stable regime).
    """
    contango = estimate_contango(vix)
    
    trades = []
    for i in range(len(vxx) - 21):
        if not contango.iloc[i].item():
            continue
        
        entry = vxx.iloc[i]
        exit_price = vxx.iloc[i + 21]  # Hold 1 month
        
        # Short VXX
        pnl = (entry - exit_price) / entry
        
        trades.append({
            'date': vxx.index[i],
            'vix_level': vix.iloc[i],
            'entry_vxx': entry,
            'exit_vxx': exit_price,
            'pnl': pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("VIX Contango Roll Yield Backtest")
    print("="*50)
    print("Signal: Short VXX when VIX < 20 (contango)")
    
    print("\nDownloading ^VIX, VXX...")
    vix, vxx = get_vix_data()
    
    if vix.empty or vxx.empty:
        print("Error: No data")
        return
    
    print(f"Data: {len(vix)} days")
    
    print("\nBacktesting...")
    trades = backtest_vix_contango(vix, vxx)
    
    if trades.empty:
        print("No trades (VIX always > 20?)")
        return
    
    returns = trades['pnl']
    sharpe = returns.mean() / returns.std() * np.sqrt(12) if returns.std() > 0 else 0
    win_rate = (returns > 0).mean()
    
    print(f"\nResults:")
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Avg Return: {returns.mean():.2%}")
    print(f"Sharpe: {sharpe:.2f}")
    
    trades.to_csv(RESULTS_DIR / 'vix_contango_backtest.csv', index=False)
    print(f"\nSaved: results/vix_contango_backtest.csv")
    
    print(f"\n{'='*50}")
    if sharpe >= 1.0:
        print("✅ PASS")
    else:
        print(f"⚠️ Sharpe {sharpe:.2f}")
    
    print("\nNote: Contango estimation simplified. Real implementation")
    print("would use VIX futures term structure (1st vs 2nd month).")

if __name__ == '__main__':
    main()
