#!/usr/bin/env python3
"""
Continuous Strategy Research Batch - Feb 23 (20:25 UTC)
New Hypotheses Testing with Walk-Forward Validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

DATA_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data'
RESULTS_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results'

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

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
        # Filter for train/test split
        df['year'] = df.index.year
        return df
    except Exception as e:
        print(f"Error loading {ticker}: {e}")
        return None

def calculate_95_ci(wins, total):
    """Calculate 95% confidence interval for win rate"""
    if total == 0:
        return 0, 0
    p = wins / total
    z = 1.96  # 95% confidence
    se = np.sqrt(p * (1 - p) / total)
    ci_lower = max(0, p - z * se)
    ci_upper = min(1, p + z * se)
    return ci_lower * 100, ci_upper * 100

def calculate_decay(train_wr, test_wr):
    """Calculate decay between train and test"""
    if train_wr == 0:
        return 0
    return ((test_wr - train_wr) / train_wr) * 100

def backtest_rsi_macd_combo(df, hold_days=5, rsi_threshold=35, volume_mult=1.0):
    """
    H1: RSI + MACD Combo
    RSI < threshold AND MACD Histogram improving (bullish momentum building)
    """
    df = df.copy()
    
    # MACD improving = current hist > previous hist
    df['macd_improving'] = df['macd_hist'] > df['macd_hist'].shift(1)
    df['volume_above_avg'] = df['volume'] > df['volume'].rolling(20).mean() * volume_mult
    
    # Signal: RSI oversold + MACD improving + Volume confirmation
    df['signal'] = (df['rsi'] < rsi_threshold) & df['macd_improving'] & df['volume_above_avg']
    
    signals = []
    for i in range(1, len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def backtest_bb_rsi_confluence(df, hold_days=5):
    """
    H2: BB + RSI Confluence
    Price touches BB lower AND RSI < 40 (strong oversold)
    """
    df = df.copy()
    
    # Price near or below BB lower
    df['near_bb_lower'] = df['close'] <= df['bb_lower'] * 1.01  # Within 1% of lower band
    df['rsi_oversold'] = df['rsi'] < 40
    
    df['signal'] = df['near_bb_lower'] & df['rsi_oversold']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def backtest_adx_trend_continuation(df, hold_days=10, adx_threshold=25):
    """
    H3: ADX Trend Continuation
    Strong trend (ADX > threshold) + Price above SMA20 = trend continuation
    """
    df = df.copy()
    
    df['strong_trend'] = df['adx'] > adx_threshold
    df['above_sma20'] = df['close'] > df['sma_20']
    df['signal'] = df['strong_trend'] & df['above_sma20']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def backtest_volatility_expansion(df, hold_days=5):
    """
    H4: Volatility Expansion After Compression
    BB Width < 5% (compression) followed by expansion
    """
    df = df.copy()
    
    # BB Width compression
    df['bb_compressed'] = df['bb_width'] < 0.05
    df['compression_lag'] = df['bb_compressed'].shift(1)  # Was compressed yesterday
    df['signal'] = df['compression_lag'] & (~df['bb_compressed'])  # Now expanding
    
    signals = []
    for i in range(1, len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def backtest_atr_breakout(df, hold_days=5, atr_mult=1.5):
    """
    H5: ATR Breakout
    Price breaks above yesterday's close + ATR * multiplier
    """
    df = df.copy()
    
    df['breakout_level'] = df['close'].shift(1) + df['atr'] * atr_mult
    df['signal'] = df['close'] > df['breakout_level']
    
    signals = []
    for i in range(1, len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def backtest_double_oversold(df, hold_days=5):
    """
    H6: Double Oversold
    RSI < 30 AND Stoch < 20 (extreme oversold on both indicators)
    """
    df = df.copy()
    df['signal'] = (df['rsi'] < 30) & (df['stoch_k'] < 20)
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            pnl = (exit_price - entry_price) / entry_price
            win = 1 if pnl > 0 else 0
            
            signals.append({
                'entry_date': entry_date,
                'exit_date': df.index[exit_idx],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'win': win
            })
    
    return pd.DataFrame(signals)

def run_walk_forward_test(ticker, strategy_func, strategy_name, hold_days=5):
    """Run walk-forward test: Train 2021-2022, Test 2023-2024"""
    df = get_data(ticker)
    if df is None or len(df) < 100:
        return None
    
    # Split data
    train_data = df[(df['year'] >= 2021) & (df['year'] <= 2022)]
    test_data = df[(df['year'] >= 2023) & (df['year'] <= 2024)]
    
    if len(train_data) < 50 or len(test_data) < 50:
        return None
    
    # Run backtest on both periods
    train_results = strategy_func(train_data, hold_days)
    test_results = strategy_func(test_data, hold_days)
    
    if len(train_results) == 0 or len(test_results) == 0:
        return None
    
    train_wins = train_results['win'].sum()
    train_total = len(train_results)
    train_wr = (train_wins / train_total) * 100
    
    test_wins = test_results['win'].sum()
    test_total = len(test_results)
    test_wr = (test_wins / test_total) * 100
    
    decay = calculate_decay(train_wr, test_wr)
    ci_lower, ci_upper = calculate_95_ci(test_wins, test_total)
    avg_return = test_results['pnl'].mean() * 100
    
    return {
        'ticker': ticker,
        'strategy': strategy_name,
        'hold_days': hold_days,
        'train_wr': round(train_wr, 1),
        'train_n': train_total,
        'test_wr': round(test_wr, 1),
        'test_n': test_total,
        'decay': round(decay, 1),
        'ci_lower': round(ci_lower, 1),
        'ci_upper': round(ci_upper, 1),
        'avg_return': round(avg_return, 2),
        'status': classify_status(test_wr, test_total, decay)
    }

def classify_status(test_wr, n, decay):
    """Classify strategy status"""
    if test_wr >= 70 and n >= 30 and decay < 15:
        return "🏆 GOLDEN"
    elif test_wr >= 60 and n >= 20:
        return "⭐ Near-Golden"
    elif test_wr >= 55 and n >= 15:
        return "✅ Validated"
    elif test_wr >= 55 and n < 15:
        return "⚠️ Insufficient"
    else:
        return "❌ Rejected"

def main():
    print("="*80)
    print("CONTINUOUS STRATEGY RESEARCH BATCH")
    print("Timestamp:", datetime.now().strftime('%Y-%m-%d %H:%M UTC'))
    print("="*80)
    
    # Available tickers
    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'GOOGL', 'AMZN', 'QQQ', 'SPY', 'MSTR', 'COIN']
    
    # Test all hypotheses
    all_results = []
    
    hypotheses = [
        ('H1: RSI+MACD+Volume', backtest_rsi_macd_combo, 5),
        ('H2: BB+RSI Confluence', backtest_bb_rsi_confluence, 5),
        ('H3: ADX Trend Continuation', backtest_adx_trend_continuation, 10),
        ('H4: Volatility Expansion', backtest_volatility_expansion, 5),
        ('H5: ATR Breakout', backtest_atr_breakout, 5),
        ('H6: Double Oversold (RSI+Stoch)', backtest_double_oversold, 5),
    ]
    
    for hyp_name, hyp_func, hold_days in hypotheses:
        print(f"\n{'='*60}")
        print(f"Testing: {hyp_name} (Hold: {hold_days} days)")
        print('='*60)
        
        for ticker in tickers:
            result = run_walk_forward_test(ticker, hyp_func, hyp_name, hold_days)
            if result:
                all_results.append(result)
                status_icon = "✓" if result['status'] not in ["❌ Rejected", "⚠️ Insufficient"] else "✗"
                print(f"{status_icon} {ticker}: Test={result['test_wr']}% (n={result['test_n']}), Decay={result['decay']:+.1f}% | {result['status']}")
    
    # Save results
    output_file = os.path.join(RESULTS_DIR, f'continuous_batch_{datetime.now().strftime("%Y-%m-%d_%H%M")}.json')
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    golden = [r for r in all_results if "GOLDEN" in r['status']]
    near_golden = [r for r in all_results if "Near-Golden" in r['status']]
    validated = [r for r in all_results if "Validated" in r['status']]
    rejected = [r for r in all_results if "Rejected" in r['status']]
    insufficient = [r for r in all_results if "Insufficient" in r['status']]
    
    print(f"🏆 Golden: {len(golden)}")
    print(f"⭐ Near-Golden: {len(near_golden)}")
    print(f"✅ Validated: {len(validated)}")
    print(f"⚠️ Insufficient: {len(insufficient)}")
    print(f"❌ Rejected: {len(rejected)}")
    print(f"\nTotal Tests: {len(all_results)}")
    print(f"Results saved to: {output_file}")
    
    # Print golden strategies
    if golden:
        print(f"\n{'='*80}")
        print("🏆 GOLDEN STRATEGIES DISCOVERED")
        print('='*80)
        for r in golden:
            print(f"\n{r['ticker']} - {r['strategy']}")
            print(f"  Test Win Rate: {r['test_wr']}% (n={r['test_n']})")
            print(f"  Decay: {r['decay']:+.1f}%")
            print(f"  95% CI: [{r['ci_lower']}% - {r['ci_upper']}%]")
            print(f"  Avg Return: {r['avg_return']:+.2f}%")
    
    return all_results

if __name__ == '__main__':
    results = main()
