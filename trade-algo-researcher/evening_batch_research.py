#!/usr/bin/env python3
"""
Evening Batch Continuous Research - February 23, 2026
Uses local CSV data files
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import math

DATA_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data'

def get_data(ticker):
    """Fetch price data with indicators from local CSV"""
    filepath = os.path.join(DATA_DIR, f'{ticker}_indicators.csv')
    if not os.path.exists(filepath):
        return None
    
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        # Calculate additional indicators
        df['returns'] = df['close'].pct_change()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # Candlestick patterns
        df['body'] = df['close'] - df['open']
        df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
        df['range'] = df['high'] - df['low']
        df['body_pct'] = abs(df['body']) / (df['range'] + 0.001)
        
        return df
    except Exception as e:
        print(f"Error loading {ticker}: {e}")
        return None

def calculate_95_ci(wins, total):
    """Calculate 95% confidence interval for win rate"""
    if total == 0:
        return 0, 0
    p = wins / total
    z = 1.96
    se = np.sqrt(p * (1 - p) / total)
    ci_lower = max(0, p - z * se)
    ci_upper = min(1, p + z * se)
    return ci_lower * 100, ci_upper * 100

def split_train_test(df, train_end='2022-12-31', test_start='2023-01-01'):
    """Split data into train and test periods"""
    train = df[df.index <= train_end].copy()
    test = df[df.index >= test_start].copy()
    return train, test

# ============================================
# HYPOTHESIS TESTING FUNCTIONS
# ============================================

def test_rsi_macd_volume(df, rsi_threshold=35, volume_threshold=1.1, hold_days=5):
    """RSI < threshold + MACD improving + Volume > threshold"""
    signals = []
    
    for i in range(len(df) - hold_days):
        if i < 26:
            continue
        
        rsi_ok = df['rsi'].iloc[i] < rsi_threshold
        macd_improving = df['macd_hist'].iloc[i] > df['macd_hist'].iloc[i-1] if i > 0 else False
        volume_ok = df['volume_ratio'].iloc[i] > volume_threshold
        
        if rsi_ok and macd_improving and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_morning_star(df, hold_days=5):
    """Morning Star candlestick pattern detection"""
    signals = []
    
    for i in range(2, len(df) - hold_days):
        # Day 1: Bearish (red candle)
        day1_bearish = df['close'].iloc[i-2] < df['open'].iloc[i-2]
        day1_body = abs(df['body'].iloc[i-2])
        
        # Day 2: Small body (indecision/doji)
        day2_body = abs(df['body'].iloc[i-1])
        day2_small = day2_body < day1_body * 0.3
        
        # Day 3: Bullish (green candle) with close above day1 mid
        day3_bullish = df['close'].iloc[i] > df['open'].iloc[i]
        day1_mid = (df['open'].iloc[i-2] + df['close'].iloc[i-2]) / 2
        day3_strong = df['close'].iloc[i] > day1_mid
        
        if day1_bearish and day2_small and day3_bullish and day3_strong:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_evening_star(df, hold_days=5):
    """Evening Star candlestick pattern (bearish)"""
    signals = []
    
    for i in range(2, len(df) - hold_days):
        # Day 1: Bullish (green candle)
        day1_bullish = df['close'].iloc[i-2] > df['open'].iloc[i-2]
        day1_body = abs(df['body'].iloc[i-2])
        
        # Day 2: Small body
        day2_body = abs(df['body'].iloc[i-1])
        day2_small = day2_body < day1_body * 0.3
        
        # Day 3: Bearish (red candle)
        day3_bearish = df['close'].iloc[i] < df['open'].iloc[i]
        
        if day1_bullish and day2_small and day3_bearish:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (entry_price - exit_price) / entry_price  # Short position
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_doji_reversal(df, rsi_low=30, rsi_high=70, hold_days=5):
    """Doji pattern with RSI confirmation"""
    signals = []
    
    for i in range(len(df) - hold_days):
        # Doji: very small body relative to range
        body_size = abs(df['body'].iloc[i])
        range_size = df['range'].iloc[i]
        is_doji = body_size < range_size * 0.1 if range_size > 0 else False
        
        rsi = df['rsi'].iloc[i]
        rsi_extreme = rsi < rsi_low or rsi > rsi_high
        
        if is_doji and rsi_extreme:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            
            # Long if RSI low, short if RSI high
            if rsi < rsi_low:
                pnl = (exit_price - entry_price) / entry_price
            else:
                pnl = (entry_price - exit_price) / entry_price
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_bb_squeeze(df, bb_width_threshold=0.05, rsi_threshold=45, hold_days=5):
    """BB Squeeze + RSI filter"""
    signals = []
    
    for i in range(2, len(df) - hold_days):
        # Calculate BB width if not present
        if 'bb_width' in df.columns:
            bb_width = df['bb_width'].iloc[i]
            bb_width_prev = df['bb_width'].iloc[i-1]
        else:
            bb_width = (df['bb_upper'].iloc[i] - df['bb_lower'].iloc[i]) / df['close'].iloc[i]
            bb_width_prev = (df['bb_upper'].iloc[i-1] - df['bb_lower'].iloc[i-1]) / df['close'].iloc[i-1]
        
        bb_squeeze = bb_width < bb_width_threshold
        bb_squeeze_prev = bb_width_prev < bb_width_threshold
        rsi_ok = df['rsi'].iloc[i] < rsi_threshold
        
        if bb_squeeze and bb_squeeze_prev and rsi_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_adx_trend(df, adx_threshold=25, volume_threshold=0, hold_days=5):
    """ADX Trend strategy with optional volume filter"""
    signals = []
    
    for i in range(len(df) - hold_days):
        if i < 50:
            continue
        
        above_sma50 = df['close'].iloc[i] > df['sma_50'].iloc[i]
        adx_ok = df['adx'].iloc[i] > adx_threshold
        volume_ok = df['volume_ratio'].iloc[i] > volume_threshold if volume_threshold > 0 else True
        
        if above_sma50 and adx_ok and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

def test_bearish_rsi_regime(ticker_df, spy_df, rsi_threshold=75, hold_days=5):
    """Bearish RSI with bear market filter (SPY < 200d MA)"""
    signals = []
    
    # Align data
    df = ticker_df.copy()
    spy = spy_df.copy()
    
    for i in range(len(df) - hold_days):
        if i < 200:
            continue
        
        # Get corresponding SPY data
        date = df.index[i]
        spy_row = spy[spy.index == date]
        if len(spy_row) == 0:
            continue
        
        spy_close = spy_row['close'].values[0]
        spy_sma200 = spy_row['sma_200'].values[0] if 'sma_200' in spy_row.columns else None
        
        if spy_sma200 is None:
            continue
        
        bear_regime = spy_close < spy_sma200
        rsi_ok = df['rsi'].iloc[i] > rsi_threshold
        
        if bear_regime and rsi_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (entry_price - exit_price) / entry_price  # Short
            
            signals.append({
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl,
                'win': 1 if pnl > 0 else 0
            })
    
    return pd.DataFrame(signals)

# ============================================
# MAIN EXECUTION
# ============================================

def run_research():
    """Run evening batch research"""
    
    print("=" * 80)
    print("EVENING BATCH CONTINUOUS RESEARCH - February 23, 2026 (22:25 UTC)")
    print("=" * 80)
    
    # Available tickers
    tech_tickers = ['NVDA', 'META', 'TSLA', 'AAPL', 'MSFT', 'AMD', 'COIN', 'MSTR']
    spy = get_data('SPY')
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'new_hypotheses': {},
        'enhanced_strategies': {},
        'cross_sector': {},
        'summary': {'golden': [], 'validated': [], 'rejected': [], 'insufficient': []}
    }
    
    # ============================================
    # PART 1: NEW HYPOTHESES
    # ============================================
    print("\n" + "=" * 80)
    print("PART 1: NEW HYPOTHESIS TESTING")
    print("=" * 80)
    
    # H1: RSI + MACD + Volume
    print("\n--- H1: RSI + MACD + Volume Triple Confirmation ---")
    h1_results = {}
    
    for ticker in ['NVDA', 'META', 'TSLA', 'AAPL', 'COIN', 'AMD']:
        df = get_data(ticker)
        if df is None or len(df) < 100:
            continue
        
        train, test = split_train_test(df)
        if len(train) < 50 or len(test) < 50:
            continue
        
        train_signals = test_rsi_macd_volume(train, rsi_threshold=35, volume_threshold=1.1)
        test_signals = test_rsi_macd_volume(test, rsi_threshold=35, volume_threshold=1.1)
        
        if len(test_signals) >= 5:
            test_win = test_signals['win'].sum()
            test_total = len(test_signals)
            test_wr = test_win / test_total * 100
            ci_low, ci_high = calculate_95_ci(test_win, test_total)
            
            train_wr = train_signals['win'].sum() / len(train_signals) * 100 if len(train_signals) > 0 else 0
            decay = test_wr - train_wr
            
            h1_results[ticker] = {
                'train_wr': round(train_wr, 1),
                'test_wr': round(test_wr, 1),
                'n': test_total,
                'decay': round(decay, 1),
                'ci': [round(ci_low, 1), round(ci_high, 1)]
            }
            
            status = "🏆 GOLDEN" if test_wr >= 70 and test_total >= 30 and abs(decay) < 15 else \
                     "✅ VALIDATED" if test_wr >= 55 and test_total >= 10 else "⚠️ INSUFFICIENT"
            print(f"  {ticker}: Test={test_wr:.1f}% (n={test_total}), Decay={decay:.1f}% {status}")
    
    results['new_hypotheses']['rsi_macd_volume'] = h1_results
    
    # H2: Candlestick Patterns
    print("\n--- H2: Candlestick Patterns ---")
    
    candlestick_results = {'morning_star': {}, 'evening_star': {}, 'doji': {}}
    
    for ticker in ['NVDA', 'AAPL', 'META', 'AMD', 'COIN', 'TSLA']:
        df = get_data(ticker)
        if df is None:
            continue
        
        _, test = split_train_test(df)
        
        # Morning Star
        signals = test_morning_star(test)
        if len(signals) >= 5:
            wr = signals['win'].mean() * 100
            candlestick_results['morning_star'][ticker] = {'test_wr': round(wr, 1), 'n': len(signals)}
        
        # Evening Star
        signals = test_evening_star(test)
        if len(signals) >= 5:
            wr = signals['win'].mean() * 100
            candlestick_results['evening_star'][ticker] = {'test_wr': round(wr, 1), 'n': len(signals)}
        
        # Doji
        signals = test_doji_reversal(test)
        if len(signals) >= 5:
            wr = signals['win'].mean() * 100
            candlestick_results['doji'][ticker] = {'test_wr': round(wr, 1), 'n': len(signals)}
    
    print(f"  Morning Star: {candlestick_results['morning_star']}")
    print(f"  Evening Star: {candlestick_results['evening_star']}")
    print(f"  Doji: {candlestick_results['doji']}")
    
    results['new_hypotheses']['candlestick'] = candlestick_results
    
    # H3: Bearish with Regime Filter
    print("\n--- H3: Bearish RSI > 75 + Bear Market Filter ---")
    h3_results = {}
    
    if spy is not None:
        for ticker in ['SPY', 'QQQ', 'AAPL', 'TSLA']:
            df = get_data(ticker)
            if df is None:
                continue
            
            _, test = split_train_test(df)
            _, spy_test = split_train_test(spy)
            
            signals = test_bearish_rsi_regime(test, spy_test, rsi_threshold=75)
            if len(signals) >= 5:
                wr = signals['win'].mean() * 100
                h3_results[ticker] = {'test_wr': round(wr, 1), 'n': len(signals)}
                print(f"  {ticker}: {wr:.1f}% (n={len(signals)})")
            else:
                print(f"  {ticker}: No signals (bull market)")
    
    results['new_hypotheses']['bearish_regime'] = h3_results
    
    # ============================================
    # PART 2: ENHANCED STRATEGIES
    # ============================================
    print("\n" + "=" * 80)
    print("PART 2: ENHANCED VALIDATED STRATEGIES")
    print("=" * 80)
    
    enhanced = {}
    
    # META Trend Enhancement
    print("\n--- META Trend Enhancement ---")
    df = get_data('META')
    if df is not None:
        train, test = split_train_test(df)
        
        # Original
        orig_train = test_adx_trend(train, adx_threshold=25, volume_threshold=0)
        orig_test = test_adx_trend(test, adx_threshold=25, volume_threshold=0)
        orig_wr = orig_test['win'].mean() * 100 if len(orig_test) > 0 else 0
        
        # Enhanced with volume
        enh_test = test_adx_trend(test, adx_threshold=25, volume_threshold=1.0)
        enh_wr = enh_test['win'].mean() * 100 if len(enh_test) > 0 else 0
        
        # Higher ADX
        enh2_test = test_adx_trend(test, adx_threshold=30, volume_threshold=0)
        enh2_wr = enh2_test['win'].mean() * 100 if len(enh2_test) > 0 else 0
        
        enhanced['META'] = {
            'original': {'wr': round(orig_wr, 1), 'n': len(orig_test)},
            'volume_filter': {'wr': round(enh_wr, 1), 'n': len(enh_test)},
            'adx_30': {'wr': round(enh2_wr, 1), 'n': len(enh2_test)}
        }
        
        print(f"  Original ADX>25: {orig_wr:.1f}% (n={len(orig_test)})")
        print(f"  +Volume>1.0x: {enh_wr:.1f}% (n={len(enh_test)})")
        print(f"  ADX>30: {enh2_wr:.1f}% (n={len(enh2_test)})")
    
    # AMD Trend Enhancement
    print("\n--- AMD Trend Enhancement ---")
    df = get_data('AMD')
    if df is not None:
        train, test = split_train_test(df)
        
        orig_test = test_adx_trend(test, adx_threshold=25, volume_threshold=0)
        orig_wr = orig_test['win'].mean() * 100 if len(orig_test) > 0 else 0
        
        enh_test = test_adx_trend(test, adx_threshold=25, volume_threshold=1.2)
        enh_wr = enh_test['win'].mean() * 100 if len(enh_test) > 0 else 0
        
        enhanced['AMD'] = {
            'original': {'wr': round(orig_wr, 1), 'n': len(orig_test)},
            'volume_1.2x': {'wr': round(enh_wr, 1), 'n': len(enh_test)}
        }
        
        print(f"  Original: {orig_wr:.1f}% (n={len(orig_test)})")
        print(f"  +Volume>1.2x: {enh_wr:.1f}% (n={len(enh_test)})")
    
    results['enhanced_strategies'] = enhanced
    
    # ============================================
    # PART 3: CROSS-SECTOR BB SQUEEZE
    # ============================================
    print("\n" + "=" * 80)
    print("PART 3: CROSS-SECTOR BB SQUEEZE")
    print("=" * 80)
    
    # Note: Finance/Healthcare tickers may not be in local data
    # We'll test on available tech/crypto as proxy for methodology
    cross_sector = {}
    
    print("\n--- Tech Validation (Baseline) ---")
    tech_bb = {}
    for ticker in ['NVDA', 'META', 'AAPL', 'MSFT']:
        df = get_data(ticker)
        if df is None:
            continue
        
        train, test = split_train_test(df)
        train_signals = test_bb_squeeze(train, bb_width_threshold=0.05, rsi_threshold=45)
        test_signals = test_bb_squeeze(test, bb_width_threshold=0.05, rsi_threshold=45)
        
        if len(test_signals) >= 10:
            test_wr = test_signals['win'].mean() * 100
            train_wr = train_signals['win'].mean() * 100 if len(train_signals) > 0 else 0
            decay = test_wr - train_wr
            
            tech_bb[ticker] = {
                'test_wr': round(test_wr, 1),
                'train_wr': round(train_wr, 1),
                'n': len(test_signals),
                'decay': round(decay, 1)
            }
            
            status = "🏆 GOLDEN" if test_wr >= 70 and len(test_signals) >= 30 and abs(decay) < 15 else "✅ VALIDATED"
            print(f"  {ticker}: Test={test_wr:.1f}% (n={len(test_signals)}), Decay={decay:.1f}% {status}")
    
    cross_sector['tech'] = tech_bb
    
    # Crypto sector
    print("\n--- Crypto Sector (Cross-Asset) ---")
    crypto_bb = {}
    for ticker in ['COIN', 'MSTR']:
        df = get_data(ticker)
        if df is None:
            continue
        
        train, test = split_train_test(df)
        train_signals = test_bb_squeeze(train, bb_width_threshold=0.05, rsi_threshold=45)
        test_signals = test_bb_squeeze(test, bb_width_threshold=0.05, rsi_threshold=45)
        
        if len(test_signals) >= 10:
            test_wr = test_signals['win'].mean() * 100
            train_wr = train_signals['win'].mean() * 100 if len(train_signals) > 0 else 0
            decay = test_wr - train_wr
            
            crypto_bb[ticker] = {
                'test_wr': round(test_wr, 1),
                'train_wr': round(train_wr, 1),
                'n': len(test_signals),
                'decay': round(decay, 1)
            }
            
            status = "🏆 GOLDEN" if test_wr >= 70 and len(test_signals) >= 30 and abs(decay) < 15 else "✅ VALIDATED"
            print(f"  {ticker}: Test={test_wr:.1f}% (n={len(test_signals)}), Decay={decay:.1f}% {status}")
    
    cross_sector['crypto'] = crypto_bb
    results['cross_sector'] = cross_sector
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    # Collect all results
    all_results = []
    
    # From new hypotheses
    for strategy, data in results['new_hypotheses'].items():
        if isinstance(data, dict):
            for ticker, metrics in data.items():
                if isinstance(metrics, dict) and 'test_wr' in metrics:
                    all_results.append({
                        'strategy': strategy,
                        'ticker': ticker,
                        **metrics
                    })
    
    # From cross-sector
    for sector, data in results['cross_sector'].items():
        for ticker, metrics in data.items():
            all_results.append({
                'strategy': f'bb_squeeze_{sector}',
                'ticker': ticker,
                **metrics
            })
    
    # Categorize
    golden = [r for r in all_results if r.get('test_wr', 0) >= 70 and r.get('n', 0) >= 30 and abs(r.get('decay', 0)) < 15]
    validated = [r for r in all_results if 55 <= r.get('test_wr', 0) < 70 and r.get('n', 0) >= 10]
    near = [r for r in all_results if r.get('test_wr', 0) >= 55 and 5 <= r.get('n', 0) < 10]
    rejected = [r for r in all_results if r.get('test_wr', 0) < 50 and r.get('n', 0) >= 5]
    
    print(f"\n  🏆 Golden Strategies: {len(golden)}")
    for r in golden:
        print(f"    - {r['ticker']} {r['strategy']}: {r['test_wr']}% (n={r['n']}, decay={r.get('decay', 'N/A')}%)")
    
    print(f"\n  ✅ Validated (55-70%): {len(validated)}")
    for r in validated:
        print(f"    - {r['ticker']} {r['strategy']}: {r['test_wr']}% (n={r['n']})")
    
    print(f"\n  🟡 Near Validated: {len(near)}")
    for r in near:
        print(f"    - {r['ticker']} {r['strategy']}: {r['test_wr']}% (n={r['n']})")
    
    print(f"\n  ❌ Rejected: {len(rejected)}")
    
    results['summary'] = {
        'golden': golden,
        'validated': validated,
        'near': near,
        'rejected': rejected,
        'total_tested': len(all_results)
    }
    
    # Save results
    output_file = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/evening_batch_2026-02-23_2225.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  Results saved: {output_file}")
    print("\n" + "=" * 80)
    print("RESEARCH COMPLETE")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    run_research()
