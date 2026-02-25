#!/usr/bin/env python3
"""
Put-Write Strategy Backtest - FIXED VERSION
Sell cash-secured puts on SPY (proxy simulation)

Uses yfinance only (proxy for options)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def get_prices(ticker='SPY', start='2015-01-01', end='2024-12-31'):
    """Get price data."""
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        return None
    # Flatten column names if multi-index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def backtest_put_write(prices, annual_premium=0.10, strike_otm=0.05):
    """
    Simulate put-write strategy.
    
    Assumptions:
    - Sell 30 DTE put at -5% OTM monthly
    - Collect ~1% premium (12% annually)
    - If assigned, hold stock
    """
    if prices is None or prices.empty:
        return pd.DataFrame()
    
    # Get monthly closes
    closes = prices['Close'].values.flatten() if hasattr(prices['Close'], 'values') else prices['Close'].values
    dates = prices.index
    
    # Create monthly series
    monthly_data = pd.DataFrame({'close': closes}, index=dates).resample('ME').last()
    monthly_returns = monthly_data['close'].pct_change().dropna()
    
    trades = []
    for date, monthly_ret in monthly_returns.items():
        # Simulate short put payoff
        put_premium = annual_premium / 12  # Monthly premium
        
        if monthly_ret > 0:
            # Stock up, put expires worthless
            pnl = put_premium
            outcome = 'expire_worthless'
        elif monthly_ret > -strike_otm:
            # Stock down but above strike
            pnl = put_premium
            outcome = 'expire_worthless'
        else:
            # Stock below strike, assigned
            loss = abs(monthly_ret) - put_premium
            pnl = -loss
            outcome = 'assigned'
        
        trades.append({
            'date': date,
            'spy_return': monthly_ret,
            'put_pnl': pnl,
            'outcome': outcome
        })
    
    return pd.DataFrame(trades)

def main():
    print("=" * 70)
    print("PUT-WRITE STRATEGY BACKTEST - FIXED")
    print("=" * 70)
    print("Note: Using proxy calculations (not real options data)")
    print("Assumes: 1% monthly premium, -5% OTM strike")
    print("=" * 70)
    
    prices = get_prices('SPY')
    
    if prices is None or prices.empty:
        print("❌ Error downloading data")
        return
    
    trades = backtest_put_write(prices)
    
    if trades.empty:
        print("❌ No trades generated")
        return
    
    returns = trades['put_pnl']
    win_rate = (returns > 0).mean()
    avg_return = returns.mean()
    
    # Calculate annual stats
    annual_return = avg_return * 12
    annual_vol = returns.std() * np.sqrt(12)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0
    
    # Max drawdown
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Downside months
    spy_monthly = trades['spy_return']
    spy_down_months = (spy_monthly < 0).sum()
    put_down_months = (returns < 0).sum()
    
    print(f"\n📊 MONTHLY RESULTS:")
    print(f"  Trades: {len(trades)}")
    print(f"  Win Rate: {win_rate:.1%}")
    print(f"  Avg Monthly Return: {avg_return:.2%}")
    print(f"  Months Assigned: {(trades['outcome'] == 'assigned').sum()}")
    
    print(f"\n📈 ANNUALIZED:")
    print(f"  Return: {annual_return:.1%}")
    print(f"  Volatility: {annual_vol:.1%}")
    print(f"  Sharpe: {sharpe:.2f}")
    print(f"  Max Drawdown: {max_dd:.1%}")
    
    print(f"\n🛡️ PROTECTION VS BUY-HOLD:")
    print(f"  SPY down months: {spy_down_months}")
    print(f"  Put-write down months: {put_down_months}")
    print(f"  Downside reduction: {1 - put_down_months/spy_down_months:.1%}" if spy_down_months > 0 else "  N/A")
    
    # Compare to buy-and-hold
    spy_annual = trades['spy_return'].mean() * 12
    print(f"\n📉 COMPARISON:")
    print(f"  Put-Write: {annual_return:.1%} return, {max_dd:.1%} max DD")
    print(f"  SPY Buy-Hold: {spy_annual:.1%} return")
    
    if sharpe > 0.8 and max_dd > -0.25:
        print(f"\n✅ STRATEGY VIABLE - Lower vol than buy-hold")
    else:
        print(f"\n⚠️ High drawdown risk in stress periods")
    
    trades.to_csv(RESULTS_DIR / 'put_write_spy.csv', index=False)
    print(f"\n💾 Saved to results/put_write_spy.csv")
    
    return trades

if __name__ == '__main__':
    main()
