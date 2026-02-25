#!/usr/bin/env python3
"""
Continuous Strategy Research Batch - 2026-02-23 22:55 UTC
Focus: New Hypotheses, Enhancements, and Cross-Sector Validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Load all available data
def load_data():
    tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'META', 'AMD', 'TSLA', 'COIN', 'MSTR']
    data = {}
    for ticker in tickers:
        try:
            df = pd.read_csv(f'data/{ticker}_indicators.csv')
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Calculate true range
            df['prev_close'] = df['close'].shift(1)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['low'] - df['prev_close'])
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            data[ticker] = df
            print(f"Loaded {ticker}: {len(df)} records, {df['date'].min().date()} to {df['date'].max().date()}")
        except Exception as e:
            print(f"Failed to load {ticker}: {e}")
    return data

def walk_forward_split(df, train_end='2022-12-31'):
    """Split data into train (2021-2022) and test (2023-2024)"""
    train = df[df['date'] <= train_end].copy()
    test = df[df['date'] > train_end].copy()
    return train, test

def calculate_win_rate(returns):
    """Calculate win rate with confidence interval"""
    if not returns or len(returns) == 0:
        return 0.0, 0, 0.0, (0.0, 0.0)
    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / len(returns) * 100
    avg_return = float(np.mean(returns))
    # 95% CI using Wilson score
    n = len(returns)
    p = wins / n if n > 0 else 0
    z = 1.96
    ci_lower = max(0.0, (p + z**2/(2*n) - z*np.sqrt((p*(1-p) + z**2/(4*n))/n)) / (1 + z**2/n)) * 100 if n > 0 else 0.0
    ci_upper = min(100.0, (p + z**2/(2*n) + z*np.sqrt((p*(1-p) + z**2/(4*n))/n)) / (1 + z**2/n)) * 100 if n > 0 else 0.0
    return win_rate, n, avg_return, (ci_lower, ci_upper)

def test_rsi_macd_combo(df, rsi_thresh=35, hold_days=5):
    """RSI + MACD improving combo"""
    df = df.copy()
    signals = df[
        (df['rsi'] < rsi_thresh) & 
        (df['macd'] > df['macd_signal']) &
        (df['macd'] > df['macd'].shift(1))  # MACD improving
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        # Find position in dataframe
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_support_bounce(df, hold_days=5):
    """Bounce off 50-day SMA support"""
    df = df.copy()
    df['near_sma50'] = abs(df['close'] - df['sma_50']) / df['sma_50'] < 0.02
    df['above_sma200'] = df['close'] > df['sma_200']
    
    signals = df[
        (df['near_sma50']) & 
        (df['rsi'] < 45) &
        (df['above_sma200'])  # Only in uptrend
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_gap_fill(df, gap_thresh=-0.02, hold_days=3):
    """Gap and fill strategy"""
    df = df.copy()
    df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
    df['gap_down'] = df['gap'] < gap_thresh  # Gap down threshold
    
    signals = df[df['gap_down']].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']  # Enter at close of gap day
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_rsi_divergence(df, lookback=14, hold_days=5):
    """RSI Bullish Divergence"""
    df = df.copy()
    df['price_low'] = df['low'].rolling(lookback).min()
    df['rsi_low'] = df['rsi'].rolling(lookback).min()
    df['price_lower_low'] = df['low'] < df['price_low'].shift(1)
    df['rsi_higher_low'] = df['rsi'] > df['rsi_low'].shift(1)
    
    signals = df[
        (df['price_lower_low']) & 
        (df['rsi_higher_low']) &
        (df['rsi'] < 50)
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_volatility_expansion(df, hold_days=5):
    """ATR compression followed by expansion"""
    df = df.copy()
    df['atr_low'] = df['atr'].rolling(20).min()
    df['atr_compression'] = df['atr'] <= df['atr_low'] * 1.05
    df['breakout'] = df['high'] > df['high'].shift(1)
    df['above_sma50'] = df['close'] > df['sma_50']
    
    signals = df[
        (df['atr_compression'].shift(1)) & 
        (df['breakout']) &
        (df['above_sma50'])
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_momentum_breakout(df, momentum_thresh=0.05, volume_thresh=1.0, hold_days=5):
    """Momentum breakout with volume confirmation"""
    df = df.copy()
    df['return_20d'] = (df['close'] - df['close'].shift(20)) / df['close'].shift(20)
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    signals = df[
        (df['return_20d'] > momentum_thresh) & 
        (df['volume_ratio'] > volume_thresh)
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_bb_rsi_combo(df, bb_width_thresh=0.05, rsi_thresh=40, hold_days=5):
    """BB Squeeze + RSI combo"""
    df = df.copy()
    
    signals = df[
        (df['bb_width'] < bb_width_thresh) & 
        (df['rsi'] < rsi_thresh)
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_trend_following(df, adx_thresh=25, hold_days=10):
    """Trend following with ADX confirmation"""
    df = df.copy()
    signals = df[
        (df['adx'] > adx_thresh) & 
        (df['close'] > df['sma_50'])
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_adx_momentum(df, adx_thresh=30, rsi_range=(40, 70), hold_days=5):
    """Strong trend + moderate RSI (not overbought/oversold)"""
    df = df.copy()
    signals = df[
        (df['adx'] > adx_thresh) & 
        (df['rsi'] > rsi_range[0]) &
        (df['rsi'] < rsi_range[1]) &
        (df['close'] > df['sma_20'])
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def test_stoch_rsi_combo(df, stoch_thresh=20, rsi_thresh=35, hold_days=5):
    """Stochastic + RSI double oversold"""
    df = df.copy()
    signals = df[
        (df['stoch_k'] < stoch_thresh) & 
        (df['rsi'] < rsi_thresh)
    ].copy()
    
    returns = []
    signal_indices = signals.index.tolist()
    for idx in signal_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days < len(df):
            entry = df.iloc[pos]['close']
            exit_price = df.iloc[pos + hold_days]['close']
            ret = (exit_price - entry) / entry * 100
            returns.append(ret)
    
    return calculate_win_rate(returns)

def main():
    print("=" * 80)
    print("CONTINUOUS STRATEGY RESEARCH BATCH")
    print("Timestamp: 2026-02-23 22:55 UTC")
    print("=" * 80)
    
    data = load_data()
    
    results = []
    
    # Hypothesis 1: RSI + MACD Combo (enhanced mean reversion)
    print("\n" + "=" * 80)
    print("H1: RSI + MACD Combo (RSI<35 + MACD Improving)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_rsi_macd_combo(train)
            test_wr, test_n, test_ret, ci = test_rsi_macd_combo(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H1_RSI_MACD_Combo',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 2: Support Bounce (50-day SMA)
    print("\n" + "=" * 80)
    print("H2: Support Bounce (50-day SMA + RSI<45 + Uptrend)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_support_bounce(train)
            test_wr, test_n, test_ret, ci = test_support_bounce(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H2_Support_Bounce',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 3: Gap Fill
    print("\n" + "=" * 80)
    print("H3: Gap Fill (2%+ Gap Down)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_gap_fill(train)
            test_wr, test_n, test_ret, ci = test_gap_fill(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H3_Gap_Fill',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 4: RSI Divergence Enhanced
    print("\n" + "=" * 80)
    print("H4: RSI Bullish Divergence")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_rsi_divergence(train)
            test_wr, test_n, test_ret, ci = test_rsi_divergence(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H4_RSI_Divergence',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 5: Volatility Expansion (ATR)
    print("\n" + "=" * 80)
    print("H5: Volatility Expansion (ATR Compression + Breakout)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_volatility_expansion(train)
            test_wr, test_n, test_ret, ci = test_volatility_expansion(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H5_Volatility_Expansion',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 6: Stoch + RSI Double Oversold
    print("\n" + "=" * 80)
    print("H6: Stoch + RSI Double Oversold (Stoch<20 + RSI<35)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_stoch_rsi_combo(train)
            test_wr, test_n, test_ret, ci = test_stoch_rsi_combo(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H6_Stoch_RSI_Combo',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 7: ADX Momentum (Strong trend + moderate RSI)
    print("\n" + "=" * 80)
    print("H7: ADX Momentum (ADX>30 + RSI 40-70 + Above SMA20)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_adx_momentum(train)
            test_wr, test_n, test_ret, ci = test_adx_momentum(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H7_ADX_Momentum',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Hypothesis 8: BB + RSI Combo (enhanced version)
    print("\n" + "=" * 80)
    print("H8: BB Squeeze + RSI Enhanced (Width<5% + RSI<40)")
    print("=" * 80)
    for ticker, df in data.items():
        train, test = walk_forward_split(df)
        if len(train) > 50 and len(test) > 50:
            train_wr, train_n, train_ret, _ = test_bb_rsi_combo(train)
            test_wr, test_n, test_ret, ci = test_bb_rsi_combo(test)
            decay = test_wr - train_wr
            
            results.append({
                'hypothesis': 'H8_BB_RSI_Enhanced',
                'ticker': ticker,
                'train_wr': round(train_wr, 1),
                'train_n': train_n,
                'test_wr': round(test_wr, 1),
                'test_n': test_n,
                'decay': round(decay, 1),
                'avg_ret': round(test_ret, 2),
                'ci_lower': round(ci[0], 1),
                'ci_upper': round(ci[1], 1)
            })
            
            status = "GOLDEN" if test_wr >= 70 and test_n >= 30 else "VALIDATED" if test_wr >= 55 else "REJECTED"
            print(f"{ticker}: Train={train_wr:.1f}% (n={train_n}) | Test={test_wr:.1f}% (n={test_n}) | Decay={decay:+.1f}% | {status}")
    
    # Save results
    import os
    os.makedirs('results', exist_ok=True)
    with open('results/continuous_batch_2026-02-23_2255.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    df_results = pd.DataFrame(results)
    golden = df_results[(df_results['test_wr'] >= 70) & (df_results['test_n'] >= 30)]
    validated = df_results[(df_results['test_wr'] >= 55) & (df_results['test_wr'] < 70) & (df_results['test_n'] >= 10)]
    rejected = df_results[(df_results['test_wr'] < 55) | (df_results['test_n'] < 10)]
    
    print(f"\n🏆 GOLDEN (≥70%, n≥30): {len(golden)}")
    print(f"⭐ VALIDATED (55-70%, n≥10): {len(validated)}")
    print(f"❌ REJECTED (<55% or n<10): {len(rejected)}")
    
    if len(golden) > 0:
        print("\n🏆 NEW GOLDEN STRATEGIES:")
        for _, row in golden.iterrows():
            print(f"  - {row['ticker']} {row['hypothesis']}: {row['test_wr']:.1f}% (n={row['test_n']}, decay={row['decay']:+.1f}%)")
    
    # Best validated
    if len(validated) > 0:
        print("\n⭐ TOP VALIDATED STRATEGIES:")
        top_validated = validated.nlargest(5, 'test_wr')
        for _, row in top_validated.iterrows():
            print(f"  - {row['ticker']} {row['hypothesis']}: {row['test_wr']:.1f}% (n={row['test_n']}, decay={row['decay']:+.1f}%)")
    
    # Best by hypothesis
    print("\n📊 BEST RESULT BY HYPOTHESIS:")
    for hyp in df_results['hypothesis'].unique():
        hyp_df = df_results[df_results['hypothesis'] == hyp]
        best = hyp_df.loc[hyp_df['test_wr'].idxmax()]
        print(f"  {hyp}: {best['ticker']} {best['test_wr']:.1f}% (n={best['test_n']})")
    
    print("\n" + "=" * 80)
    print("Results saved to: results/continuous_batch_2026-02-23_2255.json")
    print("=" * 80)
    
    return results

if __name__ == '__main__':
    main()
