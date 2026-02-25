#!/usr/bin/env python3
"""
Peer Firm Lag Backtest
Oil majors → nationals/services lead-lag analysis

Uses yfinance only.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Universe
MAJORS = ['XOM', 'CVX']  # Exxon, Chevron (US liquid)
NATIONALS = ['SNP', 'PTR']  # Sinopec, PetroChina (ADR)
SERVICES = ['SLB', 'HAL']  # Schlumberger, Halliburton

def get_prices(tickers, start='2019-01-01', end='2024-12-31'):
    """Download prices from yfinance."""
    data = yf.download(tickers, start=start, end=end, progress=False)['Close']
    return data

def calculate_lead_lag(lead_ticker, lag_ticker, prices, max_lag=5):
    """Calculate cross-correlation at different lags."""
    lead_returns = prices[lead_ticker].pct_change().dropna()
    lag_returns = prices[lag_ticker].pct_change().dropna()
    
    # Align dates
    aligned = pd.concat([lead_returns, lag_returns], axis=1).dropna()
    
    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # Lead moves before lag
            corr = aligned[lead_ticker].shift(-lag).corr(aligned[lag_ticker])
        elif lag > 0:
            # Lag moves after lead
            corr = aligned[lead_ticker].shift(lag).corr(aligned[lag_ticker])
        else:
            corr = aligned[lead_ticker].corr(aligned[lag_ticker])
        correlations[lag] = corr
    
    return correlations

def simulate_strategy(lead_ticker, lag_ticker, prices, threshold=0.02, hold_days=3):
    """Simulate peer lag strategy."""
    lead_returns = prices[lead_ticker].pct_change()
    
    trades = []
    for i in range(len(prices) - hold_days):
        if lead_returns.iloc[i] > threshold:
            # Lead up → Lag should follow
            entry = prices[lag_ticker].iloc[i]
            exit_price = prices[lag_ticker].iloc[i + hold_days]
            pnl = (exit_price / entry - 1)
            trades.append({'date': prices.index[i], 'pnl': pnl, 'direction': 'long'})
        elif lead_returns.iloc[i] < -threshold:
            # Lead down → Short lag
            entry = prices[lag_ticker].iloc[i]
            exit_price = prices[lag_ticker].iloc[i + hold_days]
            pnl = -(exit_price / entry - 1)  # Short
            trades.append({'date': prices.index[i], 'pnl': pnl, 'direction': 'short'})
    
    return pd.DataFrame(trades)

def main():
    print("Peer Firm Lag Backtest")
    print("="*50)
    
    # Download data
    all_tickers = MAJORS + NATIONALS + SERVICES
    print(f"Downloading data for {len(all_tickers)} tickers...")
    prices = get_prices(all_tickers)
    
    if prices.empty:
        print("Error: No data downloaded")
        return
    
    # Lead-lag analysis
    print("\nLead-Lag Correlations:")
    print("-"*50)
    
    for major in MAJORS:
        if major not in prices.columns:
            continue
        for national in NATIONALS:
            if national not in prices.columns:
                continue
            
            corr = calculate_lead_lag(major, national, prices)
            best_lag = max(corr, key=corr.get)
            
            print(f"{major} → {national}: Best lag={best_lag}d, corr={corr[best_lag]:.3f}")
    
    # Strategy backtest
    print("\nStrategy Backtest (XOM → SNP):")
    print("-"*50)
    
    if 'XOM' in prices.columns and 'SNP' in prices.columns:
        trades = simulate_strategy('XOM', 'SNP', prices)
        if not trades.empty:
            sharpe = trades['pnl'].mean() / trades['pnl'].std() * np.sqrt(252/3)
            win_rate = (trades['pnl'] > 0).mean()
            
            print(f"Trades: {len(trades)}")
            print(f"Win Rate: {win_rate:.1%}")
            print(f"Avg PnL: {trades['pnl'].mean():.3%}")
            print(f"Sharpe: {sharpe:.2f}")
            
            # Save
            trades.to_csv(RESULTS_DIR / 'peer_firm_lag_backtest.csv')

if __name__ == '__main__':
    main()
