#!/usr/bin/env python3
"""
Opening Gap Fade Backtest - FIXED VERSION
Fade SPY opening gaps >0.5%

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

def get_ohlc(ticker='SPY', start='2019-01-01', end='2024-12-31'):
    """Get OHLC data."""
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        return None
    # Flatten column names if multi-index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def backtest_gap_fade(ohlc, gap_threshold=0.005):
    """
    Fade opening gaps.
    Gap up >0.5% → Short at open
    Gap down >0.5% → Long at open
    Exit at close (intraday fade assumption)
    """
    if ohlc is None or len(ohlc) < 20:
        return pd.DataFrame()
    
    # Extract values properly
    opens = ohlc['Open'].values.flatten() if hasattr(ohlc['Open'], 'values') else ohlc['Open'].values
    highs = ohlc['High'].values.flatten() if hasattr(ohlc['High'], 'values') else ohlc['High'].values
    lows = ohlc['Low'].values.flatten() if hasattr(ohlc['Low'], 'values') else ohlc['Low'].values
    closes = ohlc['Close'].values.flatten() if hasattr(ohlc['Close'], 'values') else ohlc['Close'].values
    
    trades = []
    for i in range(1, len(ohlc)):
        # Calculate overnight gap
        prev_close = closes[i-1]
        gap = (opens[i] - prev_close) / prev_close
        
        if abs(gap) < gap_threshold:
            continue
        
        entry = opens[i]
        
        # Simulate intraday fade
        # Assume 50% of gap fills by close on average
        if gap > 0:  # Gap up → Short (fade down)
            exit_p = closes[i]  # Close position
            pnl = (entry - exit_p) / entry  # Short profit
            direction = 'short'
            fill_pct = gap - (exit_p - prev_close) / prev_close
        else:  # Gap down → Long (fade up)
            exit_p = closes[i]
            pnl = (exit_p - entry) / entry  # Long profit
            direction = 'long'
            fill_pct = abs(gap) - abs((exit_p - prev_close) / prev_close)
        
        trades.append({
            'date': ohlc.index[i],
            'gap': gap,
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'direction': direction,
            'fill_pct': fill_pct
        })
    
    return pd.DataFrame(trades)

def main():
    print("=" * 70)
    print("OPENING GAP FADE BACKTEST - FIXED")
    print("=" * 70)
    print("Signal: Gap >0.5% from previous close")
    print("Trade: Fade the gap (long gaps down, short gaps up)")
    print("Exit: Same day close")
    print("=" * 70)
    
    results_summary = []
    
    for ticker in ['SPY', 'QQQ', 'IWM', 'AAPL', 'TSLA']:
        print(f"\n{ticker}:")
        try:
            ohlc = get_ohlc(ticker)
            
            if ohlc is None or ohlc.empty:
                print("  ❌ No data")
                continue
            
            trades = backtest_gap_fade(ohlc)
            
            if trades.empty:
                print("  ⚠️ No trades")
                continue
            
            returns = trades['pnl']
            win_rate = (returns > 0).mean()
            avg_return = returns.mean()
            total_return = (1 + returns).prod() - 1
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            avg_fill = trades['fill_pct'].mean()
            
            print(f"  Trades: {len(trades)}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Avg Return: {avg_return:.2%}")
            print(f"  Total Return: {total_return:.1%}")
            print(f"  Sharpe: {sharpe:.2f}")
            print(f"  Avg Gap Fill: {avg_fill:.2%}")
            
            if win_rate >= 0.55:
                print(f"  ✅ PROMISING")
            else:
                print(f"  ⚠️ Win rate {win_rate:.1%} < 55%")
            
            results_summary.append({
                'ticker': ticker,
                'trades': len(trades),
                'win_rate': win_rate,
                'sharpe': sharpe,
                'avg_return': avg_return,
                'avg_fill': avg_fill
            })
            
            trades.to_csv(RESULTS_DIR / f'gap_fade_{ticker}.csv', index=False)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
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
            print("\n⚠️ Strategy underperforms - gap fade may not work in current market")
    
    return summary_df

if __name__ == '__main__':
    main()
