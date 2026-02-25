#!/usr/bin/env python3
"""
Commodity Seasonality Backtest Engine
Tests seasonal trading patterns in futures markets

Usage:
    python commodity_seasonality_backtest.py --commodity NG
    python commodity_seasonality_backtest.py --all
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Seasonal patterns (expected monthly returns %)
SEASONAL_PATTERNS = {
    'NG': {  # Natural Gas
        1: 2.0, 2: 1.5, 3: -2.0, 4: -1.5, 5: 0.5, 6: 1.0,
        7: 2.0, 8: 1.5, 9: -1.5, 10: -1.0, 11: 3.0, 12: 2.5
    },
    'RB': {  # Gasoline
        1: 0.5, 2: 1.5, 3: 2.0, 4: 1.5, 5: 2.0, 6: 2.5,
        7: 2.0, 8: 1.0, 9: -0.5, 10: -1.5, 11: -0.5, 12: 0.5
    },
    'HO': {  # Heating Oil
        1: 2.0, 2: 2.5, 3: 1.0, 4: -1.0, 5: -0.5, 6: 0.5,
        7: 0.5, 8: 0.5, 9: 1.5, 10: 2.0, 11: 2.5, 12: 2.0
    },
    'ZC': {  # Corn
        1: 0.5, 2: 1.0, 3: 2.0, 4: 2.5, 5: 2.0, 6: 1.5,
        7: 2.0, 8: 1.0, 9: -2.0, 10: -2.5, 11: -1.5, 12: 0.5
    }
}


def load_commodity_data(commodity: str) -> pd.DataFrame:
    """Load commodity futures data."""
    data_file = DATA_DIR / "commodities" / f"{commodity}_daily_synthetic.csv"
    
    if not data_file.exists():
        print(f"[ERROR] Data file not found: {data_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    return df


def calculate_monthly_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly returns for seasonal analysis."""
    if df.empty:
        return pd.DataFrame()
    
    df = df.sort_values('date')
    df['month_year'] = df['date'].dt.to_period('M')
    
    # Monthly close prices
    monthly = df.groupby('month_year').agg({
        'close': 'last',
        'commodity': 'first',
        'month': 'first',
        'year': 'first'
    }).reset_index()
    
    # Calculate returns
    monthly['return'] = monthly['close'].pct_change() * 100
    
    return monthly


def analyze_seasonality(monthly_df: pd.DataFrame) -> Dict:
    """Analyze seasonal patterns in monthly returns."""
    if monthly_df.empty:
        return {}
    
    commodity = monthly_df['commodity'].iloc[0]
    
    stats = {}
    for month in range(1, 13):
        month_data = monthly_df[monthly_df['month'] == month]['return'].dropna()
        
        if len(month_data) > 0:
            stats[month] = {
                'mean': month_data.mean(),
                'std': month_data.std(),
                'count': len(month_data),
                'win_rate': (month_data > 0).mean(),
                't_stat': month_data.mean() / (month_data.std() / np.sqrt(len(month_data))) if month_data.std() > 0 else 0
            }
    
    return stats


def run_seasonal_backtest(df: pd.DataFrame, commodity: str, threshold: float = 1.5) -> pd.DataFrame:
    """Run seasonal trading backtest."""
    if df.empty:
        return pd.DataFrame()
    
    pattern = SEASONAL_PATTERNS.get(commodity, {})
    
    trades = []
    df = df.sort_values('date')
    
    for year in df['year'].unique():
        for month in range(1, 13):
            score = pattern.get(month, 0)
            
            if abs(score) < threshold:
                continue
            
            month_mask = (df['year'] == year) & (df['month'] == month)
            month_data = df[month_mask]
            
            if len(month_data) < 2:
                continue
            
            entry_price = month_data.iloc[0]['open']
            exit_price = month_data.iloc[-1]['close']
            
            pnl = (exit_price / entry_price - 1) * 100
            
            direction = 1 if score > 0 else -1
            pnl = pnl * direction
            
            trades.append({
                'commodity': commodity,
                'year': year,
                'month': month,
                'entry_date': month_data.iloc[0]['date'],
                'exit_date': month_data.iloc[-1]['date'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'seasonal_score': score,
                'direction': 'long' if direction > 0 else 'short',
                'pnl': pnl
            })
    
    return pd.DataFrame(trades)


def calculate_metrics(trades_df: pd.DataFrame) -> Dict:
    """Calculate performance metrics."""
    if trades_df.empty:
        return {}
    
    returns = trades_df['pnl']
    
    metrics = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean(),
        'avg_return': returns.mean(),
        'median_return': returns.median(),
        'std_return': returns.std(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(12) if returns.std() > 0 else 0,
        'max_drawdown': (returns.cumsum() - returns.cumsum().cummax()).min(),
        'best_month': returns.max(),
        'worst_month': returns.min()
    }
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Commodity Seasonality Backtest')
    parser.add_argument('--commodity', type=str, default='NG',
                       choices=['NG', 'RB', 'HO', 'ZC'],
                       help='Commodity to backtest')
    parser.add_argument('--threshold', type=float, default=1.5, help='Seasonal score threshold')
    parser.add_argument('--all', action='store_true', help='Backtest all commodities')
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("Commodity Seasonality Backtest Engine")
    print(f"{'='*70}\n")
    
    commodities = ['NG', 'RB', 'HO', 'ZC'] if args.all else [args.commodity]
    
    all_results = []
    
    for commodity in commodities:
        print(f"\n{'-'*70}")
        print(f"Analyzing: {commodity}")
        print(f"{'-'*70}")
        
        df = load_commodity_data(commodity)
        
        if df.empty:
            print(f"[ERROR] No data for {commodity}")
            continue
        
        print(f"Loaded {len(df)} daily records")
        
        monthly_df = calculate_monthly_returns(df)
        
        if monthly_df.empty:
            print(f"[ERROR] Could not calculate monthly returns")
            continue
        
        seasonality = analyze_seasonality(monthly_df)
        
        print("\nSeasonal Analysis (by month):")
        print(f"{'Month':<8} {'Mean%':<8} {'Win%':<8} {'T-Stat':<8}")
        print("-" * 35)
        for month in range(1, 13):
            if month in seasonality:
                s = seasonality[month]
                print(f"{month:<8} {s['mean']:>7.2f} {s['win_rate']*100:>7.1f} {s['t_stat']:>7.2f}")
        
        print(f"\nRunning backtest (threshold={args.threshold})...")
        trades_df = run_seasonal_backtest(df, commodity, args.threshold)
        
        if trades_df.empty:
            print("[WARNING] No trades generated")
            continue
        
        metrics = calculate_metrics(trades_df)
        
        print(f"\nBacktest Results:")
        print(f"  Total Trades: {metrics.get('total_trades', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"  Avg Return: {metrics.get('avg_return', 0):.2f}%")
        print(f"  Sharpe Ratio: {metrics.get('sharpe', 0):.2f}")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        
        all_results.append({
            'commodity': commodity,
            'metrics': metrics,
            'trades': trades_df
        })
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        trades_file = RESULTS_DIR / f"commodity_{commodity}_{timestamp}_trades.csv"
        trades_df.to_csv(trades_file, index=False)
        print(f"\n  Saved: {trades_file}")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Commodity':<12} {'Trades':<8} {'Win%':<8} {'Sharpe':<8} {'Status':<10}")
    print("-" * 55)
    
    for result in all_results:
        m = result['metrics']
        sharpe = m.get('sharpe', 0)
        status = "✅ PASS" if sharpe >= 0.9 else "⚠️ LOW"
        print(f"{result['commodity']:<12} {m.get('total_trades', 0):<8} "
              f"{m.get('win_rate', 0):.1%}    {sharpe:.2f}     {status}")
    
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
