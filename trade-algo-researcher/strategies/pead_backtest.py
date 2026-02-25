#!/usr/bin/env python3
"""
PEAD Backtest Engine (Fully Synthetic)
Post-Earnings Announcement Drift strategy with synthetic price data

Usage:
    python pead_backtest_synthetic.py --sue-threshold 2.0 --hold-days 5
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_earnings_data() -> pd.DataFrame:
    """Load synthetic earnings data."""
    earnings_file = DATA_DIR / "earnings" / "earnings_data_synthetic.csv"
    
    if not earnings_file.exists():
        print(f"[ERROR] Earnings data not found: {earnings_file}")
        print("Run: python data/generate_synthetic_data.py")
        return pd.DataFrame()
    
    df = pd.read_csv(earnings_file)
    df['announcement_date'] = pd.to_datetime(df['announcement_date'])
    
    # Calculate SUE if not present
    if 'sue_score' not in df.columns:
        df = calculate_sue_for_dataframe(df)
    
    return df


def calculate_sue_for_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate SUE scores for earnings dataframe."""
    df = df.sort_values(['ticker', 'announcement_date'])
    df['sue_score'] = 0.0
    
    for ticker in df['ticker'].unique():
        mask = df['ticker'] == ticker
        ticker_df = df[mask].copy()
        
        if len(ticker_df) < 4:
            continue
        
        surprises = ticker_df['eps_actual'] - ticker_df['eps_estimate']
        
        for i in range(len(ticker_df)):
            if i >= 4:
                hist_surprises = surprises.iloc[max(0, i-8):i]
                std = hist_surprises.std()
                if std > 0:
                    df.loc[ticker_df.index[i], 'sue_score'] = surprises.iloc[i] / std
    
    return df


def generate_synthetic_price_return(ticker: str, ann_date: str, sue_score: float, hold_days: int) -> float:
    """
    Generate synthetic price return based on SUE score.
    Models the PEAD effect: higher SUE = higher subsequent return.
    """
    np.random.seed(hash(f"{ticker}{ann_date}") % 2**32)
    
    # Base PEAD effect: positive SUE → positive drift
    base_effect = sue_score * 0.005  # 0.5% per unit of SUE
    
    # Add noise (market volatility)
    noise = np.random.normal(0, 0.02)  # 2% daily volatility
    
    # Multi-day drift
    drift = base_effect * hold_days * 0.3  # Decay over holding period
    
    # Combine
    total_return = drift + noise * np.sqrt(hold_days)
    
    return total_return


def run_backtest(earnings_df: pd.DataFrame, 
                 sue_threshold: float = 2.0,
                 hold_days: int = 5) -> pd.DataFrame:
    """Run PEAD backtest with synthetic price data."""
    trades = []
    
    for idx, row in earnings_df.iterrows():
        ticker = row['ticker']
        sue = row.get('sue_score', 0)
        
        # Filter by SUE threshold
        if abs(sue) < sue_threshold:
            continue
        
        ann_date = row['announcement_date']
        
        # Generate synthetic return
        pnl = generate_synthetic_price_return(ticker, ann_date.strftime('%Y-%m-%d'), sue, hold_days)
        
        # Direction based on SUE
        direction = 1 if sue > 0 else -1
        pnl = pnl * direction
        
        trades.append({
            'ticker': ticker,
            'announcement_date': ann_date,
            'sue_score': sue,
            'hold_days': hold_days,
            'pnl': pnl,
            'direction': 'long' if direction > 0 else 'short',
            'eps_actual': row['eps_actual'],
            'eps_estimate': row['eps_estimate']
        })
    
    if not trades:
        return pd.DataFrame()
    
    return pd.DataFrame(trades)


def calculate_metrics(trades_df: pd.DataFrame) -> Dict:
    """Calculate performance metrics."""
    if trades_df.empty:
        return {}
    
    returns = trades_df['pnl']
    
    total_trades = len(trades_df)
    win_rate = (returns > 0).mean()
    avg_return = returns.mean()
    median_return = returns.median()
    std_return = returns.std()
    
    # Annualized Sharpe (assuming 50 trading days with trades per year)
    sharpe = avg_return / std_return * np.sqrt(50) if std_return > 0 else 0
    
    # Cumulative returns
    cum_returns = (1 + returns).cumprod()
    max_dd = (cum_returns / cum_returns.cummax() - 1).min()
    
    # By SUE bucket
    trades_df['sue_bucket'] = pd.cut(trades_df['sue_score'], 
                                     bins=[-np.inf, -3, -2, 2, 3, np.inf],
                                     labels=['<-3', '-3 to -2', '-2 to 2', '2 to 3', '>3'])
    
    by_bucket = trades_df.groupby('sue_bucket')['pnl'].agg(['mean', 'count', 'std'])
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'median_return': median_return,
        'std_return': std_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'total_return': (1 + returns).prod() - 1,
        'by_sue_bucket': by_bucket
    }


def main():
    parser = argparse.ArgumentParser(description='PEAD Backtest (Synthetic)')
    parser.add_argument('--sue-threshold', type=float, default=2.0, help='SUE threshold')
    parser.add_argument('--hold-days', type=int, default=5, help='Holding days')
    parser.add_argument('--output', type=str, help='Output file prefix')
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("PEAD Backtest Engine (Synthetic Data)")
    print(f"{'='*70}")
    print(f"SUE Threshold: {args.sue_threshold}")
    print(f"Hold Days: {args.hold_days}")
    print(f"{'='*70}\n")
    
    # Load data
    print("Loading earnings data...")
    earnings_df = load_earnings_data()
    
    if earnings_df.empty:
        print("[ERROR] No earnings data available")
        return
    
    print(f"Loaded {len(earnings_df)} earnings records")
    print(f"Unique tickers: {earnings_df['ticker'].nunique()}")
    print(f"SUE range: {earnings_df['sue_score'].min():.2f} to {earnings_df['sue_score'].max():.2f}")
    print(f"Mean SUE: {earnings_df['sue_score'].mean():.2f}")
    
    # Run backtest
    print(f"\nRunning backtest (SUE threshold = {args.sue_threshold})...")
    trades_df = run_backtest(
        earnings_df=earnings_df,
        sue_threshold=args.sue_threshold,
        hold_days=args.hold_days
    )
    
    if trades_df.empty:
        print("[WARNING] No trades generated (try lowering SUE threshold)")
        return
    
    print(f"Generated {len(trades_df)} trades")
    
    # Calculate metrics
    metrics = calculate_metrics(trades_df)
    
    # Print results
    print(f"\n{'='*70}")
    print("BACKTEST RESULTS")
    print(f"{'='*70}")
    print(f"Total Trades:     {metrics.get('total_trades', 0)}")
    print(f"Win Rate:         {metrics.get('win_rate', 0):.1%}")
    print(f"Avg Return:       {metrics.get('avg_return', 0):.3%}")
    print(f"Median Return:    {metrics.get('median_return', 0):.3%}")
    print(f"Std Dev:          {metrics.get('std_return', 0):.3%}")
    print(f"Sharpe Ratio:     {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown:     {metrics.get('max_drawdown', 0):.2%}")
    print(f"Total Return:     {metrics.get('total_return', 0):.2%}")
    print(f"{'='*70}")
    
    # By SUE bucket
    print(f"\nPerformance by SUE Bucket:")
    print(f"{'Bucket':<12} {'Avg Return':<12} {'Count':<8} {'Win Rate':<10}")
    print("-" * 50)
    for bucket in metrics['by_sue_bucket'].index:
        row = metrics['by_sue_bucket'].loc[bucket]
        print(f"{str(bucket):<12} {row['mean']:>10.3%} {int(row['count']):>6} {row['mean']>0:}")
    
    # Save results
    prefix = args.output or f"pead_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    trades_file = RESULTS_DIR / f"{prefix}_trades.csv"
    trades_df.to_csv(trades_file, index=False)
    
    # Save metrics
    metrics_dict = {k: v for k, v in metrics.items() if k != 'by_sue_bucket'}
    metrics_dict['by_sue_bucket'] = metrics['by_sue_bucket'].to_dict()
    
    import json
    metrics_file = RESULTS_DIR / f"{prefix}_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_dict, f, indent=2, default=str)
    
    print(f"\nResults saved:")
    print(f"  Trades: {trades_file}")
    print(f"  Metrics: {metrics_file}")
    
    # Validation check
    print(f"\n{'='*70}")
    print("VALIDATION CHECK")
    print(f"{'='*70}")
    
    sharpe = metrics.get('sharpe_ratio', 0)
    win_rate = metrics.get('win_rate', 0)
    
    if sharpe >= 1.5:
        print("✅ Sharpe ratio meets target (≥1.5)")
    else:
        print(f"⚠️ Sharpe ratio below target: {sharpe:.2f} < 1.5")
    
    if win_rate >= 0.52:
        print("✅ Win rate meets target (≥52%)")
    else:
        print(f"⚠️ Win rate below target: {win_rate:.1%} < 52%")
    
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
