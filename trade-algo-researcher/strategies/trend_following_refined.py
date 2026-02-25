#!/usr/bin/env python3
"""
Trend Following Backtest - REFINED
Multiple lookbacks + volatility scaling

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

UNIVERSE = ['SPY', 'QQQ', 'TLT', 'GLD', 'IWM', 'EFA']

def get_prices(tickers, start='2015-01-01', end='2024-12-31'):
    return yf.download(tickers, start=start, end=end, progress=False)['Close']

def backtest_momentum(prices, lookback=126, vol_scale=True, hold_months=1):
    """
    Momentum with volatility scaling.
    
    - lookback: 126d (6mo), 189d (9mo), 252d (12mo)
    - vol_scale: Size by inverse volatility
    - Top 2 / Bottom 2 instead of 3/3
    """
    returns_lookback = prices.pct_change(lookback)
    volatility = prices.pct_change().rolling(21).std() * np.sqrt(252)
    
    trades = []
    for i in range(lookback, len(prices) - 21, 21):
        date = prices.index[i]
        mom = returns_lookback.iloc[i].dropna()
        vol = volatility.iloc[i].dropna()
        
        if len(mom) < 4:
            continue
        
        # Risk-adjusted momentum
        if vol_scale:
            risk_adj = mom / vol
            ranked = risk_adj.rank(ascending=False)
        else:
            ranked = mom.rank(ascending=False)
        
        longs = ranked[ranked <= 2].index.tolist()
        shorts = ranked[ranked > len(ranked) - 2].index.tolist()
        
        entry = prices.iloc[i]
        exit_prices = prices.iloc[i + 21]
        
        long_pnl = np.mean([(exit_prices[t]/entry[t]-1) for t in longs if t in entry and t in exit_prices])
        short_pnl = np.mean([(entry[t]/exit_prices[t]-1) for t in shorts if t in entry and t in exit_prices])
        
        total_pnl = (long_pnl + short_pnl) / 2
        
        trades.append({
            'date': date,
            'lookback': lookback,
            'longs': ','.join(longs),
            'shorts': ','.join(shorts),
            'total_pnl': total_pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("Trend Following - REFINED")
    print("="*50)
    
    print("Downloading data...")
    prices = get_prices(UNIVERSE)
    
    if prices.empty:
        print("Error: No data")
        return
    
    results = []
    for lookback in [63, 126, 189, 252]:  # 3, 6, 9, 12 months
        for vol_scale in [False, True]:
            trades = backtest_momentum(prices, lookback, vol_scale)
            if trades.empty:
                continue
            
            returns = trades['total_pnl']
            sharpe = returns.mean() / returns.std() * np.sqrt(12) if returns.std() > 0 else 0
            win_rate = (returns > 0).mean()
            
            results.append({
                'lookback': lookback,
                'vol_scale': vol_scale,
                'sharpe': sharpe,
                'win_rate': win_rate,
                'trades': len(trades)
            })
            
            label = f"{lookback}d {'+vol' if vol_scale else ''}"
            print(f"{label:12} Sharpe: {sharpe:.2f}  Win: {win_rate:.1%}")
    
    df = pd.DataFrame(results)
    best = df.loc[df['sharpe'].idxmax()]
    
    print(f"\n{'='*50}")
    print(f"BEST: {best['lookback']}d {'+vol_scale' if best['vol_scale'] else ''}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    
    if best['sharpe'] >= 1.0:
        print("✅ PASS")
    else:
        print(f"⚠️ Below target (1.0)")

if __name__ == '__main__':
    main()
