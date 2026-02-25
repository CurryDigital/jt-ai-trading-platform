#!/usr/bin/env python3
"""
Continuous Strategy Research — Batch 2026-02-24
Test 3 new hypotheses with walk-forward validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Available tickers with data
TICKERS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'COIN', 'MSTR']

# Train/Test split dates
TRAIN_END = '2022-12-31'
TEST_START = '2023-01-01'

def load_data(ticker):
    """Load indicator data for a ticker"""
    df = pd.read_csv(f'data/{ticker}_indicators.csv', parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate additional indicators
    df['returns_1d'] = df['close'].pct_change()
    df['returns_5d'] = df['close'].pct_change(5)
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma20']
    df['price_above_sma20'] = df['close'] > df['sma_20']
    df['price_above_sma50'] = df['close'] > df['sma_50']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['atr_compression'] = df['atr_pct'] < df['atr_pct'].rolling(20).quantile(0.2)
    
    return df

def backtest_strategy(df, entry_mask, exit_days=5, ticker='UNKNOWN'):
    """
    Run walk-forward backtest
    entry_mask: boolean series indicating entry signals
    exit_days: hold period
    """
    results = []
    
    for i in range(len(df) - exit_days):
        if entry_mask.iloc[i] and not pd.isna(entry_mask.iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + exit_days]
            ret = (exit_price - entry_price) / entry_price
            
            results.append({
                'date': df['date'].iloc[i],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return': ret,
                'win': ret > 0
            })
    
    return pd.DataFrame(results)

def split_results(df, train_end=TRAIN_END):
    """Split results into train and test periods"""
    train = df[df['date'] <= train_end]
    test = df[df['date'] >= TEST_START]
    return train, test

def calculate_metrics(trades_df):
    """Calculate performance metrics with confidence intervals"""
    if len(trades_df) == 0:
        return {'win_rate': 0, 'n': 0, 'ci_lower': 0, 'ci_upper': 0, 'avg_return': 0}
    
    wins = trades_df['win'].sum()
    n = len(trades_df)
    win_rate = wins / n
    
    # 95% confidence interval using Wilson score
    z = 1.96
    p = win_rate
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2*n)) / denominator
    margin = z * np.sqrt((p * (1-p) + z**2 / (4*n)) / n) / denominator
    
    ci_lower = max(0, centre - margin)
    ci_upper = min(1, centre + margin)
    
    return {
        'win_rate': win_rate,
        'n': n,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'avg_return': trades_df['return'].mean(),
 'total_return': trades_df['return'].sum(),
        'sharpe': trades_df['return'].mean() / trades_df['return'].std() if trades_df['return'].std() > 0 else 0
    }

# ============================================
# HYPOTHESIS 1: MACD Histogram Reversal
# ============================================

def test_macd_histogram_reversal(df):
    """
    H1: MACD histogram turning positive from negative + ADX > 25
    Entry: MACD hist crosses above 0 + ADX > 25 (trend confirmation)
    Exit: 5-day hold
    """
    # MACD histogram crossing above zero (momentum shift)
    hist_positive = df['macd_hist'] > 0
    hist_prev_negative = df['macd_hist'].shift(1) < 0
    macd_cross = hist_positive & hist_prev_negative
    
    # ADX trend confirmation
    strong_trend = df['adx'] > 25
    
    # Combined signal
    entry = macd_cross & strong_trend & df['price_above_sma20']
    
    return backtest_strategy(df, entry, 5, 'MACD_Hist_Reversal')

# ============================================
# HYPOTHESIS 2: Volume Breakout with Pullback
# ============================================

def test_volume_breakout_pullback(df):
    """
    H2: High volume breakout followed by RSI pullback to support
    Entry: Price > SMA20 + Volume > 1.5x avg + RSI between 40-60 (pullback)
    Exit: 5-day hold
    """
    # Trend context
    uptrend = df['price_above_sma50'] & (df['close'] > df['sma_20'])
    
    # Volume confirmation
    high_volume = df['volume_ratio'] > 1.5
    
    # RSI in sweet spot (not overbought, not oversold — pullback)
    rsi_pullback = (df['rsi'] >= 40) & (df['rsi'] <= 60)
    
    # Combined signal
    entry = uptrend & high_volume & rsi_pullback
    
    return backtest_strategy(df, entry, 5, 'Volume_Breakout_Pullback')

# ============================================
# HYPOTHESIS 3: Bollinger Band Walk
# ============================================

def test_bb_walk(df):
    """
    H3: Price walking along BB upper band in strong trend
    Entry: Close > BB Upper * 0.98 + ADX > 30 + Price > SMA50
    Exit: 3-day hold (momentum burst)
    """
    # Near upper band
    near_upper = df['close'] > df['bb_upper'] * 0.98
    
    # Strong trend
    strong_trend = (df['adx'] > 30) & df['price_above_sma50']
    
    # Volume confirmation
    volume_confirm = df['volume_ratio'] > 1.0
    
    # Combined signal
    entry = near_upper & strong_trend & volume_confirm
    
    return backtest_strategy(df, entry, 3, 'BB_Walk')

# ============================================
# RUN ALL TESTS
# ============================================

def run_all_tests():
    """Run all hypotheses across all tickers"""
    
    results = {
        'H1_MACD_Hist_Reversal': {},
        'H2_Volume_Breakout_Pullback': {},
        'H3_BB_Walk': {}
    }
    
    print("=" * 80)
    print("CONTINUOUS STRATEGY RESEARCH — 2026-02-24")
    print("=" * 80)
    
    for ticker in TICKERS:
        print(f"\n🔍 Testing {ticker}...")
        
        try:
            df = load_data(ticker)
            
            # Test H1
            trades_h1 = test_macd_histogram_reversal(df)
            train_h1, test_h1 = split_results(trades_h1)
            
            results['H1_MACD_Hist_Reversal'][ticker] = {
                'train': calculate_metrics(train_h1),
                'test': calculate_metrics(test_h1),
                'decay': calculate_metrics(test_h1)['win_rate'] - calculate_metrics(train_h1)['win_rate']
            }
            
            # Test H2
            trades_h2 = test_volume_breakout_pullback(df)
            train_h2, test_h2 = split_results(trades_h2)
            
            results['H2_Volume_Breakout_Pullback'][ticker] = {
                'train': calculate_metrics(train_h2),
                'test': calculate_metrics(test_h2),
                'decay': calculate_metrics(test_h2)['win_rate'] - calculate_metrics(train_h2)['win_rate']
            }
            
            # Test H3
            trades_h3 = test_bb_walk(df)
            train_h3, test_h3 = split_results(trades_h3)
            
            results['H3_BB_Walk'][ticker] = {
                'train': calculate_metrics(train_h3),
                'test': calculate_metrics(test_h3),
                'decay': calculate_metrics(test_h3)['win_rate'] - calculate_metrics(train_h3)['win_rate']
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    return results

def print_summary(results):
    """Print formatted summary of results"""
    
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    for hypothesis, tickers in results.items():
        print(f"\n📊 {hypothesis}")
        print("-" * 80)
        print(f"{'Ticker':<8} {'Train WR%':<12} {'Test WR%':<12} {'n (test)':<10} {'Decay':<10} {'Status':<15}")
        print("-" * 80)
        
        for ticker, data in tickers.items():
            train_wr = data['train']['win_rate'] * 100
            test_wr = data['test']['win_rate'] * 100
            n = data['test']['n']
            decay = data['decay'] * 100
            
            # Determine status
            if test_wr >= 70 and n >= 30 and abs(decay) < 15:
                status = "🏆 GOLDEN"
            elif test_wr >= 55 and n >= 10:
                status = "✅ Validated"
            elif n < 10:
                status = "⚠️ Low n"
            else:
                status = "❌ Rejected"
            
            print(f"{ticker:<8} {train_wr:>6.1f}%      {test_wr:>6.1f}%      {n:<10} {decay:>+6.1f}%    {status}")

if __name__ == '__main__':
    results = run_all_tests()
    print_summary(results)
    
    # Save results
    with open('results/continuous_batch_2026-02-24.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Results saved to results/continuous_batch_2026-02-24.json")
