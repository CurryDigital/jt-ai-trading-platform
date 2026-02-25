#!/usr/bin/env python3
"""
Continuous Strategy Research — Hypothesis Testing Engine
Tests 3 NEW hypotheses redesigned for bull market conditions (2023-2024)

Key Insight: 2023-2024 was strong bull market:
- Price > SMA50: 92% of days
- RSI > 70: 40% of days (overbought common)
- RSI < 30: 2.3% of days (oversold rare)

Date: 2026-02-24
Hypotheses: 
- H1: Pullback in Uptrend (RSI 40-60)
- H2: MACD Momentum Continuation  
- H3: RSI 50-60 Pullback Entry
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
TEST_START = '2023-01-01'
TEST_END = '2024-12-31'

TICKERS = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'META', 'AMD', 'AAPL', 'MSFT', 'COIN', 'MSTR']

def load_csv_data(ticker):
    """Load data from local CSV files."""
    filepath = f'data/{ticker}_indicators.csv'
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"   ⚠️ Could not load {ticker}: {e}")
        return None

def test_h1_pullback_uptrend(df, ticker):
    """
    H1: Pullback in Strong Uptrend
    - RSI 40-60 (healthy pullback zone)
    - Price > SMA50 (uptrend confirmation)
    - ADX > 20 (trending market)
    - Volume > 20-day average (participation)
    Hold 5 days
    """
    signals = []
    
    df['volume_avg20'] = df['volume'].rolling(20).mean()
    
    for i in range(50, len(df) - 5):
        date = df.index[i]
        
        # Skip if not in test period
        date_str = date.strftime('%Y-%m-%d')
        if date_str < TEST_START or date_str > TEST_END:
            continue
        
        # Entry conditions
        rsi_ok = 40 <= df['rsi'].iloc[i] <= 60
        trend_ok = df['close'].iloc[i] > df['sma_50'].iloc[i]
        adx_ok = df['adx'].iloc[i] > 20
        volume_ok = df['volume'].iloc[i] > df['volume_avg20'].iloc[i]
        
        if rsi_ok and trend_ok and adx_ok and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + 5]
            
            return_pct = (exit_price - entry_price) / entry_price * 100
            win = 1 if return_pct > 0 else 0
            
            signals.append({
                'date': date,
                'ticker': ticker,
                'hypothesis': 'H1_Pullback_Uptrend',
                'entry': entry_price,
                'exit': exit_price,
                'return_pct': return_pct,
                'win': win,
                'hold_days': 5
            })
    
    return pd.DataFrame(signals)

def test_h2_macd_momentum(df, ticker):
    """
    H2: MACD Momentum Continuation
    - MACD > 0 (bullish momentum)
    - MACD Histogram > 0 (accelerating)
    - Price > SMA20 (short-term uptrend)
    - RSI < 65 (not overbought)
    Hold 5 days
    """
    signals = []
    
    for i in range(50, len(df) - 5):
        date = df.index[i]
        
        # Skip if not in test period
        date_str = date.strftime('%Y-%m-%d')
        if date_str < TEST_START or date_str > TEST_END:
            continue
        
        # Entry conditions
        macd_ok = df['macd'].iloc[i] > 0
        hist_ok = df['macd_hist'].iloc[i] > 0
        trend_ok = df['close'].iloc[i] > df['sma_20'].iloc[i]
        rsi_ok = df['rsi'].iloc[i] < 65
        
        if macd_ok and hist_ok and trend_ok and rsi_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + 5]
            
            return_pct = (exit_price - entry_price) / entry_price * 100
            win = 1 if return_pct > 0 else 0
            
            signals.append({
                'date': date,
                'ticker': ticker,
                'hypothesis': 'H2_MACD_Momentum',
                'entry': entry_price,
                'exit': exit_price,
                'return_pct': return_pct,
                'win': win,
                'hold_days': 5
            })
    
    return pd.DataFrame(signals)

def test_h3_rsi_pullback_entry(df, ticker):
    """
    H3: RSI 50-60 Pullback Entry
    - RSI between 50-60 (minor pullback in uptrend)
    - Price > SMA200 (long-term uptrend)
    - Previous day RSI > 60 (was stronger, now pulling back)
    - Volume > average
    Hold 3 days (shorter hold for quick bounce)
    """
    signals = []
    
    df['volume_avg20'] = df['volume'].rolling(20).mean()
    df['rsi_prev'] = df['rsi'].shift(1)
    
    for i in range(50, len(df) - 3):
        date = df.index[i]
        
        # Skip if not in test period
        date_str = date.strftime('%Y-%m-%d')
        if date_str < TEST_START or date_str > TEST_END:
            continue
        
        # Entry conditions
        rsi_ok = 50 <= df['rsi'].iloc[i] <= 60
        rsi_falling = df['rsi_prev'].iloc[i] > 60  # Was higher, now pulling back
        trend_ok = df['close'].iloc[i] > df['sma_200'].iloc[i]
        volume_ok = df['volume'].iloc[i] > df['volume_avg20'].iloc[i]
        
        if rsi_ok and rsi_falling and trend_ok and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + 3]
            
            return_pct = (exit_price - entry_price) / entry_price * 100
            win = 1 if return_pct > 0 else 0
            
            signals.append({
                'date': date,
                'ticker': ticker,
                'hypothesis': 'H3_RSI_Pullback',
                'entry': entry_price,
                'exit': exit_price,
                'return_pct': return_pct,
                'win': win,
                'hold_days': 3
            })
    
    return pd.DataFrame(signals)

def calculate_metrics(signals_df):
    """Calculate metrics for test period (2023-2024)."""
    if len(signals_df) == 0:
        return None
    
    wins = signals_df['win'].sum()
    n = len(signals_df)
    win_rate = wins / n * 100
    avg_return = signals_df['return_pct'].mean()
    total_return = signals_df['return_pct'].sum()
    
    # 95% confidence interval
    p = win_rate / 100
    margin = 1.96 * np.sqrt(p * (1 - p) / n) if n > 0 and p > 0 and p < 1 else 0
    ci_lower = max(0, (p - margin) * 100)
    ci_upper = min(100, (p + margin) * 100)
    
    return {
        'ticker': signals_df['ticker'].iloc[0],
        'hypothesis': signals_df['hypothesis'].iloc[0],
        'test_win_rate': round(win_rate, 1),
        'test_n': n,
        'ci_lower': round(ci_lower, 1),
        'ci_upper': round(ci_upper, 1),
        'avg_return': round(avg_return, 2),
        'total_return': round(total_return, 2),
        'wins': int(wins),
        'losses': int(n - wins)
    }

def classify_strategy(metrics):
    """Classify strategy based on performance."""
    if metrics is None or metrics['test_n'] < 10:
        return 'INSUFFICIENT'
    
    test_wr = metrics['test_win_rate']
    n = metrics['test_n']
    
    if test_wr >= 70 and n >= 30:
        return 'GOLDEN'
    elif test_wr >= 55 and n >= 10:
        return 'VALIDATED'
    elif test_wr >= 50 and n >= 10:
        return 'MARGINAL'
    else:
        return 'REJECTED'

def main():
    """Run all hypothesis tests."""
    print("=" * 80)
    print("CONTINUOUS STRATEGY RESEARCH — 2026-02-24 12:00 UTC")
    print("Testing 3 New Hypotheses (Bull Market Optimized)")
    print("=" * 80)
    
    all_results = []
    
    for ticker in TICKERS:
        print(f"\n📊 Testing {ticker}...")
        
        df = load_csv_data(ticker)
        if df is None or len(df) < 252:
            print(f"   ⚠️ Insufficient data")
            continue
        
        # Test each hypothesis
        for test_func, name in [
            (test_h1_pullback_uptrend, 'H1_Pullback'),
            (test_h2_macd_momentum, 'H2_MACD'),
            (test_h3_rsi_pullback_entry, 'H3_RSI_Pullback')
        ]:
            try:
                signals = test_func(df, ticker)
                if len(signals) > 0:
                    metrics = calculate_metrics(signals)
                    if metrics:
                        metrics['status'] = classify_strategy(metrics)
                        metrics['signals_df'] = signals  # Keep for analysis
                        all_results.append(metrics)
                        
                        status_icon = {
                            'GOLDEN': '🏆',
                            'VALIDATED': '✅',
                            'MARGINAL': '⚠️',
                            'REJECTED': '❌',
                            'INSUFFICIENT': '⚪'
                        }.get(metrics['status'], '?')
                        
                        print(f"   {status_icon} {name}: {metrics['test_win_rate']:.1f}% WR, n={metrics['test_n']}, AvgRet={metrics['avg_return']:+.2f}%")
                    else:
                        print(f"   ⚪ {name}: No metrics")
                else:
                    print(f"   ⚪ {name}: No signals")
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)[:60]}")
    
    # Summarize results
    print("\n" + "=" * 80)
    print("SUMMARY RESULTS")
    print("=" * 80)
    
    if len(all_results) > 0:
        # Summary by hypothesis
        print("\n📈 By Hypothesis:")
        for hypo in ['H1_Pullback_Uptrend', 'H2_MACD_Momentum', 'H3_RSI_Pullback']:
            hypo_results = [r for r in all_results if r['hypothesis'] == hypo]
            if len(hypo_results) > 0:
                golden = len([r for r in hypo_results if r['status'] == 'GOLDEN'])
                validated = len([r for r in hypo_results if r['status'] == 'VALIDATED'])
                marginal = len([r for r in hypo_results if r['status'] == 'MARGINAL'])
                rejected = len([r for r in hypo_results if r['status'] == 'REJECTED'])
                avg_wr = np.mean([r['test_win_rate'] for r in hypo_results])
                total_signals = sum([r['test_n'] for r in hypo_results])
                print(f"   {hypo}: {golden} Golden, {validated} Validated, {marginal} Marginal, {rejected} Rejected")
                print(f"                    Avg WR: {avg_wr:.1f}% | Total Signals: {total_signals}")
        
        # Golden discoveries
        golden_results = [r for r in all_results if r['status'] == 'GOLDEN']
        print(f"\n🏆 GOLDEN DISCOVERIES: {len(golden_results)}")
        for r in golden_results:
            print(f"   • {r['ticker']} {r['hypothesis']}: {r['test_win_rate']:.1f}% WR (n={r['test_n']}, {r['wins']}W/{r['losses']}L)")
        
        # Validated discoveries
        valid_results = [r for r in all_results if r['status'] == 'VALIDATED']
        print(f"\n✅ VALIDATED: {len(valid_results)}")
        for r in valid_results:
            print(f"   • {r['ticker']} {r['hypothesis']}: {r['test_win_rate']:.1f}% WR (n={r['test_n']}, AvgRet={r['avg_return']:+.2f}%)")
        
        # Rejected
        rejected_results = [r for r in all_results if r['status'] == 'REJECTED']
        print(f"\n❌ REJECTED: {len(rejected_results)}")
        for r in rejected_results:
            print(f"   • {r['ticker']} {r['hypothesis']}: {r['test_win_rate']:.1f}% WR (n={r['test_n']})")
        
        # Save results
        os.makedirs('results', exist_ok=True)
        
        # Save metrics only (without DataFrames)
        metrics_only = [{k: v for k, v in r.items() if k != 'signals_df'} for r in all_results]
        output_file = 'results/continuous_research_2026-02-24_1200.json'
        with open(output_file, 'w') as f:
            json.dump(metrics_only, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Print recommendation
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if len(golden_results) > 0:
            print("\n🏆 Deploy these Golden strategies immediately:")
            for r in golden_results:
                print(f"   • {r['ticker']}: {r['hypothesis']} ({r['test_win_rate']:.1f}% WR)")
        
        if len(valid_results) > 0:
            print("\n✅ Monitor these Validated strategies for promotion:")
            for r in valid_results[:5]:  # Top 5
                print(f"   • {r['ticker']}: {r['hypothesis']} ({r['test_win_rate']:.1f}% WR)")
        
        return all_results
    else:
        print("\n⚠️ No results generated")
        return None

if __name__ == '__main__':
    results = main()
