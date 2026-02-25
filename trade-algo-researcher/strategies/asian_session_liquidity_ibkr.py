#!/usr/bin/env python3
"""
Asian Session Liquidity Gap Backtest
Fade Tokyo session gaps during London/NY

Requires IBKR for hourly forex data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

PAIRS = ['USDJPY', 'AUDUSD', 'EURJPY']

def get_hourly_data_ibkr(pairs):
    """
    Get hourly forex data from IBKR.
    
    IBKR provides:
    - Hourly bars for forex
    - Tokyo session: 19:00-04:00 ET (previous day)
    - London session: 03:00-12:00 ET
    - NY session: 08:00-17:00 ET
    """
    print("[INFO] Hourly data requires IBKR connection")
    print("[INFO] Request 1-hour bars for:", ', '.join(pairs))
    return None

def detect_tokyo_gap(hourly_data):
    """
    Detect large moves in Tokyo session.
    
    Tokyo session: 19:00 ET - 04:00 ET next day
    """
    gaps = []
    
    for date, day_data in hourly_data.groupby(hourly_data.index.date):
        # Tokyo hours (simplified)
        tokyo = day_data.between_time('19:00', '23:59')
        
        if len(tokyo) < 4:  # Need at least 4 hours
            continue
        
        tokyo_return = (tokyo['close'].iloc[-1] / tokyo['open'].iloc[0] - 1)
        
        if abs(tokyo_return) > 0.005:  # >0.5% move
            gaps.append({
                'date': date,
                'pair': day_data.name if hasattr(day_data, 'name') else 'unknown',
                'tokyo_return': tokyo_return,
                'direction': 'up' if tokyo_return > 0 else 'down'
            })
    
    return pd.DataFrame(gaps)

def backtest_fade_strategy(hourly_data, gaps_df):
    """
    Fade Tokyo gaps in London session.
    
    Entry: 04:00 ET (Tokyo close)
    Exit: 12:00 ET (London close)
    
    Signal: If Tokyo up >0.5%, short. If down >0.5%, long.
    """
    trades = []
    
    for _, gap in gaps_df.iterrows():
        date = gap['date']
        tokyo_return = gap['tokyo_return']
        
        # Get London session data
        day_data = hourly_data[hourly_data.index.date == date]
        london = day_data.between_time('04:00', '12:00')
        
        if len(london) < 4:
            continue
        
        entry = london['open'].iloc[0]
        exit_p = london['close'].iloc[-1]
        
        # Fade the gap
        if tokyo_return > 0:  # Tokyo up → short
            pnl = (entry - exit_p) / entry
        else:  # Tokyo down → long
            pnl = (exit_p - entry) / entry
        
        trades.append({
            'date': date,
            'tokyo_move': tokyo_return,
            'pnl': pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("Asian Session Liquidity Gap Strategy")
    print("=" * 50)
    print("Pairs:", ', '.join(PAIRS))
    
    print("\n[SETUP REQUIRED]")
    print("1. Start IBKR Gateway")
    print("2. Subscribe to forex data (usually free)")
    print("3. Request hourly bars for:", ', '.join(PAIRS))
    print("\nTarget: 1.5-2.0 Sharpe")
    print("Edge: Retail sentiment overreaction in thin Tokyo hours")

if __name__ == '__main__':
    main()
