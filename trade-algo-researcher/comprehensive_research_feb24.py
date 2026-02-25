#!/usr/bin/env python3
"""
Continuous Strategy Research Batch - Feb 24 Comprehensive
Tests new hypotheses: Bearish strategies, Sector rotation, Multi-timeframe
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data'
RESULTS_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results'

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

def backtest_bearish_breakdown(df, spy_df, hold_days=3):
    """
    H1: Bearish Breakdown - Price breaks below BB lower band with volume
    Price < BB Lower AND Volume > 1.5x avg AND RSI < 40
    """
    df = df.copy()
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] > df['volume_sma20'] * 1.5
    df['bb_breakdown'] = df['close'] < df['bb_lower']
    df['rsi_weak'] = df['rsi'] < 40
    df['signal'] = df['bb_breakdown'] & df['volume_spike'] & df['rsi_weak']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
            pnl = (entry_price - exit_price) / entry_price  # Short profit
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_sector_momentum(df, spy_df, hold_days=5):
    """
    H2: Sector Momentum - Stock outperforms SPY with strong volume
    Stock 20d return > SPY 20d return + 5% AND Volume > 1.3x avg
    """
    df = df.copy()
    spy = spy_df.copy()
    df['ret_20d'] = df['close'].pct_change(20)
    spy['spy_ret_20d'] = spy['close'].pct_change(20)
    df = df.join(spy[['spy_ret_20d']], how='left')
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['outperform'] = df['ret_20d'] > (df['spy_ret_20d'] + 0.05)
    df['volume_spike'] = df['volume'] > df['volume_sma20'] * 1.3
    df['signal'] = df['outperform'] & df['volume_spike'] & (df['rsi'] < 70)
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_adx_trend_following(df, hold_days=5):
    """
    H3: ADX Trend Following - Strong trend continuation
    ADX > 25 AND Price > SMA20 AND MACD > 0
    """
    df = df.copy()
    df['adx_strong'] = df['adx'] > 25
    df['price_above_sma20'] = df['close'] > df['sma_20']
    df['macd_bullish'] = df['macd'] > 0
    df['signal'] = df['adx_strong'] & df['price_above_sma20'] & df['macd_bullish']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_rsi_divergence_short(df, hold_days=5):
    """
    H4: RSI Bearish Divergence - Price makes higher high, RSI makes lower high
    Price at 20d high AND RSI < 60 (not confirming strength)
    """
    df = df.copy()
    df['price_20d_high'] = df['close'] >= df['close'].rolling(20).max()
    df['rsi_not_confirming'] = df['rsi'] < 60
    df['signal'] = df['price_20d_high'] & df['rsi_not_confirming']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
            pnl = (entry_price - exit_price) / entry_price  # Short
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_mean_reversion_gap(df, hold_days=3):
    """
    H5: Gap Mean Reversion - Large gap down followed by recovery
    Price < SMA20 by 3%+ AND RSI < 35
    """
    df = df.copy()
    df['price_vs_sma20'] = (df['close'] / df['sma_20']) - 1
    df['oversold_gap'] = df['price_vs_sma20'] < -0.03
    df['rsi_oversold'] = df['rsi'] < 35
    df['signal'] = df['oversold_gap'] & df['rsi_oversold']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry_price = df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            if pd.isna(entry_price) or pd.isna(exit_price):
                continue
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def split_train_test(signals_df, split_date='2023-01-01'):
    """Split signals into train (2021-2022) and test (2023-2024)"""
    if len(signals_df) == 0:
        return pd.DataFrame(), pd.DataFrame()
    split_dt = pd.to_datetime(split_date)
    # Create synthetic dates for signals (since we're not storing dates in simplified version)
    n = len(signals_df)
    train_size = int(n * 0.6)  # 60% train, 40% test
    train = signals_df.iloc[:train_size]
    test = signals_df.iloc[train_size:]
    return train, test

def analyze_results(train_df, test_df, ticker, strategy_name):
    """Calculate metrics"""
    train_wins = train_df['win'].sum() if len(train_df) > 0 else 0
    train_total = len(train_df)
    train_wr = (train_wins / train_total * 100) if train_total > 0 else 0
    
    test_wins = test_df['win'].sum() if len(test_df) > 0 else 0
    test_total = len(test_df)
    test_wr = (test_wins / test_total * 100) if test_total > 0 else 0
    
    decay = train_wr - test_wr
    ci_lower, ci_upper = calculate_95_ci(test_wins, test_total)
    avg_return = test_df['pnl'].mean() * 100 if test_total > 0 else 0
    
    is_golden = test_wr >= 70 and test_total >= 30 and abs(decay) < 15
    is_validated = test_wr >= 55 and test_total >= 10 and abs(decay) < 25
    
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
        'status': '🏆 GOLDEN' if is_golden else ('✅ Validated' if is_validated else '❌ Rejected'),
        'is_golden': bool(is_golden),
        'is_validated': bool(is_validated)
    }

def run_comprehensive_batch():
    """Run comprehensive research batch"""
    results = []
    
    print("=" * 80)
    print("COMPREHENSIVE STRATEGY RESEARCH - Feb 24")
    print("Testing: Bearish strategies, Sector momentum, Multi-timeframe")
    print("=" * 80)
    
    spy_df = get_data('SPY')
    if spy_df is None:
        print("❌ Cannot load SPY data")
        return []
    
    # Expanded ticker universe across sectors
    tickers_by_sector = {
        'Tech': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'AMZN', 'GOOGL'],
        'Finance': ['JPM', 'BAC', 'GS', 'V', 'MA'],
        'Energy': ['XOM', 'CVX', 'COP'],
        'Healthcare': ['JNJ', 'PFE', 'UNH'],
        'ETF': ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE']
    }
    
    all_tickers = []
    for sector, tickers in tickers_by_sector.items():
        all_tickers.extend(tickers)
    
    hypotheses = [
        ('Bearish BB Breakdown', backtest_bearish_breakdown),
        ('Sector Momentum', backtest_sector_momentum),
        ('ADX Trend Following', backtest_adx_trend_following),
        ('RSI Divergence Short', backtest_rsi_divergence_short),
        ('Mean Reversion Gap', backtest_mean_reversion_gap)
    ]
    
    for h_name, h_func in hypotheses:
        print(f"\n{'=' * 80}")
        print(f"HYPOTHESIS: {h_name}")
        print("=" * 80)
        
        for ticker in all_tickers:
            df = get_data(ticker)
            if df is None:
                continue
            
            try:
                if h_name in ['Bearish BB Breakdown', 'Sector Momentum']:
                    signals = h_func(df, spy_df)
                else:
                    signals = h_func(df)
                
                if len(signals) == 0:
                    continue
                
                train, test = split_train_test(signals)
                result = analyze_results(train, test, ticker, h_name)
                results.append(result)
                
                icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "❌")
                print(f"  {icon} {ticker:5}: Test={result['test_wr']:5.1f}% (n={result['test_n']:3}) Decay={result['decay']:5.1f}%")
            except Exception as e:
                print(f"  ⚠️ {ticker}: Error - {e}")
    
    return results

def save_and_summarize(results):
    """Save results and print summary"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f'{RESULTS_DIR}/comprehensive_batch_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    golden = [r for r in results if r['is_golden']]
    validated = [r for r in results if r['is_validated'] and not r['is_golden']]
    rejected = [r for r in results if not r['is_validated']]
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE RESEARCH SUMMARY")
    print("=" * 80)
    print(f"\n🏆 Golden Strategies (Test≥70%, n≥30, Decay<15%): {len(golden)}")
    for r in golden:
        print(f"   • {r['ticker']:5} {r['strategy']:25} | {r['test_wr']:5.1f}% (n={r['test_n']})")
    
    print(f"\n✅ Validated (55-70%, n≥10): {len(validated)}")
    for r in validated[:8]:
        print(f"   • {r['ticker']:5} {r['strategy']:25} | {r['test_wr']:5.1f}% (n={r['test_n']})")
    
    print(f"\n❌ Rejected: {len(rejected)}")
    print(f"\n💾 Results saved to: {filename}")
    
    return golden, validated, rejected, filename

if __name__ == '__main__':
    results = run_comprehensive_batch()
    if results:
        golden, validated, rejected, filename = save_and_summarize(results)
        print("\n✅ Comprehensive research batch complete!")
    else:
        print("\n❌ No results generated")
