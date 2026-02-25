#!/usr/bin/env python3
"""
Trend Following Backtest
12-month time series momentum

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

UNIVERSE = ['SPY', 'QQQ', 'TLT', 'GLD', 'USO', 'UUP']

def get_prices(tickers, start='2015-01-01', end='2024-12-31'):
    return yf.download(tickers, start=start, end=end, progress=False)['Close']

def backtest_trend_following(prices, lookback=252, hold_months=1):
    """
    12-month momentum strategy.
    
    Rules:
    - Rank assets by 12-month return
    - Long top 3, short bottom 3
    - Rebalance monthly
    """
    returns_12m = prices.pct_change(lookback)
    
    trades = []
    for i in range(lookback, len(prices) - 21, 21):  # Monthly rebalance
        date = prices.index[i]
        momentum = returns_12m.iloc[i].dropna()
        
        if len(momentum) < 6:
            continue
        
        ranked = momentum.rank(ascending=False)
        longs = ranked[ranked <= 3].index.tolist()
        shorts = ranked[ranked > len(ranked) - 3].index.tolist()
        
        # Hold for 1 month
        entry = prices.iloc[i]
        exit_prices = prices.iloc[i + 21]
        
        long_pnl = 0
        for ticker in longs:
            if ticker in entry and ticker in exit_prices:
                long_pnl += (exit_prices[ticker] / entry[ticker] - 1) / len(longs)
        
        short_pnl = 0
        for ticker in shorts:
            if ticker in entry and ticker in exit_prices:
                short_pnl += (entry[ticker] / exit_prices[ticker] - 1) / len(shorts)
        
        total_pnl = (long_pnl + short_pnl) / 2
        
        trades.append({
            'date': date,
            'longs': ','.join(longs),
            'shorts': ','.join(shorts),
            'long_pnl': long_pnl,
            'short_pnl': short_pnl,
            'total_pnl': total_pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("Trend Following Backtest")
    print("="*50)
    print(f"Universe: {', '.join(UNIVERSE)}")
    
    print("\nDownloading data...")
    prices = get_prices(UNIVERSE)
    
    if prices.empty:
        print("Error: No data")
        return
    
    print("Backtesting 12-month momentum...")
    trades = backtest_trend_following(prices)
    
    if trades.empty:
        print("No trades")
        return
    
    returns = trades['total_pnl']
    sharpe = returns.mean() / returns.std() * np.sqrt(12) if returns.std() > 0 else 0
    win_rate = (returns > 0).mean()
    
    print(f"\nResults:")
    print(f"Trades (months): {len(trades)}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Avg Monthly Return: {returns.mean():.2%}")
    print(f"Sharpe: {sharpe:.2f}")
    
    trades.to_csv(RESULTS_DIR / 'trend_following_backtest.csv', index=False)
    print(f"\nSaved: results/trend_following_backtest.csv")
    
    print(f"\n{'='*50}")
    if sharpe >= 1.0:
        print("✅ PASS")
    else:
        print(f"⚠️ Sharpe {sharpe:.2f}")

if __name__ == '__main__':
    main()
