#!/usr/bin/env python3
"""
H015-012: Pairs Trading (Mean Reversion)
Trade cointegrated pairs: long underperformer, short outperformer
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest')
from backtest_analytics import BacktestAnalytics

# Pairs to test
PAIRS = [
    ('JPM', 'BAC'),   # Banks
    ('XLK', 'XLF'),   # Sectors
    ('0700.HK', '9988.HK'),  # HK Tech
]

TEST_START, TEST_END = '2023-01-01', '2024-12-31'

def simulate_pair_data(ticker1, ticker2, n_days=1000):
    """Simulate correlated pair data"""
    np.random.seed(hash(ticker1 + ticker2) % 10000)
    
    dates = pd.date_range(end='2025-02-25', periods=n_days, freq='B')
    
    # Common factor
    common_factor = np.random.normal(0.0003, 0.015, n_days)
    
    # Ticker 1
    returns1 = common_factor + np.random.normal(0, 0.008, n_days)
    prices1 = 100 * np.exp(np.cumsum(returns1))
    
    # Ticker 2 (correlated)
    returns2 = common_factor * 0.9 + np.random.normal(0, 0.008, n_days)
    prices2 = 100 * np.exp(np.cumsum(returns2))
    
    return pd.DataFrame({
        'close_1': prices1,
        'close_2': prices2
    }, index=dates)

def backtest_pairs_trading(df, ticker1, ticker2):
    """Backtest pairs trading strategy"""
    # Calculate spread
    df['ratio'] = df['close_1'] / df['close_2']
    df['ratio_ma'] = df['ratio'].rolling(20).mean()
    df['ratio_std'] = df['ratio'].rolling(20).std()
    df['z_score'] = (df['ratio'] - df['ratio_ma']) / df['ratio_std']
    
    HOLD_DAYS = 5
    trades = []
    in_position = False
    position_type = None  # 'long_spread' or 'short_spread'
    entry_date = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if pd.isna(row['z_score']):
            continue
        
        # Entry signals
        if not in_position:
            if row['z_score'] > 2.0:  # Spread too high, expect reversion
                in_position = True
                position_type = 'short_spread'  # Short 1, Long 2
                entry_date = df.index[i]
                entry_ratio = row['ratio']
            elif row['z_score'] < -2.0:  # Spread too low
                in_position = True
                position_type = 'long_spread'  # Long 1, Short 2
                entry_date = df.index[i]
                entry_ratio = row['ratio']
        
        # Exit
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            
            # Exit on reversion or time limit
            exit_signal = abs(row['z_score']) < 0.5 or days_held >= HOLD_DAYS
            
            if exit_signal:
                exit_ratio = row['ratio']
                
                if position_type == 'long_spread':
                    pnl = (exit_ratio - entry_ratio) / entry_ratio * 100
                else:
                    pnl = (entry_ratio - exit_ratio) / entry_ratio * 100
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[i],
                    'pnl': pnl,
                    'type': position_type
                })
                
                in_position = False
                position_type = None
                entry_date = None
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    analytics = BacktestAnalytics()
    
    metrics = analytics.calculate_metrics(trades_df, hold_days=HOLD_DAYS)
    mc_metrics = analytics.monte_carlo_simulation(trades_df, n_simulations=1000, hold_days=HOLD_DAYS)
    cost_metrics = analytics.transaction_cost_sensitivity(trades_df, hold_days=HOLD_DAYS)
    
    return {
        'pair': f"{ticker1}/{ticker2}",
        'metrics': metrics,
        'mc_metrics': mc_metrics,
        'cost_metrics': cost_metrics
    }

def main():
    print("=" * 80)
    print("H015-012: PAIRS TRADING (MEAN REVERSION)")
    print("=" * 80)
    print("Logic: Long underperformer, short outperformer when Z-score > 2")
    print("Exit: Z-score < 0.5 or 5 days")
    print("=" * 80)
    
    results = []
    
    for ticker1, ticker2 in PAIRS:
        print(f"\n🧪 Testing {ticker1}/{ticker2}...")
        
        df = simulate_pair_data(ticker1, ticker2)
        test_df = df[(df.index >= TEST_START) & (df.index <= TEST_END)]
        
        result = backtest_pairs_trading(test_df, ticker1, ticker2)
        
        if result is None:
            print(f"  ❌ No trades")
            continue
        
        m = result['metrics']
        mc = result['mc_metrics']
        
        print(f"  Trades: {m['total_trades']} | WR: {m['win_rate']:.1f}% | Return: {m['total_return_pct']:+.2f}%")
        print(f"  MC Robust: {mc['mc_robustness_score']:.1f}%")
        
        # Quick score
        score = 0
        if m['win_rate'] >= 55: score += 1
        if m['expectancy'] > 0: score += 1
        if mc['mc_robustness_score'] >= 70: score += 1
        
        print(f"  Quick Score: {score}/3")
        
        if score >= 2:
            print(f"  ⭐ PROMISING")
        
        results.append(result)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    validated = [r for r in results if r['metrics']['win_rate'] >= 55 and r['mc_metrics']['mc_robustness_score'] >= 70]
    
    print(f"\nPairs tested: {len(results)}")
    print(f"Validated: {len(validated)}")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
