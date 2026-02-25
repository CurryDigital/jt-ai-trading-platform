#!/usr/bin/env python3
"""
Crypto Funding Rate Backtest (Simplified)
Test mean reversion of funding rates on major cryptos
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

def get_crypto_data(ticker, start='2019-01-01', end='2024-12-31'):
    """Get crypto price data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty or len(data) < 100:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

def backtest_funding_proxy(prices, ticker, threshold=0.05, hold_days=3):
    """
    Simplified funding rate proxy strategy.
    
    After large moves (proxy for high funding), expect mean reversion.
    Similar concept: high funding = crowded longs = expect pullback.
    """
    if prices is None or len(prices) < 50:
        return None
    
    closes = prices['Close'].values.flatten()
    returns = pd.Series(closes).pct_change()
    
    # Use 3-day return as proxy for funding pressure
    # Large 3-day moves = proxy for high funding environment
    ret_3d = returns.rolling(3).sum()
    
    trades = []
    for i in range(10, len(prices) - hold_days):
        # Entry: Large 3-day move (proxy for high funding)
        if abs(ret_3d.iloc[i]) < threshold:
            continue
        
        # Fade the move
        direction = -1 if ret_3d.iloc[i] > 0 else 1  # Mean reversion
        
        entry = closes[i+1]  # Next day open
        exit_p = closes[i+hold_days]  # Hold N days
        
        pnl = (exit_p - entry) / entry * direction
        
        trades.append({
            'date': prices.index[i],
            'move_3d': ret_3d.iloc[i],
            'pnl': pnl,
            'direction': 'short' if direction == -1 else 'long'
        })
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/hold_days) if df['pnl'].std() > 0 else 0,
        'avg_move': df['move_3d'].abs().mean()
    }

def main():
    print("=" * 80)
    print("CRYPTO FUNDING RATE PROXY BACKTEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Proxy: Using 3-day moves as funding pressure signal")
    print("Concept: Large moves = crowded positioning = mean reversion")
    print("=" * 80)
    
    cryptos = [
        ('BTC-USD', 'Bitcoin'),
        ('ETH-USD', 'Ethereum'),
        ('SOL-USD', 'Solana'),
        ('ADA-USD', 'Cardano'),
        ('DOT-USD', 'Polkadot'),
        ('MATIC-USD', 'Polygon'),
        ('LINK-USD', 'Chainlink'),
        ('UNI-USD', 'Uniswap'),
        ('AAVE-USD', 'Aave'),
        ('CRV-USD', 'Curve'),
    ]
    
    results = []
    
    for ticker, name in cryptos:
        print(f"\n{name}: {ticker}")
        
        prices = get_crypto_data(ticker)
        if prices is None:
            print(f"  ❌ No data")
            continue
        
        print(f"  ✓ Data: {len(prices)} days")
        
        result = backtest_funding_proxy(prices, ticker)
        
        if result and result['trades'] >= 20:
            print(f"  Trades: {result['trades']}")
            print(f"  Win Rate: {result['win_rate']:.1%}")
            print(f"  Avg Return: {result['avg_return']:.2%}")
            print(f"  Sharpe: {result['sharpe']:.2f}")
            print(f"  Avg 3D Move: {result['avg_move']:.1%}")
            
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
        print(f"\nCryptos tested: {len(df)}")
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
        
        df.to_csv(RESULTS_DIR / 'crypto_funding_proxy_backtest.csv', index=False)
        print(f"\n💾 Saved to results/crypto_funding_proxy_backtest.csv")
    else:
        print("\n❌ No valid results")

if __name__ == '__main__':
    main()
