#!/usr/bin/env python3
"""
Broad HK Market Test - 50+ Stocks
Test rejected US strategies on full spectrum of HK stocks
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"

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

def backtest_3day_reversal(data):
    """3-Day Reversal test."""
    if data is None:
        return None
    
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    returns = pd.Series(closes).pct_change().values
    avg_volume = pd.Series(volumes).rolling(20).mean().values
    
    trades = []
    for i in range(20, len(data) - 4):
        down_1 = returns[i-2] < 0
        down_2 = returns[i-1] < 0  
        down_3 = returns[i] < 0
        
        if not (down_1 and down_2 and down_3):
            continue
        
        decline_3d = (closes[i] - closes[i-3]) / closes[i-3]
        if decline_3d > -0.05:
            continue
        
        volume_spike = volumes[i] / avg_volume[i] if avg_volume[i] > 0 else 1
        if volume_spike < 1.3:
            continue
        
        entry_price = closes[i+1]
        exit_price = closes[i+4]
        pnl = (exit_price - entry_price) / entry_price
        
        trades.append({'pnl': pnl})
    
    if len(trades) < 10:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/3) if df['pnl'].std() > 0 else 0
    }

def backtest_gap_fade(data):
    """Gap Fade test."""
    if data is None:
        return None
    
    opens = data['Open'].values.flatten()
    closes = data['Close'].values.flatten()
    
    trades = []
    for i in range(1, len(data)):
        gap = (opens[i] - closes[i-1]) / closes[i-1]
        
        if abs(gap) < 0.005:
            continue
        
        if gap > 0:
            pnl = (opens[i] - closes[i]) / opens[i]
        else:
            pnl = (closes[i] - opens[i]) / opens[i]
        
        trades.append({'pnl': pnl})
    
    if len(trades) < 10:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252) if df['pnl'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("BROAD HK MARKET TEST - 50+ STOCKS")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Testing rejected US strategies on full HK universe")
    print("=" * 80)
    
    # 50+ HK stocks across sectors
    hk_tickers = [
        # Conglomerates
        '0001.HK', '0012.HK', '0016.HK', '0017.HK', '0027.HK', '0066.HK',
        # Utilities/Infrastructure
        '0002.HK', '0003.HK', '0006.HK', '0836.HK', '1038.HK', '2688.HK',
        # Finance
        '0005.HK', '0011.HK', '0023.HK', '0939.HK', '1299.HK', '2318.HK', '2388.HK', '2628.HK', '2888.HK', '2899.HK',
        # Property
        '0017.HK', '0101.HK', '0883.HK', '0960.HK', '1109.HK', '1113.HK', '1972.HK', '1997.HK',
        # Tech/Telco
        '0070.HK', '00762.HK', '02018.HK', '02313.HK', '02382.HK', '03690.HK', '09618.HK', '09988.HK',
        # Energy/Materials
        '00038.HK', '00857.HK', '00883.HK', '00939.HK', '01211.HK', '01898.HK', '02318.HK',
        # Consumer/Retail
        '00175.HK', '00267.HK', '00293.HK', '00494.HK', '00688.HK', '01876.HK', '01928.HK', '02319.HK',
        # Transport
        '00293.HK', '00662.HK',
        # Others
        '0241.HK', '0386.HK', '0388.HK', '1044.HK', '1093.HK', '1177.HK', '1398.HK', '1658.HK', '1810.HK', '9633.HK', '9999.HK'
    ]
    
    print(f"\nTesting {len(hk_tickers)} Hong Kong stocks...")
    print("Strategies: 3-Day Reversal, Gap Fade")
    print()
    
    results_3day = []
    results_gap = []
    failed_tickers = []
    
    for i, ticker in enumerate(hk_tickers, 1):
        print(f"[{i}/{len(hk_tickers)}] {ticker}...", end=' ')
        
        data = get_data(ticker)
        if data is None:
            print("❌ No data")
            failed_tickers.append(ticker)
            continue
        
        # Test 3-Day Reversal
        result_3day = backtest_3day_reversal(data)
        if result_3day:
            result_3day['ticker'] = ticker
            results_3day.append(result_3day)
            status_3d = "✅" if result_3day['win_rate'] > 0.55 else "❌"
        else:
            status_3d = "⚠️"
        
        # Test Gap Fade
        result_gap = backtest_gap_fade(data)
        if result_gap:
            result_gap['ticker'] = ticker
            results_gap.append(result_gap)
            status_gap = "✅" if result_gap['win_rate'] > 0.55 else "❌"
        else:
            status_gap = "⚠️"
        
        wr_3d = f"{result_3day['win_rate']:.1%}" if result_3day else 'N/A'
        wr_gap = f"{result_gap['win_rate']:.1%}" if result_gap else 'N/A'
        print(f"3D:{status_3d} {wr_3d} | GF:{status_gap} {wr_gap}")
    
    # Summaries
    print("\n" + "=" * 80)
    print("3-DAY REVERSAL RESULTS (HK Market)")
    print("=" * 80)
    
    if results_3day:
        df_3day = pd.DataFrame(results_3day)
        df_3day_sorted = df_3day.sort_values('win_rate', ascending=False)
        
        print(f"\nTotal stocks tested: {len(results_3day)}")
        print(f"Passing (WR > 55%): {(df_3day['win_rate'] > 0.55).sum()}")
        print(f"Average win rate: {df_3day['win_rate'].mean():.1%}")
        print(f"Average Sharpe: {df_3day['sharpe'].mean():.2f}")
        
        print("\nTop 10 Performers:")
        print(df_3day_sorted.head(10)[['ticker', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
        
        print("\nBottom 5 Performers:")
        print(df_3day_sorted.tail(5)[['ticker', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
    
    print("\n" + "=" * 80)
    print("GAP FADE RESULTS (HK Market)")
    print("=" * 80)
    
    if results_gap:
        df_gap = pd.DataFrame(results_gap)
        df_gap_sorted = df_gap.sort_values('win_rate', ascending=False)
        
        print(f"\nTotal stocks tested: {len(results_gap)}")
        print(f"Passing (WR > 55%): {(df_gap['win_rate'] > 0.55).sum()}")
        print(f"Average win rate: {df_gap['win_rate'].mean():.1%}")
        print(f"Average Sharpe: {df_gap['sharpe'].mean():.2f}")
        
        print("\nTop 10 Performers:")
        print(df_gap_sorted.head(10)[['ticker', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
    
    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    if results_3day:
        passing_3d = (df_3day['win_rate'] > 0.55).sum()
        total_3d = len(df_3day)
        print(f"\n3-Day Reversal: {passing_3d}/{total_3d} HK stocks pass (WR > 55%)")
        print(f"Success rate: {passing_3d/total_3d:.1%}")
        
        if passing_3d >= 10:
            print("🎯 STRONG evidence - Works on many HK stocks")
        elif passing_3d >= 5:
            print("✅ MODERATE evidence - Works on select HK stocks")
        else:
            print("⚠️ WEAK evidence - Only works on few stocks")
    
    if results_gap:
        passing_gap = (df_gap['win_rate'] > 0.55).sum()
        total_gap = len(df_gap)
        print(f"\nGap Fade: {passing_gap}/{total_gap} HK stocks pass (WR > 55%)")
        print(f"Success rate: {passing_gap/total_gap:.1%}")
    
    if failed_tickers:
        print(f"\nFailed to download: {len(failed_tickers)} tickers")
        print(failed_tickers[:10])  # Show first 10
    
    # Save results
    if results_3day:
        df_3day.to_csv(RESULTS_DIR / 'hk_broad_3day_reversal.csv', index=False)
    if results_gap:
        df_gap.to_csv(RESULTS_DIR / 'hk_broad_gap_fade.csv', index=False)
    
    print(f"\n💾 Saved to results/")

if __name__ == '__main__':
    main()
