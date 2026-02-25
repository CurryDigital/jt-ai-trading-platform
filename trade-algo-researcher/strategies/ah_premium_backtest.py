#!/usr/bin/env python3
"""
AH Premium Arbitrage Backtest
Test dual-listed China A-share vs H-share premium mean reversion
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def get_data(ticker, start='2019-01-01', end='2024-12-31'):
    """Get price data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty or len(data) < 100:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data['Close'].values.flatten()
    except:
        return None

def backtest_ah_premium(h_prices, a_prices, ticker_h, ticker_a, threshold=0.30, hold_days=20):
    """
    Backtest AH premium arbitrage.
    
    When H-shares trade at >30% discount to A-shares (AH premium > 30%),
    long H-shares expecting convergence.
    
    Simplified: Assume we can track relative performance
    """
    if h_prices is None or a_prices is None:
        return None
    
    min_len = min(len(h_prices), len(a_prices))
    h = h_prices[:min_len]
    a = a_prices[:min_len]
    
    # Calculate AH premium
    # Premium = (A - H) / H
    # If premium > 30%, H-shares are cheap
    
    trades = []
    in_trade = False
    entry_idx = 0
    
    for i in range(60, min_len - hold_days):  # Need 60 days for rolling avg
        if not in_trade:
            # Calculate current premium
            premium = (a[i] - h[i]) / h[i]
            
            # Calculate historical average premium (60-day)
            hist_premium = np.mean([(a[j] - h[j]) / h[j] for j in range(i-60, i)])
            
            # Entry: Premium > 30% AND above historical average
            if premium > threshold and premium > hist_premium * 1.2:
                in_trade = True
                entry_idx = i
                entry_premium = premium
        else:
            # Exit after hold_days
            if i - entry_idx >= hold_days:
                # Calculate returns
                h_return = (h[i] - h[entry_idx]) / h[entry_idx]
                
                # For simplified backtest, just track H-share return
                # (assuming A-shares stay flat or we hedge)
                pnl = h_return
                
                trades.append({
                    'pnl': pnl,
                    'entry_premium': entry_premium,
                    'exit_premium': (a[i] - h[i]) / h[i],
                    'hold_days': i - entry_idx
                })
                in_trade = False
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'pair': f"{ticker_h}_{ticker_a}",
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'total_return': (1 + df['pnl']).prod() - 1,
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/hold_days) if df['pnl'].std() > 0 else 0,
        'avg_entry_premium': df['entry_premium'].mean(),
        'avg_exit_premium': df['exit_premium'].mean()
    }

def main():
    print("=" * 80)
    print("AH PREMIUM ARBITRAGE BACKTEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Testing dual-listed China stock premium mean reversion")
    print("=" * 80)
    
    # Dual-listed pairs (H-share : A-share)
    # Note: A-shares need .SS (Shanghai) or .SZ (Shenzhen) suffix
    pairs = [
        ('2318.HK', '601318.SS', 'Ping An'),
        ('0998.HK', '600028.SS', 'Sinopec'),
        ('1398.HK', '601398.SS', 'ICBC'),
        ('0939.HK', '601939.SS', 'CCB'),
        ('1288.HK', '601288.SS', 'Agricultural Bank'),
        ('3988.HK', '601988.SS', 'Bank of China'),
        ('6030.HK', '600030.SS', 'CITIC Securities'),
        ('1336.HK', '601336.SS', 'New China Life'),
        ('1339.HK', '601339.SS', 'CRRC'),
        ('1766.HK', '601766.SS', 'CRRC'),
    ]
    
    results = []
    
    for h_ticker, a_ticker, name in pairs:
        print(f"\n{name}: {h_ticker} vs {a_ticker}")
        
        h_data = get_data(h_ticker)
        a_data = get_data(a_ticker)
        
        if h_data is None:
            print(f"  ❌ No data for {h_ticker}")
            continue
        if a_data is None:
            print(f"  ❌ No data for {a_ticker}")
            continue
        
        print(f"  ✓ Data: {len(h_data)} H-shares, {len(a_data)} A-shares")
        
        result = backtest_ah_premium(h_data, a_data, h_ticker, a_ticker)
        
        if result and result['trades'] >= 3:
            print(f"  Trades: {result['trades']}")
            print(f"  Win Rate: {result['win_rate']:.1%}")
            print(f"  Avg Return: {result['avg_return']:.2%}")
            print(f"  Total Return: {result['total_return']:.1%}")
            print(f"  Sharpe: {result['sharpe']:.2f}")
            print(f"  Avg Entry Premium: {result['avg_entry_premium']:.1%}")
            print(f"  Avg Exit Premium: {result['avg_exit_premium']:.1%}")
            
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
        print(f"\nPairs tested: {len(df)}")
        print(f"Pairs with >55% win rate: {(df['win_rate'] > 0.55).sum()}")
        
        if len(df) > 0:
            print(f"\nAverage metrics:")
            print(f"  Win Rate: {df['win_rate'].mean():.1%}")
            print(f"  Sharpe: {df['sharpe'].mean():.2f}")
            print(f"  Avg Return: {df['avg_return'].mean():.2%}")
        
        # Best performers
        print("\nBest performers:")
        best = df.nlargest(3, 'win_rate')
        for _, row in best.iterrows():
            print(f"  {row['pair']}: {row['win_rate']:.1%} win, {row['sharpe']:.2f} Sharpe")
        
        df.to_csv(RESULTS_DIR / 'ah_premium_backtest.csv', index=False)
        print(f"\n💾 Saved to results/ah_premium_backtest.csv")
    else:
        print("\n❌ No valid results")

if __name__ == '__main__':
    main()
