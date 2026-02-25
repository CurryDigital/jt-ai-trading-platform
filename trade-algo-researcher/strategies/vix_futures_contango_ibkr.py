#!/usr/bin/env python3
"""
VIX Futures Contango Strategy
Short VIX futures when term structure in contango

Requires IBKR for VIX futures data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def get_vix_futures_ibkr():
    """
    Get VIX futures data from IBKR.
    
    Need:
    - Front month (VX1)
    - Second month (VX2)
    - Contango = VX2 > VX1 (typically 70% of time)
    """
    print("[INFO] VIX futures require IBKR connection")
    print("[INFO] Contracts: VX1 (front), VX2 (second month)")
    return None

def calculate_contango(vx1, vx2):
    """
    Calculate contango percentage.
    
    Contango = (VX2 - VX1) / VX1
    """
    return (vx2 - vx1) / vx1

def backtest_short_vol(vix_futures, threshold=0.05):
    """
    Short VIX futures when contango > 5%.
    
    This captures the roll yield as VX1 converges to spot VIX.
    """
    print("\n[STRATEGY] Short VIX in Contango")
    print("-" * 50)
    
    # Calculate contango
    contango = calculate_contango(vix_futures['VX1'], vix_futures['VX2'])
    
    trades = []
    for i in range(len(vix_futures) - 21):  # Hold 1 month
        if contango.iloc[i] < threshold:
            continue
        
        entry = vix_futures['VX1'].iloc[i]
        exit_p = vix_futures['VX1'].iloc[i + 21]
        
        # Short VIX futures
        pnl = (entry - exit_p) / entry
        
        trades.append({
            'date': vix_futures.index[i],
            'contango': contango.iloc[i],
            'vix_level': vix_futures['VX1'].iloc[i],
            'pnl': pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("VIX Futures Contango Strategy")
    print("=" * 50)
    
    print("\nSignal: Short VIX futures when VX2 > VX1 + 5%")
    print("Hold: 1 month (capture roll yield)")
    print("Target Sharpe: 1.0-1.4")
    
    print("\n[SETUP REQUIRED]")
    print("1. IBKR Gateway running")
    print("2. Futures market data subscription")
    print("3. Margin approval for futures")
    print("\nNote: VIX futures are cash-settled")
    print("Risk: Tail events (Feb 2018 volmageddon)")

if __name__ == '__main__':
    main()
