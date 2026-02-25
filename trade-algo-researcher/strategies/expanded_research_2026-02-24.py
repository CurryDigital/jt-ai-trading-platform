#!/usr/bin/env python3
"""
Continuous Strategy Research - Expanded Hypothesis Testing
Date: 2026-02-24 (14:00 UTC Run)
Tests: H12-H16 (New Hypotheses) + Bearish Strategies + Multi-timeframe
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

# Configuration
DATA_DIR = "/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data"
RESULTS_DIR = "/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results"
TICKERS = ["AAPL", "AMD", "COIN", "META", "MSFT", "MSTR", "NVDA", "QQQ", "SPY", "TSLA"]

# Train/Test split dates
TRAIN_START = "2021-01-01"
TRAIN_END = "2022-12-31"
TEST_START = "2023-01-01"
TEST_END = "2024-12-31"

# Strategy parameters
HOLD_DAYS = 5
PROFIT_TARGET = 0.05
SHORT_PROFIT_TARGET = 0.04  # 4% for shorts (asymmetric)

def load_data(ticker):
    """Load indicator data for a ticker"""
    filepath = f"{DATA_DIR}/{ticker}_indicators.csv"
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate additional indicators
    df['returns'] = df['close'].pct_change()
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    
    # Multi-timeframe indicators
    df['sma_10'] = df['close'].rolling(10).mean()
    df['rsi_7'] = calculate_rsi(df['close'], 7)  # Faster RSI
    
    # BB position (0-1 where 0=lower, 1=upper)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # Rate of change
    df['roc_5'] = df['close'].pct_change(5)
    df['roc_10'] = df['close'].pct_change(10)
    
    # Volatility regime
    df['atr_14'] = calculate_atr(df, 14)
    df['atr_percent'] = df['atr_14'] / df['close'] * 100
    
    return df

def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_future_returns(df, days=HOLD_DAYS):
    """Calculate future returns for backtesting"""
    df[f'future_return_{days}d'] = df['close'].shift(-days) / df['close'] - 1
    df[f'future_high_{days}d'] = df['close'].rolling(window=days, min_periods=1).max().shift(-days) / df['close'] - 1
    df[f'future_low_{days}d'] = df['close'].rolling(window=days, min_periods=1).min().shift(-days) / df['close'] - 1
    return df

def calc_confidence_interval(wins, total, confidence=0.95):
    """Calculate Wilson score interval"""
    if total == 0:
        return 0, 0, 0
    
    p = wins / total
    z = 1.96 if confidence == 0.95 else 2.576
    
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    
    return p * 100, (centre - margin) * 100, (centre + margin) * 100

# ============================================================
# NEW HYPOTHESIS DEFINITIONS (H12-H16)
# ============================================================

def h12_bb_squeeze_momentum(df):
    """
    H12: BB Squeeze + Momentum Breakout
    - BB width < 15% of price (squeeze)
    - Close above upper band (breakout)
    - Volume > 1.2x average
    """
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close'] * 100
    signal = (
        (df['bb_width'] < 15) &  # Squeeze
        (df['close'] > df['bb_upper']) &  # Breakout
        (df['volume'] > 1.2 * df['volume_sma20'])  # Volume confirmation
    )
    return signal

def h13_volatility_compression_breakout(df):
    """
    H13: Volatility Compression Breakout
    - ATR% < 2.5% (low volatility)
    - ATR% expanding (current > previous 3-day avg)
    - Close > SMA20 (bullish breakout)
    """
    df['atr_percent_avg3'] = df['atr_percent'].rolling(3).mean().shift(1)
    signal = (
        (df['atr_percent'] < 2.5) &  # Low vol regime
        (df['atr_percent'] > df['atr_percent_avg3']) &  # Expanding
        (df['close'] > df['sma_20'])  # Above key MA
    )
    return signal

def h14_rsi_fast_slow_convergence(df):
    """
    H14: RSI Fast/Slow Convergence
    - RSI(7) > RSI(14) (short-term momentum accelerating)
    - RSI(14) > 50 (bullish)
    - Price > SMA20
    """
    signal = (
        (df['rsi_7'] > df['rsi']) &  # Fast > Slow
        (df['rsi'] > 50) &  # Bullish
        (df['close'] > df['sma_20'])
    )
    return signal

def h15_adx_macd_combo(df):
    """
    H15: ADX + MACD Combo (Refined Trend Following)
    - ADX > 25 (trending)
    - MACD > Signal (bullish)
    - MACD histogram increasing (momentum accelerating)
    """
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_hist_prev'] = df['macd_hist'].shift(1)
    signal = (
        (df['adx'] > 25) &
        (df['macd'] > df['macd_signal']) &
        (df['macd_hist'] > df['macd_hist_prev']) &  # Accelerating
        (df['close'] > df['sma_20'])
    )
    return signal

def h16_multi_timeframe_trend(df):
    """
    H16: Multi-Timeframe Trend Alignment
    - Price > SMA10 (short-term)
    - Price > SMA20 (medium-term)
    - Price > SMA50 (long-term)
    - All MAs aligned upward (SMA10 > SMA20 > SMA50)
    """
    signal = (
        (df['close'] > df['sma_10']) &
        (df['close'] > df['sma_20']) &
        (df['close'] > df['sma_50']) &
        (df['sma_10'] > df['sma_20']) &
        (df['sma_20'] > df['sma_50'])
    )
    return signal

# ============================================================
# BEARISH (SHORT) STRATEGIES (B1-B4)
# ============================================================

def b1_adx_trend_short(df):
    """
    B1: ADX Trend Short
    - ADX > 25 (strong trend)
    - Close < SMA20 (downtrend)
    - RSI > 50 (weak bounce to short)
    """
    signal = (
        (df['adx'] > 25) &
        (df['close'] < df['sma_20']) &
        (df['rsi'] > 50) &
        (df['rsi'] < 65)  # Not oversold
    )
    return signal

def b2_bb_upper_rejection(df):
    """
    B2: BB Upper Band Rejection (Mean Reversion Short)
    - Close > 0.95 * BB_Upper (near upper band)
    - RSI > 65 (overbought)
    - Bearish candle (close < open)
    """
    df['bearish'] = df['close'] < df['open']
    signal = (
        (df['close'] > 0.95 * df['bb_upper']) &
        (df['rsi'] > 65) &
        (df['bearish'] == True)
    )
    return signal

def b3_momentum_divergence_short(df):
    """
    B3: Momentum Divergence Short
    - Price makes higher high
    - RSI makes lower high (bearish divergence)
    - Volume declining (weak momentum)
    """
    df['price_hh'] = df['close'] > df['close'].shift(5)
    df['rsi_lh'] = df['rsi'] < df['rsi'].shift(5)
    df['vol_decline'] = df['volume'] < df['volume_sma20']
    signal = (
        (df['price_hh'] == True) &
        (df['rsi_lh'] == True) &
        (df['vol_decline'] == True) &
        (df['rsi'] > 60)  # From overbought area
    )
    return signal

def b4_volatility_expansion_short(df):
    """
    B4: Volatility Expansion Short
    - ATR% > 3.5% (high volatility)
    - Close < SMA20 (bearish)
    - Volume spike > 1.5x average
    """
    signal = (
        (df['atr_percent'] > 3.5) &
        (df['close'] < df['sma_20']) &
        (df['volume'] > 1.5 * df['volume_sma20'])
    )
    return signal

# ============================================================
# ENHANCED EXIT STRATEGIES
# ============================================================

def e8_atr_based_profit_target(df):
    """
    E8: ATR-Based Dynamic Profit Target
    - Entry when ADX > 25 + Price > SMA20
    - Exit at 2x ATR profit target (adaptive)
    """
    signal = (
        (df['adx'] > 25) &
        (df['close'] > df['sma_20'])
    )
    return signal, 'atr_based'  # Flag for special handling

def e9_time_based_exit(df):
    """
    E9: Time-Based Exit Optimization
    - Standard entry (ADX > 25, Price > SMA20)
    - Test 3-day hold vs 5-day vs 10-day
    """
    signal = (
        (df['adx'] > 25) &
        (df['close'] > df['sma_20'])
    )
    return signal

# ============================================================
# BACKTEST ENGINE
# ============================================================

def backtest_strategy(df, signal_func, strategy_name, exit_type='fixed', hold_days=HOLD_DAYS, is_short=False):
    """Run backtest with various exit types"""
    
    df = df.copy()
    df = calculate_future_returns(df, hold_days)
    
    # Handle tuple return for special exit types
    if isinstance(signal_func(df), tuple):
        df['signal'] = signal_func(df)[0]
        exit_type = signal_func(df)[1]
    else:
        df['signal'] = signal_func(df)
    
    # Split into train/test
    train_mask = (df['date'] >= TRAIN_START) & (df['date'] <= TRAIN_END)
    test_mask = (df['date'] >= TEST_START) & (df['date'] <= TEST_END)
    
    results = {
        'strategy': strategy_name,
        'ticker': None,
        'exit_type': exit_type,
        'hold_days': hold_days,
        'is_short': is_short,
        'train': {'wins': 0, 'total': 0, 'win_rate': 0, 'ci_low': 0, 'ci_high': 0, 'avg_return': 0},
        'test': {'wins': 0, 'total': 0, 'win_rate': 0, 'ci_low': 0, 'ci_high': 0, 'avg_return': 0},
        'decay': 0
    }
    
    for period, mask in [('train', train_mask), ('test', test_mask)]:
        period_df = df[mask]
        signals = period_df[period_df['signal'] == True]
        
        if len(signals) == 0:
            continue
        
        # Calculate wins based on exit type
        if is_short:
            # For shorts, profit when price goes down
            if exit_type == 'profit_target':
                wins = ((signals[f'future_low_{hold_days}d'] <= -SHORT_PROFIT_TARGET) | 
                        (signals[f'future_return_{hold_days}d'] < 0)).sum()
            else:
                wins = (signals[f'future_return_{hold_days}d'] < 0).sum()
            returns = -signals[f'future_return_{hold_days}d']  # Invert for short P&L
        else:
            # For longs
            if exit_type == 'profit_target':
                wins = ((signals[f'future_high_{hold_days}d'] >= PROFIT_TARGET) | 
                        (signals[f'future_return_{hold_days}d'] > 0)).sum()
            elif exit_type == 'atr_based':
                # 2x ATR target
                atr_target = signals['atr_percent'] * 2 / 100
                hits_target = signals[f'future_high_{hold_days}d'] >= atr_target
                wins = (hits_target | (signals[f'future_return_{hold_days}d'] > 0)).sum()
            else:
                wins = (signals[f'future_return_{hold_days}d'] > 0).sum()
            returns = signals[f'future_return_{hold_days}d']
        
        total = len(signals)
        win_rate, ci_low, ci_high = calc_confidence_interval(wins, total)
        avg_return = returns.mean() * 100 if len(returns) > 0 else 0
        
        results[period]['wins'] = int(wins)
        results[period]['total'] = int(total)
        results[period]['win_rate'] = round(win_rate, 2)
        results[period]['ci_low'] = round(ci_low, 2)
        results[period]['ci_high'] = round(ci_high, 2)
        results[period]['avg_return'] = round(avg_return, 3)
    
    # Calculate decay
    if results['train']['win_rate'] > 0 and results['test']['win_rate'] > 0:
        results['decay'] = round(results['train']['win_rate'] - results['test']['win_rate'], 2)
    
    return results

def classify_strategy(result):
    """Classify strategy with appropriate thresholds for shorts"""
    test_wr = result['test']['win_rate']
    test_n = result['test']['total']
    decay = result['decay']
    is_short = result.get('is_short', False)
    
    # Shorts typically have lower win rates but higher RR
    threshold = 65 if is_short else 70
    
    if test_wr >= threshold and test_n >= 30 and abs(decay) < 15:
        return "GOLDEN"
    elif test_wr >= 55 and test_n >= 10:
        return "VALIDATED"
    else:
        return "REJECTED"

def run_all_backtests():
    """Run all hypotheses on all tickers"""
    all_results = []
    
    # Define strategies: (name, function, exit_type, hold_days, is_short)
    strategies_list = [
        # New Hypotheses H12-H16 (Long)
        ('H12_BB_Squeeze_Momentum', h12_bb_squeeze_momentum, 'fixed', 5, False),
        ('H13_Vol_Compression_BO', h13_volatility_compression_breakout, 'fixed', 5, False),
        ('H14_RSI_Fast_Slow', h14_rsi_fast_slow_convergence, 'fixed', 5, False),
        ('H15_ADX_MACD_Combo', h15_adx_macd_combo, 'fixed', 5, False),
        ('H16_Multi_TF_Trend', h16_multi_timeframe_trend, 'fixed', 5, False),
        
        # With profit target
        ('H12_BB_Squeeze_PT', h12_bb_squeeze_momentum, 'profit_target', 5, False),
        ('H15_ADX_MACD_PT', h15_adx_macd_combo, 'profit_target', 5, False),
        ('H16_Multi_TF_PT', h16_multi_timeframe_trend, 'profit_target', 5, False),
        
        # Bearish Strategies B1-B4
        ('B1_ADX_Trend_Short', b1_adx_trend_short, 'fixed', 5, True),
        ('B2_BB_Upper_Reject', b2_bb_upper_rejection, 'fixed', 5, True),
        ('B3_Momentum_Div_Short', b3_momentum_divergence_short, 'fixed', 5, True),
        ('B4_Vol_Expansion_Short', b4_volatility_expansion_short, 'fixed', 5, True),
        
        # Short with profit target
        ('B1_ADX_Short_PT', b1_adx_trend_short, 'profit_target', 5, True),
        ('B2_BB_Reject_PT', b2_bb_upper_rejection, 'profit_target', 5, True),
        
        # Time-based exits
        ('H15_ADX_MACD_3D', h15_adx_macd_combo, 'fixed', 3, False),
        ('H15_ADX_MACD_10D', h15_adx_macd_combo, 'fixed', 10, False),
    ]
    
    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        try:
            df = load_data(ticker)
        except Exception as e:
            print(f"  Error loading {ticker}: {e}")
            continue
        
        for strat_name, strat_func, exit_type, hold_days, is_short in strategies_list:
            try:
                result = backtest_strategy(df, strat_func, strat_name, exit_type, hold_days, is_short)
                result['ticker'] = ticker
                result['status'] = classify_strategy(result)
                all_results.append(result)
                
                short_tag = " [SHORT]" if is_short else ""
                print(f"  {strat_name}{short_tag}: Test WR={result['test']['win_rate']:.1f}%, n={result['test']['total']}, Status={result['status']}")
            except Exception as e:
                print(f"  Error in {strat_name}: {e}")
    
    return all_results, strategies_list

# ============================================================
# OUTPUT GENERATION
# ============================================================

def generate_summary(all_results, strategies_list):
    """Generate comprehensive summary report"""
    
    golden = [r for r in all_results if r['status'] == 'GOLDEN']
    validated = [r for r in all_results if r['status'] == 'VALIDATED']
    rejected = [r for r in all_results if r['status'] == 'REJECTED']
    
    # Separate shorts
    golden_shorts = [r for r in golden if r.get('is_short', False)]
    golden_longs = [r for r in golden if not r.get('is_short', False)]
    
    report = []
    report.append("=" * 90)
    report.append("EXPANDED CONTINUOUS STRATEGY RESEARCH RESULTS")
    report.append(f"Date: 2026-02-24 14:00 UTC")
    report.append(f"Test Period: {TEST_START} to {TEST_END}")
    report.append("=" * 90)
    report.append("")
    
    # Executive Summary
    report.append("## EXECUTIVE SUMMARY")
    report.append("-" * 90)
    report.append(f"**Total Tests Run:** {len(all_results)} hypothesis-ticker combinations")
    report.append(f"**Hypotheses Tested:** {len(strategies_list)} | **Tickers:** {len(TICKERS)}")
    report.append(f"")
    report.append(f"**Results:** 🏆 Golden: {len(golden)} | ⭐ Validated: {len(validated)} | ❌ Rejected: {len(rejected)}")
    report.append(f"**Long Strategies:** {len(golden_longs)} Golden | **Short Strategies:** {len(golden_shorts)} Golden")
    report.append("")
    
    # Golden Strategies - Long
    if golden_longs:
        report.append(f"## 🏆 GOLDEN LONG STRATEGIES: {len(golden_longs)}")
        report.append("-" * 90)
        report.append(f"{'Strategy':<28} {'Ticker':<8} {'Test WR%':<10} {'n':<6} {'Decay':<8} {'Avg Ret%':<10} {'95% CI':<20}")
        report.append("-" * 90)
        for r in golden_longs:
            ci = f"[{r['test']['ci_low']:.1f}-{r['test']['ci_high']:.1f}]"
            report.append(f"{r['strategy']:<28} {r['ticker']:<8} {r['test']['win_rate']:<10.1f} {r['test']['total']:<6} {r['decay']:<8.1f} {r['test']['avg_return']:<10.2f} {ci:<20}")
        report.append("")
    
    # Golden Strategies - Short
    if golden_shorts:
        report.append(f"## 🏆 GOLDEN SHORT STRATEGIES: {len(golden_shorts)}")
        report.append("-" * 90)
        report.append(f"{'Strategy':<28} {'Ticker':<8} {'Test WR%':<10} {'n':<6} {'Decay':<8} {'Avg Ret%':<10} {'95% CI':<20}")
        report.append("-" * 90)
        for r in golden_shorts:
            ci = f"[{r['test']['ci_low']:.1f}-{r['test']['ci_high']:.1f}]"
            report.append(f"{r['strategy']:<28} {r['ticker']:<8} {r['test']['win_rate']:<10.1f} {r['test']['total']:<6} {r['decay']:<8.1f} {r['test']['avg_return']:<10.2f} {ci:<20}")
        report.append("")
    
    # Validated Strategies
    if validated:
        report.append(f"## ⭐ VALIDATED STRATEGIES: {len(validated)}")
        report.append("-" * 90)
        report.append(f"{'Strategy':<28} {'Ticker':<8} {'Test WR%':<10} {'n':<6} {'Type':<10}")
        report.append("-" * 90)
        for r in validated[:20]:  # Show top 20
            type_tag = "SHORT" if r.get('is_short') else "LONG"
            report.append(f"{r['strategy']:<28} {r['ticker']:<8} {r['test']['win_rate']:<10.1f} {r['test']['total']:<6} {type_tag:<10}")
        if len(validated) > 20:
            report.append(f"... and {len(validated) - 20} more")
        report.append("")
    
    # Strategy Performance by Category
    report.append("## STRATEGY PERFORMANCE BY CATEGORY")
    report.append("-" * 90)
    
    categories = {
        'New Hypotheses (H12-H16)': [r for r in all_results if r['strategy'].startswith('H1') and not r.get('is_short')],
        'Bearish Strategies (B1-B4)': [r for r in all_results if r.get('is_short')],
        'Profit Target Variants': [r for r in all_results if 'PT' in r['strategy']],
        'Time-Based Exits': [r for r in all_results if r['hold_days'] != 5],
    }
    
    report.append(f"{'Category':<35} {'Tests':<8} {'Golden':<8} {'Validated':<10} {'Avg WR%':<10}")
    report.append("-" * 90)
    for cat_name, cat_results in categories.items():
        if cat_results:
            golden_count = len([r for r in cat_results if r['status'] == 'GOLDEN'])
            valid_count = len([r for r in cat_results if r['status'] == 'VALIDATED'])
            avg_wr = np.mean([r['test']['win_rate'] for r in cat_results if r['test']['total'] > 0])
            report.append(f"{cat_name:<35} {len(cat_results):<8} {golden_count:<8} {valid_count:<10} {avg_wr:<10.1f}")
    report.append("")
    
    # Best Performers
    report.append("## TOP PERFORMERS BY CATEGORY")
    report.append("-" * 90)
    
    # Best long strategy
    best_long = max([r for r in all_results if not r.get('is_short') and r['test']['total'] >= 10], 
                    key=lambda x: x['test']['win_rate'], default=None)
    if best_long:
        report.append(f"**Best Long Strategy:** {best_long['strategy']} on {best_long['ticker']}")
        report.append(f"  Test Win Rate: {best_long['test']['win_rate']:.1f}% | n={best_long['test']['total']} | Decay: {best_long['decay']:.1f}%")
        report.append("")
    
    # Best short strategy
    best_short = max([r for r in all_results if r.get('is_short') and r['test']['total'] >= 10], 
                     key=lambda x: x['test']['win_rate'], default=None)
    if best_short:
        report.append(f"**Best Short Strategy:** {best_short['strategy']} on {best_short['ticker']}")
        report.append(f"  Test Win Rate: {best_short['test']['win_rate']:.1f}% | n={best_short['test']['total']} | Decay: {best_short['decay']:.1f}%")
        report.append("")
    
    # Most consistent
    long_results = [r for r in all_results if not r.get('is_short') and r['test']['total'] >= 5]
    if long_results:
        strat_consistency = {}
        for r in long_results:
            name = r['strategy']
            if name not in strat_consistency:
                strat_consistency[name] = []
            strat_consistency[name].append(r['test']['win_rate'])
        
        most_consistent = max(strat_consistency.items(), 
                              key=lambda x: np.mean(x[1]) if len(x[1]) >= 3 else 0, default=(None, []))
        if most_consistent[0]:
            report.append(f"**Most Consistent Strategy:** {most_consistent[0]}")
            report.append(f"  Average across {len(most_consistent[1])} tickers: {np.mean(most_consistent[1]):.1f}%")
            report.append("")
    
    # Key Findings
    report.append("## KEY FINDINGS")
    report.append("-" * 90)
    
    findings = []
    
    # Finding 1: Short strategy viability
    short_performance = [r['test']['win_rate'] for r in all_results if r.get('is_short') and r['test']['total'] >= 5]
    if short_performance:
        avg_short_wr = np.mean(short_performance)
        findings.append(f"1. **Short Strategy Viability:** Average win rate for bearish strategies: {avg_short_wr:.1f}%")
        if golden_shorts:
            findings.append(f"   - {len(golden_shorts)} Golden short strategies discovered")
    
    # Finding 2: Profit target effectiveness
    pt_results = [r for r in all_results if 'PT' in r['strategy'] and r['test']['total'] >= 5]
    if pt_results:
        avg_pt_wr = np.mean([r['test']['win_rate'] for r in pt_results])
        findings.append(f"2. **Profit Target Effectiveness:** PT variants average {avg_pt_wr:.1f}% win rate")
    
    # Finding 3: Time-based exit comparison
    time_results_3d = [r for r in all_results if r['hold_days'] == 3 and r['test']['total'] >= 5]
    time_results_5d = [r for r in all_results if r['hold_days'] == 5 and r['test']['total'] >= 5]
    time_results_10d = [r for r in all_results if r['hold_days'] == 10 and r['test']['total'] >= 5]
    if time_results_3d and time_results_5d:
        avg_3d = np.mean([r['test']['win_rate'] for r in time_results_3d])
        avg_5d = np.mean([r['test']['win_rate'] for r in time_results_5d])
        findings.append(f"3. **Hold Period Comparison:** 3-day: {avg_3d:.1f}% | 5-day: {avg_5d:.1f}%")
    
    # Finding 4: Best hypothesis
    new_hyp_results = [r for r in all_results if r['strategy'].startswith('H') and r['test']['total'] >= 10]
    if new_hyp_results:
        best_new = max(new_hyp_results, key=lambda x: x['test']['win_rate'])
        findings.append(f"4. **Best New Hypothesis:** {best_new['strategy']} with {best_new['test']['win_rate']:.1f}% win rate")
    
    # Finding 5: Summary stats
    findings.append(f"5. **Statistical Summary:**")
    findings.append(f"   - Total combinations tested: {len(all_results)}")
    findings.append(f"   - Golden rate: {len(golden)/len(all_results)*100:.1f}%")
    findings.append(f"   - Validated rate: {len(validated)/len(all_results)*100:.1f}%")
    
    for f in findings:
        report.append(f)
    report.append("")
    
    # Deployment Recommendations
    report.append("## DEPLOYMENT RECOMMENDATIONS")
    report.append("-" * 90)
    
    if golden_longs:
        report.append("### Immediate Deployment (Long Strategies)")
        for r in golden_longs[:5]:
            report.append(f"- {r['strategy']} on {r['ticker']}: {r['test']['win_rate']:.1f}% WR, {r['test']['total']} trades")
        report.append("")
    
    if golden_shorts:
        report.append("### Immediate Deployment (Short Strategies)")
        for r in golden_shorts[:3]:
            report.append(f"- {r['strategy']} on {r['ticker']}: {r['test']['win_rate']:.1f}% WR, {r['test']['total']} trades")
        report.append("")
    
    if validated:
        report.append("### Monitor for Promotion (Validated)")
        top_validated = sorted(validated, key=lambda x: x['test']['win_rate'], reverse=True)[:5]
        for r in top_validated:
            report.append(f"- {r['strategy']} on {r['ticker']}: {r['test']['win_rate']:.1f}% WR, needs {30-r['test']['total']} more trades for Golden")
        report.append("")
    
    report.append("=" * 90)
    report.append("END OF EXPANDED RESEARCH REPORT")
    report.append("=" * 90)
    
    return "\n".join(report), golden, validated

def save_results(all_results, golden, validated):
    """Save all results to files"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    # JSON results
    json_path = f"{RESULTS_DIR}/expanded_research_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Golden strategies file
    golden_path = f"{RESULTS_DIR}/golden_strategies_{timestamp}.json"
    with open(golden_path, 'w') as f:
        json.dump(golden, f, indent=2, default=str)
    
    return json_path, golden_path

# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    print("=" * 90)
    print("EXPANDED CONTINUOUS STRATEGY RESEARCH")
    print("New Hypotheses + Bearish Strategies + Multi-timeframe Analysis")
    print("=" * 90)
    print()
    
    # Run all backtests
    all_results, strategies_list = run_all_backtests()
    
    # Generate summary
    summary_report, golden, validated = generate_summary(all_results, strategies_list)
    
    # Save results
    json_path, golden_path = save_results(all_results, golden, validated)
    summary_path = f"{RESULTS_DIR}/expanded_summary_{datetime.now().strftime('%Y-%m-%d_%H%M')}.txt"
    
    with open(summary_path, 'w') as f:
        f.write(summary_report)
    
    # Print summary
    print()
    print("=" * 90)
    print("RESEARCH COMPLETE")
    print("=" * 90)
    print(f"Golden Strategies: {len(golden)}")
    print(f"Validated Strategies: {len(validated)}")
    print(f"Total Combinations Tested: {len(all_results)}")
    print()
    print(f"Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {summary_path}")
    print()
    print(summary_report)
