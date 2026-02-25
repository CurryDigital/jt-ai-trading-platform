#!/usr/bin/env python3
"""
Gold/Silver Ratio Rotation Backtest
Trade Gold/Silver ratio mean reversion

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

def get_prices(tickers, start='2019-01-01', end='2024-12-31'):
    """Download prices from yfinance."""
    return yf.download(tickers, start=start, end=end, progress=False)['Close']

def backtest_ratio_strategy(gold_prices, silver_prices, z_threshold=1.5):
    """
    Backtest Gold/Silver ratio mean reversion.
    
    Signal:
    - Ratio > mean + z_threshold*std → Short gold, long silver (ratio falls)
    - Ratio < mean - z_threshold*std → Long gold, short silver (ratio rises)
    """
    ratio = gold_prices / silver_prices
    ratio_mean = ratio.rolling(252).mean()
    ratio_std = ratio.rolling(252).std()
    z_score = (ratio - ratio_mean) / ratio_std
    
    trades = []
    for i in range(252, len(ratio) - 21):  # Start after 1 year lookback
        z = z_score.iloc[i]
        
        if abs(z) < z_threshold:
            continue
        
        # Entry
        entry_gold = gold_prices.iloc[i]
        entry_silver = silver_prices.iloc[i]
        
        # Exit 21 days later (1 month)
        exit_gold = gold_prices.iloc[i + 21]
        exit_silver = silver_prices.iloc[i + 21]
        
        if z > z_threshold:  # Ratio high → short gold, long silver
            gold_pnl = (entry_gold - exit_gold) / entry_gold
            silver_pnl = (exit_silver - entry_silver) / entry_silver
        else:  # Ratio low → long gold, short silver
            gold_pnl = (exit_gold - entry_gold) / entry_gold
            silver_pnl = (entry_silver - exit_silver) / entry_silver
        
        total_pnl = (gold_pnl + silver_pnl) / 2
        
        trades.append({
            'date': ratio.index[i],
            'ratio': ratio.iloc[i],
            'z_score': z,
            'gold_pnl': gold_pnl,
            'silver_pnl': silver_pnl,
            'total_pnl': total_pnl,
            'direction': 'short_ratio' if z > 0 else 'long_ratio'
        })
    
    return pd.DataFrame(trades)

def main():
    print("Gold/Silver Ratio Rotation Backtest")
    print("="*50)
    
    print("Downloading GLD, SLV...")
    prices = get_prices(['GLD', 'SLV'])
    
    if prices.empty or 'GLD' not in prices or 'SLV' not in prices:
        print("Error: Could not download data")
        return
    
    print(f"\nBacktesting...")
    trades = backtest_ratio_strategy(prices['GLD'], prices['SLV'])
    
    if trades.empty:
        print("No trades generated")
        return
    
    # Metrics
    returns = trades['total_pnl']
    sharpe = returns.mean() / returns.std() * np.sqrt(12) if returns.std() > 0 else 0
    win_rate = (returns > 0).mean()
    
    print(f"\nResults:")
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Avg Return: {returns.mean():.2%}")
    print(f"Sharpe: {sharpe:.2f}")
    
    # Save
    trades.to_csv(RESULTS_DIR / 'gold_silver_ratio_backtest.csv', index=False)
    print(f"\nSaved to: results/gold_silver_ratio_backtest.csv")
    
    # Validation
    print(f"\n{'='*50}")
    if sharpe >= 0.8:
        print("✅ PASS: Sharpe >= 0.8")
    else:
        print(f"⚠️ LOW: Sharpe {sharpe:.2f} < 0.8")

if __name__ == '__main__':
    main()
