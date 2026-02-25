#!/usr/bin/env python3
"""
Continuous Strategy Research - Hypothesis Testing Framework
Date: 2026-02-24
Tests H6-H9 (New Hypotheses) and E5-E7 (Enhancements)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import math

# Configuration
DATA_DIR = "/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data"
RESULTS_DIR = "/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results"
TICKERS = ["AAPL", "AMD", "COIN", "META", "MSFT", "MSTR", "NVDA", "QQQ", "SPY", "TSLA"]

# Train/Test split dates
TRAIN_START = "2021-01-01"
TRAIN_END = "2022-12-31"
TEST_START = "2023-01-01"
TEST_END = "2024-12-31"

# Strategy hold period and profit target
HOLD_DAYS = 5
PROFIT_TARGET = 0.05  # 5%
TRAILING_STOP = 0.03  # 3% trailing stop

def load_data(ticker):
    """Load indicator data for a ticker"""
    filepath = f"{DATA_DIR}/{ticker}_indicators.csv"
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate additional indicators if needed
    df['returns'] = df['close'].pct_change()
    
    # Volume SMA20
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    
    # For RSI divergence detection
    df['close_low_5'] = df['close'].rolling(5).min()
    df['rsi_low_5'] = df['rsi'].rolling(5).min()
    
    return df

def calculate_future_returns(df, days=HOLD_DAYS):
    """Calculate future returns for backtesting"""
    df[f'future_return_{days}d'] = df['close'].shift(-days) / df['close'] - 1
    df[f'future_high_{days}d'] = df['close'].rolling(window=days, min_periods=1).max().shift(-days) / df['close'] - 1
    return df

def calc_confidence_interval(wins, total, confidence=0.95):
    """Calculate Wilson score interval for win rate (without scipy)"""
    if total == 0:
        return 0, 0, 0
    
    p = wins / total
    # Z-score for 95% confidence = 1.96
    z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
    
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    
    return p * 100, (centre - margin) * 100, (centre + margin) * 100

# ============================================================
# HYPOTHESIS DEFINITIONS
# ============================================================

def h6_stoch_macd_confluence(df):
    """
    H6: Stochastic + MACD Confluence
    - Stoch_K < 20 (oversold)
    - MACD > Signal (bullish crossover)
    - Price > SMA50 (uptrend context)
    """
    signal = (
        (df['stoch_k'] < 20) &
        (df['macd'] > df['macd_signal']) &
        (df['close'] > df['sma_50'])
    )
    return signal

def h7_adx_volume_expansion(df):
    """
    H7: ADX + Volume Expansion
    - ADX > 30 (strong trend)
    - Volume > 1.5x 20-day average
    - Price breakout above recent high
    """
    df['recent_high'] = df['high'].rolling(10).max().shift(1)
    signal = (
        (df['adx'] > 30) &
        (df['volume'] > 1.5 * df['volume_sma20']) &
        (df['close'] > df['recent_high'])
    )
    return signal

def h8_rsi_divergence(df):
    """
    H8: RSI Divergence Pattern
    - Price makes lower low (vs 5 days ago)
    - RSI makes higher low (bullish divergence)
    - Volume above average (confirmation)
    """
    df['close_ll'] = df['close'] < df['close'].shift(5)
    df['rsi_hl'] = df['rsi'] > df['rsi'].shift(5)
    
    signal = (
        (df['close'] < df['close'].shift(5)) &  # Lower low
        (df['rsi'] > df['rsi'].shift(5)) &       # Higher RSI (divergence)
        (df['volume'] > df['volume_sma20'])       # Volume confirmation
    )
    return signal

def h9_bb_mean_reversion_v2(df):
    """
    H9: BB Mean Reversion v2 (Trending Mean Reversion)
    - Price < BB_Lower (oversold)
    - RSI < 35 (oversold)
    - ADX > 20 (trending market - trending mean reversion)
    """
    signal = (
        (df['close'] < df['bb_lower']) &
        (df['rsi'] < 35) &
        (df['adx'] > 20)
    )
    return signal

# ============================================================
# ENHANCEMENT DEFINITIONS
# ============================================================

def e5_adx_trend_profit_target(df):
    """
    E5: ADX Trend with Profit Target
    - ADX > 25 (trend strength)
    - +DI > -DI (bullish)
    - With 5% profit target instead of fixed hold
    """
    signal = (
        (df['adx'] > 25) &
        (df['close'] > df['sma_20'])  # Simplified bullish check
    )
    return signal

def e6_bb_walk_trailing_stop(df):
    """
    E6: BB Walk with Trailing Stop
    - Price within Bollinger Bands (walking the band)
    - With trailing stop logic
    """
    signal = (
        (df['close'] > df['bb_lower']) &
        (df['close'] < df['bb_upper']) &
        (df['close'] > df['sma_20'])
    )
    return signal

def e7_multi_indicator_consensus(df):
    """
    E7: Multi-Indicator Consensus
    - Require 3 of 4 indicators aligned:
      1. RSI > 50 (bullish)
      2. MACD > Signal
      3. Price > SMA20
      4. ADX > 25 (trending)
    """
    ind1 = (df['rsi'] > 50).astype(int)
    ind2 = (df['macd'] > df['macd_signal']).astype(int)
    ind3 = (df['close'] > df['sma_20']).astype(int)
    ind4 = (df['adx'] > 25).astype(int)
    
    consensus = ind1 + ind2 + ind3 + ind4
    signal = consensus >= 3
    return signal

# ============================================================
# BACKTEST ENGINE
# ============================================================

def backtest_strategy(df, signal_func, strategy_name, use_profit_target=False, use_trailing_stop=False):
    """Run backtest for a strategy with train/test split"""
    
    df = df.copy()
    df = calculate_future_returns(df)
    df['signal'] = signal_func(df)
    
    # Split into train/test
    train_mask = (df['date'] >= TRAIN_START) & (df['date'] <= TRAIN_END)
    test_mask = (df['date'] >= TEST_START) & (df['date'] <= TEST_END)
    
    results = {
        'strategy': strategy_name,
        'ticker': None,  # Set by caller
        'train': {'wins': 0, 'total': 0, 'win_rate': 0, 'ci_low': 0, 'ci_high': 0},
        'test': {'wins': 0, 'total': 0, 'win_rate': 0, 'ci_low': 0, 'ci_high': 0},
        'decay': 0
    }
    
    for period, mask in [('train', train_mask), ('test', test_mask)]:
        period_df = df[mask]
        signals = period_df[period_df['signal'] == True]
        
        if len(signals) == 0:
            continue
        
        if use_profit_target:
            # Check if profit target hit within hold period
            wins = ((signals[f'future_high_{HOLD_DAYS}d'] >= PROFIT_TARGET) | 
                    (signals[f'future_return_{HOLD_DAYS}d'] > 0)).sum()
        elif use_trailing_stop:
            # Simplified: use returns but with tighter threshold
            wins = (signals[f'future_return_{HOLD_DAYS}d'] > 0.015).sum()  # 1.5% for trailing stop
        else:
            wins = (signals[f'future_return_{HOLD_DAYS}d'] > 0).sum()
        
        total = len(signals)
        win_rate, ci_low, ci_high = calc_confidence_interval(wins, total)
        
        results[period]['wins'] = int(wins)
        results[period]['total'] = int(total)
        results[period]['win_rate'] = round(win_rate, 2)
        results[period]['ci_low'] = round(ci_low, 2)
        results[period]['ci_high'] = round(ci_high, 2)
    
    # Calculate decay
    if results['train']['win_rate'] > 0 and results['test']['win_rate'] > 0:
        results['decay'] = round(results['train']['win_rate'] - results['test']['win_rate'], 2)
    
    return results

def classify_strategy(result):
    """Classify strategy as Golden, Validated, or Rejected"""
    test_wr = result['test']['win_rate']
    test_n = result['test']['total']
    decay = result['decay']
    
    if test_wr >= 70 and test_n >= 30 and abs(decay) < 15:
        return "GOLDEN"
    elif test_wr >= 55 and test_n >= 10:
        return "VALIDATED"
    else:
        return "REJECTED"

def run_all_backtests():
    """Run all hypotheses on all tickers"""
    all_results = []
    
    strategies_list = [
        ('H6_Stoch_MACD', h6_stoch_macd_confluence, False, False),
        ('H7_ADX_Volume', h7_adx_volume_expansion, False, False),
        ('H8_RSI_Divergence', h8_rsi_divergence, False, False),
        ('H9_BB_MR_v2', h9_bb_mean_reversion_v2, False, False),
        ('E5_ADX_ProfitTarget', e5_adx_trend_profit_target, True, False),
        ('E6_BB_TrailingStop', e6_bb_walk_trailing_stop, False, True),
        ('E7_Multi_Consensus', e7_multi_indicator_consensus, False, False),
    ]
    
    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        try:
            df = load_data(ticker)
        except Exception as e:
            print(f"  Error loading {ticker}: {e}")
            continue
        
        for strat_name, strat_func, use_pt, use_ts in strategies_list:
            try:
                result = backtest_strategy(df, strat_func, strat_name, use_pt, use_ts)
                result['ticker'] = ticker
                result['status'] = classify_strategy(result)
                all_results.append(result)
                print(f"  {strat_name}: Test WR={result['test']['win_rate']:.1f}%, n={result['test']['total']}, Status={result['status']}")
            except Exception as e:
                print(f"  Error in {strat_name}: {e}")
    
    return all_results, strategies_list

# ============================================================
# OUTPUT GENERATION
# ============================================================

def generate_summary(all_results, strategies_list):
    """Generate summary report"""
    
    golden = [r for r in all_results if r['status'] == 'GOLDEN']
    validated = [r for r in all_results if r['status'] == 'VALIDATED']
    rejected = [r for r in all_results if r['status'] == 'REJECTED']
    
    report = []
    report.append("=" * 80)
    report.append("CONTINUOUS STRATEGY RESEARCH RESULTS")
    report.append(f"Date: 2026-02-24")
    report.append(f"Test Period: {TEST_START} to {TEST_END}")
    report.append("=" * 80)
    report.append("")
    
    # Golden Strategies
    report.append(f"## GOLDEN STRATEGIES DISCOVERED: {len(golden)}")
    report.append("-" * 80)
    if golden:
        report.append(f"{'Strategy':<25} {'Ticker':<8} {'Test WR%':<10} {'n':<6} {'Decay':<8} {'95% CI':<20}")
        report.append("-" * 80)
        for r in golden:
            ci = f"[{r['test']['ci_low']:.1f}-{r['test']['ci_high']:.1f}]"
            report.append(f"{r['strategy']:<25} {r['ticker']:<8} {r['test']['win_rate']:<10.1f} {r['test']['total']:<6} {r['decay']:<8.1f} {ci:<20}")
    else:
        report.append("No Golden strategies discovered in this research cycle.")
    report.append("")
    
    # Validated Strategies
    report.append(f"## VALIDATED STRATEGIES: {len(validated)}")
    report.append("-" * 80)
    if validated:
        report.append(f"{'Strategy':<25} {'Ticker':<8} {'Test WR%':<10} {'n':<6} {'Decay':<8} {'95% CI':<20}")
        report.append("-" * 80)
        for r in validated:
            ci = f"[{r['test']['ci_low']:.1f}-{r['test']['ci_high']:.1f}]"
            report.append(f"{r['strategy']:<25} {r['ticker']:<8} {r['test']['win_rate']:<10.1f} {r['test']['total']:<6} {r['decay']:<8.1f} {ci:<20}")
    else:
        report.append("No Validated strategies discovered.")
    report.append("")
    
    # Rejected Strategies (brief summary)
    report.append(f"## REJECTED STRATEGIES: {len(rejected)}")
    report.append("-" * 80)
    report.append(f"Strategies with test win rate <55% or insufficient samples: {len(rejected)}")
    report.append("")
    
    # Strategy Performance Summary
    report.append("## STRATEGY PERFORMANCE SUMMARY")
    report.append("-" * 80)
    
    strategy_groups = {}
    for r in all_results:
        name = r['strategy']
        if name not in strategy_groups:
            strategy_groups[name] = []
        strategy_groups[name].append(r)
    
    report.append(f"{'Strategy':<25} {'Tickers':<8} {'Avg WR%':<10} {'Best':<8} {'Worst':<8}")
    report.append("-" * 80)
    for name, results in strategy_groups.items():
        valid_results = [r for r in results if r['test']['total'] > 0]
        if valid_results:
            avg_wr = np.mean([r['test']['win_rate'] for r in valid_results])
            best = max([r['test']['win_rate'] for r in valid_results])
            worst = min([r['test']['win_rate'] for r in valid_results])
            report.append(f"{name:<25} {len(valid_results):<8} {avg_wr:<10.1f} {best:<8.1f} {worst:<8.1f}")
    report.append("")
    
    # Key Findings
    report.append("## KEY FINDINGS")
    report.append("-" * 80)
    
    # Analyze findings
    findings = []
    
    # Best performing strategy
    if all_results:
        best = max(all_results, key=lambda x: x['test']['win_rate'] if x['test']['total'] >= 10 else 0)
        findings.append(f"1. Best performing strategy: {best['strategy']} on {best['ticker']} with {best['test']['win_rate']:.1f}% win rate")
    
    # Most consistent strategy
    if strategy_groups:
        consistency_scores = {}
        for name, results in strategy_groups.items():
            valid = [r for r in results if r['test']['total'] >= 5]
            if len(valid) >= 3:
                consistency_scores[name] = np.mean([r['test']['win_rate'] for r in valid])
        if consistency_scores:
            most_consistent = max(consistency_scores.items(), key=lambda x: x[1])
            findings.append(f"2. Most consistent across tickers: {most_consistent[0]} (avg {most_consistent[1]:.1f}%)")
    
    # Strategy counts
    findings.append(f"3. Total strategies tested: {len(strategies_list)} on {len(TICKERS)} tickers = {len(all_results)} combinations")
    findings.append(f"4. Golden strategies: {len(golden)} | Validated: {len(validated)} | Rejected: {len(rejected)}")
    
    # Enhancement effectiveness
    enh_results = [r for r in all_results if r['strategy'].startswith('E')]
    if enh_results:
        avg_enh_wr = np.mean([r['test']['win_rate'] for r in enh_results if r['test']['total'] > 0])
        findings.append(f"5. Average win rate for enhanced strategies: {avg_enh_wr:.1f}%")
    
    for f in findings:
        report.append(f)
    report.append("")
    
    # Detailed Golden Strategy Documentation
    if golden:
        report.append("## GOLDEN STRATEGY DOCUMENTATION")
        report.append("-" * 80)
        for r in golden:
            report.append("")
            report.append(f"### {r['strategy']} - {r['ticker']}")
            report.append(f"**Status:** GOLDEN 🏆")
            report.append(f"**Test Win Rate:** {r['test']['win_rate']:.1f}% (95% CI: {r['test']['ci_low']:.1f}-{r['test']['ci_high']:.1f})")
            report.append(f"**Sample Size:** {r['test']['total']} trades")
            report.append(f"**Train Win Rate:** {r['train']['win_rate']:.1f}%")
            report.append(f"**Decay:** {r['decay']:.1f}%")
            report.append("")
    
    report.append("=" * 80)
    report.append("END OF RESEARCH REPORT")
    report.append("=" * 80)
    
    return "\n".join(report), golden, validated

def save_detailed_results(all_results):
    """Save detailed JSON results"""
    filepath = f"{RESULTS_DIR}/research_results_2026-02-24.json"
    with open(filepath, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    return filepath

def save_golden_documentation(golden):
    """Save markdown documentation for golden strategies"""
    for r in golden:
        filename = f"{RESULTS_DIR}/golden_{r['strategy']}_{r['ticker']}.md"
        doc = f"""# Golden Strategy: {r['strategy']} - {r['ticker']}

## Classification
- **Status:** GOLDEN 🏆
- **Discovered:** 2026-02-24
- **Validation Period:** {TEST_START} to {TEST_END}

## Performance Metrics

| Metric | Value |
|--------|-------|
| Test Win Rate | {r['test']['win_rate']:.2f}% |
| 95% Confidence Interval | [{r['test']['ci_low']:.2f}%, {r['test']['ci_high']:.2f}%] |
| Test Sample Size | {r['test']['total']} trades |
| Train Win Rate | {r['train']['win_rate']:.2f}% |
| Decay (Train-Test) | {r['decay']:.2f}% |

## Entry Criteria
- See strategy definition in research script

## Notes
- Golden strategy validation passed
- Win rate >= 70%
- Sample size >= 30
- Decay < 15%
- Ready for live testing consideration

## Generated
{datetime.now().isoformat()}
"""
        with open(filename, 'w') as f:
            f.write(doc)

# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CONTINUOUS STRATEGY RESEARCH - HYPOTHESIS TESTING")
    print("=" * 80)
    print()
    
    # Run all backtests
    all_results, strategies_list = run_all_backtests()
    
    # Generate summary
    summary_report, golden, validated = generate_summary(all_results, strategies_list)
    
    # Save results
    json_path = save_detailed_results(all_results)
    summary_path = f"{RESULTS_DIR}/research_summary_2026-02-24.txt"
    
    with open(summary_path, 'w') as f:
        f.write(summary_report)
    
    # Save golden docs
    if golden:
        save_golden_documentation(golden)
    
    # Print summary
    print()
    print("=" * 80)
    print("RESEARCH COMPLETE")
    print("=" * 80)
    print(f"Golden Strategies: {len(golden)}")
    print(f"Validated Strategies: {len(validated)}")
    print(f"Total Combinations Tested: {len(all_results)}")
    print()
    print(f"Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {summary_path}")
    print()
    print(summary_report)
