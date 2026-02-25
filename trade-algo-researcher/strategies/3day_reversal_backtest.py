#!/usr/bin/env python3
"""
3-Day Reversal Backtest - FIXED VERSION
Buy after 3 consecutive down days with volume confirmation

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

def get_ohlcv(ticker='SPY', start='2019-01-01', end='2024-12-31'):
    """Get OHLCV data."""
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        return None
    # Flatten column names if multi-index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def backtest_3day_reversal(prices, max_decline=0.05, min_volume_spike=1.3):
    """
    Buy after 3 consecutive down days.
    Hold for 3 days.
    """
    if prices is None or len(prices) < 50:
        return pd.DataFrame()
    
    # Calculate returns
    closes = prices['Close'].values.flatten() if hasattr(prices['Close'], 'values') else prices['Close'].values
    volumes = prices['Volume'].values.flatten() if hasattr(prices['Volume'], 'values') else prices['Volume'].values
    
    returns = pd.Series(closes).pct_change().values
    avg_volume = pd.Series(volumes).rolling(20).mean().values
    
    trades = []
    for i in range(20, len(prices) - 4):
        # Check 3 consecutive down days
        down_1 = returns[i-2] < 0
        down_2 = returns[i-1] < 0  
        down_3 = returns[i] < 0
        
        if not (down_1 and down_2 and down_3):
            continue
        
        # Check total decline over 3 days
        decline_3d = (closes[i] - closes[i-3]) / closes[i-3]
        
        if decline_3d > -max_decline:  # Must decline more than threshold
            continue
        
        # Volume confirmation
        volume_spike = volumes[i] / avg_volume[i] if avg_volume[i] > 0 else 1
        if volume_spike < min_volume_spike:
            continue
        
        # Entry/exit
        entry_price = closes[i+1]  # Next day open
        exit_price = closes[i+4]   # 3 days later
        pnl = (exit_price - entry_price) / entry_price
        
        trades.append({
            'date': prices.index[i],
            'ticker': prices.index.name if hasattr(prices.index, 'name') else 'Unknown',
            'entry_price': entry_price,
            'exit_price': exit_price,
            'decline_3d': decline_3d,
            'volume_spike': volume_spike,
            'pnl': pnl
        })
    
    return pd.DataFrame(trades)

def main():
    print("=" * 70)
    print("3-DAY REVERSAL BACKTEST - FIXED")
    print("=" * 70)
    print("Signal: 3 down days + >5% decline + volume spike >1.3x")
    print("Hold: 3 days")
    print("=" * 70)
    
    results_summary = []
    
    for ticker in ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'TSLA']:
        print(f"\n{ticker}:")
        try:
            prices = get_ohlcv(ticker)
            
            if prices is None or prices.empty:
                print("  ❌ No data")
                continue
            
            trades = backtest_3day_reversal(prices)
            
            if trades.empty:
                print("  ⚠️ No trades")
                continue
            
            returns = trades['pnl']
            win_rate = (returns > 0).mean()
            avg_return = returns.mean()
            total_return = (1 + returns).prod() - 1
            sharpe = returns.mean() / returns.std() * np.sqrt(252/3) if returns.std() > 0 else 0
            
            print(f"  Trades: {len(trades)}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Avg Return: {avg_return:.2%}")
            print(f"  Total Return: {total_return:.1%}")
            print(f"  Sharpe: {sharpe:.2f}")
            
            if win_rate >= 0.55:
                print(f"  ✅ PROMISING")
            else:
                print(f"  ⚠️ Win rate {win_rate:.1%} < 55%")
            
            results_summary.append({
                'ticker': ticker,
                'trades': len(trades),
                'win_rate': win_rate,
                'sharpe': sharpe,
                'avg_return': avg_return
            })
            
            # Save results
            trades.to_csv(RESULTS_DIR / f'3day_reversal_{ticker}.csv', index=False)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    summary_df = pd.DataFrame(results_summary)
    if not summary_df.empty:
        print(summary_df.to_string(index=False))
        
        avg_win_rate = summary_df['win_rate'].mean()
        avg_sharpe = summary_df['sharpe'].mean()
        print(f"\nAverage Win Rate: {avg_win_rate:.1%}")
        print(f"Average Sharpe: {avg_sharpe:.2f}")
        
        if avg_win_rate >= 0.55 and avg_sharpe > 0.6:
            print("\n🎯 STRATEGY SHOWS PROMISE - Consider validation")
        else:
            print("\n⚠️ Strategy underperforms - needs refinement")
    
    return summary_df

if __name__ == '__main__':
    main()
