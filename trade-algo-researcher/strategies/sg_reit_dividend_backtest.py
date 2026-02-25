#!/usr/bin/env python3
"""
Singapore REIT Dividend Capture Backtest
Test buying S-REITs before ex-date and capturing dividend + recovery
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
    """Get OHLCV data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty or len(data) < 100:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

def backtest_dividend_capture(prices, ticker, dividend_months=[1,4,7,10], days_before=14, days_after=21):
    """
    Simplified dividend capture backtest.
    
    Assume dividends in Jan, Apr, Jul, Oct (typical S-REIT quarter)
    Buy 14 days before month start, sell 21 days after.
    """
    if prices is None:
        return None
    
    dates = pd.date_range(start='2019-01-01', end='2024-12-31', freq='D')
    
    trades = []
    for year in range(2019, 2025):
        for month in dividend_months:
            try:
                # Entry: 14 days before month start
                entry_date = pd.Timestamp(f'{year}-{month:02d}-01') - pd.Timedelta(days=days_before)
                # Exit: 21 days after month start  
                exit_date = pd.Timestamp(f'{year}-{month:02d}-01') + pd.Timedelta(days=days_after)
                
                # Find closest trading days
                # Simplified: just use index positions
                start_idx = None
                end_idx = None
                
                for i, d in enumerate(prices.index):
                    if d >= entry_date and start_idx is None:
                        start_idx = i
                    if d >= exit_date and end_idx is None:
                        end_idx = i
                        break
                
                if start_idx is not None and end_idx is not None and end_idx < len(prices):
                    entry_price = prices.iloc[start_idx]
                    exit_price = prices.iloc[end_idx]
                    
                    # Assume 5% dividend yield / 4 = 1.25% per quarter
                    dividend = 0.0125
                    
                    total_return = (exit_price - entry_price) / entry_price + dividend
                    trades.append({
                        'date': f'{year}-{month:02d}',
                        'entry': entry_price,
                        'exit': exit_price,
                        'price_return': (exit_price - entry_price) / entry_price,
                        'dividend': dividend,
                        'total_return': total_return
                    })
            except:
                continue
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['total_return'] > 0).mean(),
        'avg_price_return': df['price_return'].mean(),
        'avg_total_return': df['total_return'].mean(),
        'total_cumulative': (1 + df['total_return']).prod() - 1,
        'sharpe': df['total_return'].mean() / df['total_return'].std() * np.sqrt(4) if df['total_return'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("SINGAPORE REIT DIVIDEND CAPTURE BACKTEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Testing quarterly dividend capture strategy")
    print("=" * 80)
    
    # S-REITs (using tickers that might work with yfinance)
    # Note: Many .SI tickers don't work well with yfinance
    # Using ETFs and some REIT proxies
    
    reits = [
        ('A17U.SI', 'Ascendas REIT'),
        ('C38U.SI', 'CapitaLand ICT'),
        ('M44U.SI', 'Mapletree Logistics'),
        ('N2IU.SI', 'Mapletree Commercial'),
        ('ME8U.SI', 'Mapletree Industrial'),
        ('RW0U.SI', 'Keppel DC REIT'),
        ('AJBU.SI', 'Keppel Infrastructure'),
        ('EWS', 'Singapore ETF (proxy)'),
    ]
    
    results = []
    
    for ticker, name in reits:
        print(f"\n{name}: {ticker}")
        
        prices = get_data(ticker)
        if prices is None:
            print(f"  ❌ No data")
            continue
        
        print(f"  ✓ Data: {len(prices)} days")
        
        result = backtest_dividend_capture(prices['Close'], ticker)
        
        if result and result['trades'] >= 4:
            print(f"  Trades (quarters): {result['trades']}")
            print(f"  Win Rate: {result['win_rate']:.1%}")
            print(f"  Avg Price Return: {result['avg_price_return']:.2%}")
            print(f"  Avg Total Return: {result['avg_total_return']:.2%}")
            print(f"  Total Cumulative: {result['total_cumulative']:.1%}")
            print(f"  Sharpe: {result['sharpe']:.2f}")
            
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
        print(f"\nREITs tested: {len(df)}")
        print(f"REITs with >55% win rate: {(df['win_rate'] > 0.55).sum()}")
        
        if len(df) > 0:
            print(f"\nAverage metrics:")
            print(f"  Win Rate: {df['win_rate'].mean():.1%}")
            print(f"  Sharpe: {df['sharpe'].mean():.2f}")
            print(f"  Avg Total Return: {df['avg_total_return'].mean():.2%}")
        
        df.to_csv(RESULTS_DIR / 'sg_reit_dividend_backtest.csv', index=False)
        print(f"\n💾 Saved to results/sg_reit_dividend_backtest.csv")
    else:
        print("\n❌ No valid results - .SI tickers may need alternative data source")

if __name__ == '__main__':
    main()
