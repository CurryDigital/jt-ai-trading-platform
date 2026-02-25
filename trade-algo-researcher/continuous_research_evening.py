#!/usr/bin/env python3
"""
Continuous Strategy Research Batch - Feb 23 Evening
Tests new hypotheses using local CSV data files
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

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

def backtest_bearish_rsi_bear_market(ticker_df, spy_df, hold_days=5):
    """
    H1: Bearish RSI >70 Short Strategy with Bear Market Filter
    Enter short when RSI > 70 AND SPY < 200d MA (bear market)
    """
    df = ticker_df.copy()
    spy = spy_df.copy()
    
    # Merge with SPY data for regime filter
    df = df.join(spy[['close', 'sma_200']], rsuffix='_spy', how='left')
    df['spy_above_200'] = df['close_spy'] > df['sma_200']
    
    # Signal: RSI > 70 AND SPY below 200d (bear market)
    df['signal'] = (df['rsi'] > 70) & (~df['spy_above_200'])
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_date = df.index[i]
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            # Short position: profit if price goes down
            pnl = (entry_price - exit_price) / entry_price
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

def backtest_stoch_trend_combo(df, hold_days=5, price_below_sma_pct=-0.02):
    """
    H2: Stochastic + Trend Combo (from NVDA strategy)
    Stoch < 20 AND Price < SMA50 by at least 2%
    """
    df = df.copy()
    
    # Signal: Stoch %K < 20 AND Price below SMA50 by threshold
    df['price_vs_sma50'] = (df['close'] / df['sma_50']) - 1
    df['signal'] = (df['stoch_k'] < 20) & (df['price_vs_sma50'] < price_below_sma_pct)
    
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

def backtest_rsi_macd_volume_combo(df, hold_days=5):
    """
    H3: Triple Filter - RSI < 30 + MACD improving + Volume > 1.2x avg
    """
    df = df.copy()
    
    # Calculate volume moving average
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    
    # Signal: RSI < 30 AND MACD histogram improving (current > previous) AND Volume > 1.2x avg
    df['macd_improving'] = df['macd_hist'] > df['macd_hist'].shift(1)
    df['volume_spike'] = df['volume'] > (df['volume_sma20'] * 1.2)
    
    df['signal'] = (df['rsi'] < 30) & df['macd_improving'] & df['volume_spike']
    
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

def backtest_bb_squeeze_reversal(df, hold_days=5):
    """
    H4: Bollinger Band Squeeze + RSI < 40
    BB Width < 5% (squeeze) + RSI < 40 (oversold)
    """
    df = df.copy()
    
    # Signal: BB Width < 5% AND RSI < 40
    df['bb_squeeze'] = df['bb_width'] < 0.05
    df['rsi_oversold'] = df['rsi'] < 40
    df['signal'] = df['bb_squeeze'] & df['rsi_oversold']
    
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

def split_train_test(signals_df, split_date='2023-01-01'):
    """Split signals into train (2021-2022) and test (2023-2024)"""
    split_dt = pd.to_datetime(split_date)
    train = signals_df[signals_df['entry_date'] < split_dt]
    test = signals_df[signals_df['entry_date'] >= split_dt]
    return train, test

def analyze_results(train_df, test_df, ticker, strategy_name):
    """Calculate metrics for train/test split"""
    train_wins = train_df['win'].sum() if len(train_df) > 0 else 0
    train_total = len(train_df)
    train_wr = (train_wins / train_total * 100) if train_total > 0 else 0
    
    test_wins = test_df['win'].sum() if len(test_df) > 0 else 0
    test_total = len(test_df)
    test_wr = (test_wins / test_total * 100) if test_total > 0 else 0
    
    decay = train_wr - test_wr
    ci_lower, ci_upper = calculate_95_ci(test_wins, test_total)
    avg_return = test_df['pnl'].mean() * 100 if test_total > 0 else 0
    
    # Golden criteria check
    is_golden = test_wr >= 70 and test_total >= 30 and decay < 15
    is_validated = test_wr >= 55 and test_total >= 10 and decay < 25
    
    return {
        'ticker': ticker,
        'strategy': strategy_name,
        'train_wr': round(train_wr, 1),
        'train_n': int(train_total),
        'test_wr': round(test_wr, 1),
        'test_n': int(test_total),
        'decay': round(decay, 1),
        'ci_lower': round(ci_lower, 1),
        'ci_upper': round(ci_upper, 1),
        'avg_return': round(avg_return, 2),
        'status': '🏆 GOLDEN' if is_golden else ('✅ Validated' if is_validated else '⚠️ Insufficient'),
        'is_golden': is_golden,
        'is_validated': is_validated
    }

def run_research_batch():
    """Run the continuous research batch"""
    results = []
    
    print("=" * 70)
    print("CONTINUOUS STRATEGY RESEARCH BATCH - Feb 23 Evening")
    print("Testing 4 new hypotheses on available data")
    print("=" * 70)
    
    # Get SPY data for regime filters
    print("\n📊 Loading SPY data for regime filters...")
    spy_df = get_data('SPY')
    if spy_df is None:
        print("❌ Cannot load SPY data - aborting")
        return []
    print(f"   SPY data loaded: {len(spy_df)} records")
    
    available_tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'AMZN', 'GOOGL', 'COIN', 'MSTR', 'QQQ', 'IWM']
    
    # H1: Bearish RSI > 70 with Bear Market Filter
    print("\n" + "=" * 70)
    print("H1: BEARISH RSI > 70 SHORT (Bear Market Filter)")
    print("=" * 70)
    print("Short overbought stocks during bear markets (SPY < 200d)")
    
    for ticker in available_tickers:
        df = get_data(ticker)
        if df is None:
            continue
            
        signals = backtest_bearish_rsi_bear_market(df, spy_df)
        if len(signals) == 0:
            print(f"  ⚠️  {ticker}: No signals (no bear market periods in test data)")
            continue
            
        train, test = split_train_test(signals)
        result = analyze_results(train, test, ticker, 'Bearish RSI >70 + Bear Market')
        results.append(result)
        
        status_icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "⚠️")
        print(f"  {status_icon} {ticker}: Test={result['test_wr']}% (n={result['test_n']}), Decay={result['decay']}%")
    
    # H2: Stochastic + Trend Combo
    print("\n" + "=" * 70)
    print("H2: STOCHASTIC + TREND COMBO")
    print("=" * 70)
    print("Stoch < 20 AND Price < SMA50 by 2%")
    
    for ticker in available_tickers:
        df = get_data(ticker)
        if df is None:
            continue
            
        signals = backtest_stoch_trend_combo(df)
        if len(signals) == 0:
            print(f"  ⚠️  {ticker}: No signals generated")
            continue
            
        train, test = split_train_test(signals)
        result = analyze_results(train, test, ticker, 'Stoch <20 + Price < SMA50')
        results.append(result)
        
        status_icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "⚠️")
        print(f"  {status_icon} {ticker}: Test={result['test_wr']}% (n={result['test_n']}), Decay={result['decay']}%")
    
    # H3: RSI + MACD + Volume Combo
    print("\n" + "=" * 70)
    print("H3: RSI + MACD + VOLUME COMBO")
    print("=" * 70)
    print("RSI < 30 + MACD improving + Volume > 1.2x avg")
    
    for ticker in available_tickers:
        df = get_data(ticker)
        if df is None:
            continue
            
        signals = backtest_rsi_macd_volume_combo(df)
        if len(signals) == 0:
            print(f"  ⚠️  {ticker}: No signals generated")
            continue
            
        train, test = split_train_test(signals)
        result = analyze_results(train, test, ticker, 'RSI+MACD+Volume Combo')
        results.append(result)
        
        status_icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "⚠️")
        print(f"  {status_icon} {ticker}: Test={result['test_wr']}% (n={result['test_n']}), Decay={result['decay']}%")
    
    # H4: BB Squeeze + RSI Reversal
    print("\n" + "=" * 70)
    print("H4: BB SQUEEZE + RSI REVERSAL")
    print("=" * 70)
    print("BB Width < 5% + RSI < 40")
    
    for ticker in available_tickers:
        df = get_data(ticker)
        if df is None:
            continue
            
        signals = backtest_bb_squeeze_reversal(df)
        if len(signals) == 0:
            print(f"  ⚠️  {ticker}: No signals generated")
            continue
            
        train, test = split_train_test(signals)
        result = analyze_results(train, test, ticker, 'BB Squeeze + RSI <40')
        results.append(result)
        
        status_icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "⚠️")
        print(f"  {status_icon} {ticker}: Test={result['test_wr']}% (n={result['test_n']}), Decay={result['decay']}%")
    
    return results

def save_results(results):
    """Save results to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f'results/continuous_batch_{timestamp}.json'
    
    # Convert numpy booleans to Python booleans for JSON serialization
    clean_results = []
    for r in results:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, (np.bool_, np.integer)):
                clean_r[k] = bool(v) if isinstance(v, np.bool_) else int(v)
            else:
                clean_r[k] = v
        clean_results.append(clean_r)
    
    with open(filename, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    return filename

def print_summary(results):
    """Print summary of all results"""
    print("\n" + "=" * 70)
    print("RESEARCH SUMMARY")
    print("=" * 70)
    
    golden = [r for r in results if r['is_golden']]
    validated = [r for r in results if r['is_validated'] and not r['is_golden']]
    rejected = [r for r in results if not r['is_validated']]
    
    print(f"\n🏆 Golden Strategies: {len(golden)}")
    for r in golden:
        print(f"   • {r['ticker']}: {r['test_wr']}% (n={r['test_n']}) - {r['strategy']}")
    
    print(f"\n✅ Validated (55-70%): {len(validated)}")
    for r in validated[:5]:
        print(f"   • {r['ticker']}: {r['test_wr']}% (n={r['test_n']}) - {r['strategy']}")
    
    print(f"\n⚠️  Rejected/Insufficient: {len(rejected)}")
    
    # Best performers
    print("\n" + "=" * 70)
    print("TOP 5 PERFORMERS")
    print("=" * 70)
    sorted_results = sorted(results, key=lambda x: x['test_wr'], reverse=True)
    for i, r in enumerate(sorted_results[:5], 1):
        status = "🏆" if r['is_golden'] else ("✅" if r['is_validated'] else "⚠️")
        print(f"   {i}. {status} {r['ticker']}: {r['test_wr']}% (n={r['test_n']}) - {r['strategy'][:40]}")
    
    return golden, validated, rejected

if __name__ == '__main__':
    results = run_research_batch()
    
    if results:
        save_results(results)
        golden, validated, rejected = print_summary(results)
        
        # Create summary for Telegram
        summary = {
            'timestamp': datetime.now().isoformat(),
            'golden': golden,
            'validated': validated,
            'rejected_count': len(rejected),
            'total_tested': len(results)
        }
        
        with open('results/telegram_summary_latest.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n✅ Research batch complete!")
    else:
        print("\n❌ No results generated")
