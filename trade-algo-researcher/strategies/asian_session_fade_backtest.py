#!/usr/bin/env python3
"""
Asian Session Liquidity Fade Backtest
Test fading large moves during illiquid Asian hours
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
from datetime import datetime, time
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def get_hourly_data(ticker, start='2022-01-01', end='2024-12-31'):
    """Get hourly data for intraday testing."""
    try:
        # Try to get hourly data (limited to 730 days by yfinance)
        data = yf.download(ticker, start=start, end=end, interval='1h', progress=False)
        if data.empty or len(data) < 100:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

def backtest_asian_session_fade(data, ticker, threshold=0.003, hold_hours=8):
    """
    Backtest Asian session fade strategy.
    
    Simplified version: Use daily data proxy
    - Calculate overnight/early session move
    - Fade large moves during next session
    """
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    
    # For daily data, proxy Asian session as "overnight" move
    # Entry: If large gap from previous close
    # Exit: Reversion during regular hours
    
    trades = []
    for i in range(5, len(closes) - 1):
        # Calculate overnight gap (proxy for Asian session move)
        overnight_gap = (data['Open'].iloc[i] - closes[i-1]) / closes[i-1]
        
        if abs(overnight_gap) < threshold:
            continue
        
        # Entry at open (after Asian session)
        entry = data['Open'].iloc[i]
        
        # Exit at close (end of US session)
        exit_p = closes[i]
        
        # Fade the gap
        if overnight_gap > 0:  # Gap up - expect fade down
            pnl = (entry - exit_p) / entry  # Short
        else:  # Gap down - expect fade up
            pnl = (exit_p - entry) / entry  # Long
        
        trades.append({
            'date': data.index[i],
            'overnight_gap': overnight_gap,
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl
        })
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252) if df['pnl'].std() > 0 else 0,
        'avg_gap': df['overnight_gap'].abs().mean()
    }

def main():
    print("=" * 80)
    print("ASIAN SESSION LIQUIDITY FADE BACKTEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Proxy: Using overnight gaps as Asian session moves")
    print("Threshold: >0.3% move")
    print("=" * 80)
    
    # Test on FX proxies and major indices
    tickers = [
        ('USDJPY=X', 'USD/JPY'),
        ('EURUSD=X', 'EUR/USD'),
        ('GBPUSD=X', 'GBP/USD'),
        ('AUDUSD=X', 'AUD/USD'),
        ('SPY', 'S&P 500'),
        ('QQQ', 'Nasdaq 100'),
        ('IWM', 'Russell 2000'),
        ('GLD', 'Gold'),
        ('USO', 'Oil'),
    ]
    
    results = []
    
    for ticker, name in tickers:
        print(f"\n{name}: {ticker}")
        
        data = get_hourly_data(ticker)
        if data is None:
            # Try daily as fallback
            try:
                data = yf.download(ticker, start='2019-01-01', end='2024-12-31', progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                    print(f"  Using daily data ({len(data)} days)")
            except:
                print(f"  ❌ No data")
                continue
        else:
            print(f"  Using hourly data ({len(data)} hours)")
        
        result = backtest_asian_session_fade(data, ticker)
        
        if result and result['trades'] >= 10:
            print(f"  Trades: {result['trades']}")
            print(f"  Win Rate: {result['win_rate']:.1%}")
            print(f"  Avg Return: {result['avg_return']:.2%}")
            print(f"  Sharpe: {result['sharpe']:.2f}")
            print(f"  Avg Gap: {result['avg_gap']:.2%}")
            
            if result['win_rate'] >= 0.55:
                print(f"  ✅ VIABLE")
            else:
                print(f"  ⚠️ Win rate {result['win_rate']:.1%} < 55%")
            
            results.append(result)
        else:
            print(f"  ⚠️ Insufficient trades")
    
    # Summary
    if results:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        df = pd.DataFrame(results)
        print(f"\nAssets tested: {len(df)}")
        print(f"Passing (WR > 55%): {(df['win_rate'] > 0.55).sum()}")
        
        if len(df) > 0:
            print(f"\nAverage metrics:")
            print(f"  Win Rate: {df['win_rate'].mean():.1%}")
            print(f"  Sharpe: {df['sharpe'].mean():.2f}")
            print(f"  Avg Return: {df['avg_return'].mean():.2%}")
        
        print("\nBest performers:")
        best = df.nlargest(3, 'win_rate')
        for _, row in best.iterrows():
            print(f"  {row['ticker']}: {row['win_rate']:.1%} win, {row['sharpe']:.2f} Sharpe")
        
        df.to_csv(RESULTS_DIR / 'asian_session_fade_backtest.csv', index=False)
        print(f"\n💾 Saved to results/asian_session_fade_backtest.csv")
    else:
        print("\n❌ No valid results")

if __name__ == '__main__':
    main()
