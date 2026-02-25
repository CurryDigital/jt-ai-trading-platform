#!/usr/bin/env python3
"""
Batch Backtest Runner - Additional Free-Data Strategies
VIX proxy, sector rotation, simple pairs
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
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

def backtest_vix_proxy(spy_data, vix_data, ticker='SPY'):
    """VIX proxy using volatility regime switching."""
    if spy_data is None or len(spy_data) < 50:
        return None
    
    closes = spy_data['Close'].values.flatten()
    returns = pd.Series(closes).pct_change()
    vol_20d = returns.rolling(20).std() * np.sqrt(252)
    
    trades = []
    in_high_vol = False
    
    for i in range(40, len(spy_data) - 10):
        vol_current = vol_20d.iloc[i]
        vol_avg = vol_20d.iloc[i-40:i].mean()
        
        if vol_current > vol_avg * 1.5 and not in_high_vol:
            # Entering high vol - go to cash/short
            in_high_vol = True
            entry = closes[i]
            exit_p = closes[i+10]
            # Short SPY during high vol
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl, 'type': 'short_vol'})
        elif vol_current < vol_avg * 1.2 and in_high_vol:
            # Vol normalization
            in_high_vol = False
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'VIX_Proxy_Vol_Regime',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/10) if df['pnl'].std() > 0 else 0
    }

def backtest_sector_rotation(tech_data, util_data, ticker_pair='XLK_XLU'):
    """Tech vs Utilities sector rotation."""
    if tech_data is None or util_data is None:
        return None
    
    tech_closes = tech_data['Close'].values.flatten()
    util_closes = util_data['Close'].values.flatten()
    
    # Calculate relative performance
    tech_returns = pd.Series(tech_closes).pct_change(20)
    util_returns = pd.Series(util_closes).pct_change(20)
    
    trades = []
    for i in range(30, min(len(tech_data), len(util_data)) - 20):
        if tech_returns.iloc[i] > util_returns.iloc[i] + 0.05:
            # Tech outperforming - long tech
            entry = tech_closes[i]
            exit_p = tech_closes[i+20]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long_tech'})
        elif util_returns.iloc[i] > tech_returns.iloc[i] + 0.05:
            # Utilities outperforming - long utilities
            entry = util_closes[i]
            exit_p = util_closes[i+20]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long_util'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Sector_Rotation_Tech_Util',
        'ticker': ticker_pair,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/20) if df['pnl'].std() > 0 else 0
    }

def backtest_simple_pairs(gold_data, silver_data, pair='GLD_SLV'):
    """Simple gold/silver ratio mean reversion."""
    if gold_data is None or silver_data is None:
        return None
    
    gold_closes = gold_data['Close'].values.flatten()
    silver_closes = silver_data['Close'].values.flatten()
    
    # Calculate ratio
    ratio = pd.Series(gold_closes) / pd.Series(silver_closes)
    ratio_ma = ratio.rolling(50).mean()
    ratio_std = ratio.rolling(50).std()
    
    trades = []
    for i in range(60, min(len(gold_data), len(silver_data)) - 10):
        z_score = (ratio.iloc[i] - ratio_ma.iloc[i]) / ratio_std.iloc[i]
        
        if z_score < -1.5:  # Ratio low - long gold short silver
            entry_gold = gold_closes[i]
            exit_gold = gold_closes[i+10]
            pnl_gold = (exit_gold - entry_gold) / entry_gold
            
            entry_silver = silver_closes[i]
            exit_silver = silver_closes[i+10]
            pnl_silver = (entry_silver - exit_silver) / entry_silver
            
            pnl = (pnl_gold + pnl_silver) / 2
            trades.append({'pnl': pnl, 'type': 'ratio_low'})
            
        elif z_score > 1.5:  # Ratio high - short gold long silver
            entry_gold = gold_closes[i]
            exit_gold = gold_closes[i+10]
            pnl_gold = (entry_gold - exit_gold) / entry_gold
            
            entry_silver = silver_closes[i]
            exit_silver = silver_closes[i+10]
            pnl_silver = (exit_silver - entry_silver) / entry_silver
            
            pnl = (pnl_gold + pnl_silver) / 2
            trades.append({'pnl': pnl, 'type': 'ratio_high'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Pairs_Gold_Silver',
        'ticker': pair,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/10) if df['pnl'].std() > 0 else 0
    }

def backtest_yield_curve_proxy(spy_data, tlt_data, pair='SPY_TLT'):
    """Trade yield curve steepening/flattening proxy."""
    if spy_data is None or tlt_data is None:
        return None
    
    spy_closes = spy_data['Close'].values.flatten()
    tlt_closes = tlt_data['Close'].values.flatten()
    
    spy_returns = pd.Series(spy_closes).pct_change(20)
    tlt_returns = pd.Series(tlt_closes).pct_change(20)
    
    trades = []
    for i in range(30, min(len(spy_data), len(tlt_data)) - 20):
        # When SPY rallies hard, yields likely rising (TLT down)
        # When TLT rallies, yields falling (flight to safety)
        
        if spy_returns.iloc[i] > 0.08 and tlt_returns.iloc[i] < -0.05:
            # Steepening - short TLT
            entry = tlt_closes[i]
            exit_p = tlt_closes[i+10]
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl, 'type': 'short_tlt'})
            
        elif spy_returns.iloc[i] < -0.05 and tlt_returns.iloc[i] > 0.05:
            # Flight to safety - long TLT
            entry = tlt_closes[i]
            exit_p = tlt_closes[i+10]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long_tlt'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Yield_Curve_Proxy',
        'ticker': pair,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/10) if df['pnl'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("BATCH BACKTEST - ADDITIONAL FREE-DATA STRATEGIES")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)
    
    all_results = []
    
    # VIX Proxy
    print("\n📊 VIX Proxy (Vol Regime)...")
    spy = get_data('SPY')
    if spy is not None:
        result = backtest_vix_proxy(spy, None, 'SPY')
        if result:
            all_results.append(result)
            print(f"  Trades: {result['trades']}, Win: {result['win_rate']:.1%}, Sharpe: {result['sharpe']:.2f}")
    
    # Sector Rotation
    print("\n📊 Sector Rotation (Tech vs Utilities)...")
    xlk = get_data('XLK')
    xlu = get_data('XLU')
    if xlk is not None and xlu is not None:
        result = backtest_sector_rotation(xlk, xlu, 'XLK_XLU')
        if result:
            all_results.append(result)
            print(f"  Trades: {result['trades']}, Win: {result['win_rate']:.1%}, Sharpe: {result['sharpe']:.2f}")
    
    # Pairs - Gold/Silver
    print("\n📊 Gold/Silver Pairs...")
    gld = get_data('GLD')
    slv = get_data('SLV')
    if gld is not None and slv is not None:
        result = backtest_simple_pairs(gld, slv, 'GLD_SLV')
        if result:
            all_results.append(result)
            print(f"  Trades: {result['trades']}, Win: {result['win_rate']:.1%}, Sharpe: {result['sharpe']:.2f}")
    
    # Yield Curve Proxy
    print("\n📊 Yield Curve Proxy (SPY vs TLT)...")
    tlt = get_data('TLT')
    if spy is not None and tlt is not None:
        result = backtest_yield_curve_proxy(spy, tlt, 'SPY_TLT')
        if result:
            all_results.append(result)
            print(f"  Trades: {result['trades']}, Win: {result['win_rate']:.1%}, Sharpe: {result['sharpe']:.2f}")
    
    # Summary
    if all_results:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        results_df = pd.DataFrame(all_results)
        print(results_df[['strategy', 'ticker', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
        
        # Best performers
        top = results_df[(results_df['win_rate'] > 0.55) & (results_df['sharpe'] > 0.5)]
        print(f"\n✅ Passing strategies: {len(top)}/{len(all_results)}")
        
        if not top.empty:
            print("\nTop performers:")
            print(top[['strategy', 'ticker', 'win_rate', 'sharpe']].to_string(index=False))
        
        results_df.to_csv(RESULTS_DIR / 'batch_additional_backtest.csv', index=False)
        print(f"\n💾 Saved to results/batch_additional_backtest.csv")
    else:
        print("\n❌ No results generated")

if __name__ == '__main__':
    main()
