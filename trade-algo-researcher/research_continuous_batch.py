#!/usr/bin/env python3
"""
Continuous Strategy Research — Feb 24, 2026
Test new hypotheses and enhance existing strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Configuration
TRAIN_START = '2021-01-01'
TRAIN_END = '2022-12-31'
TEST_START = '2023-01-01'
TEST_END = '2024-12-31'
TICKERS = ['AAPL', 'AMD', 'COIN', 'META', 'MSFT', 'MSTR', 'NVDA', 'QQQ', 'SPY', 'TSLA']

def load_data(ticker):
    """Load indicator data for a ticker"""
    try:
        df = pd.read_csv(f'/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data/{ticker}_indicators.csv')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error loading {ticker}: {e}")
        return None

def calculate_win_rate(returns):
    """Calculate win rate from returns"""
    if len(returns) == 0:
        return 0, 0
    wins = sum(1 for r in returns if r > 0)
    return (wins / len(returns)) * 100, len(returns)

def conf_interval(win_rate, n, confidence=0.95):
    """Calculate confidence interval for win rate"""
    if n < 5:
        return (0, 100)
    import math
    z = 1.96 if confidence == 0.95 else 2.576
    p = win_rate / 100
    se = math.sqrt(p * (1 - p) / n)
    margin = z * se
    return max(0, (p - margin) * 100), min(100, (p + margin) * 100)

def run_backtest(df, entry_mask, hold_days=5, profit_target=None, stop_loss=None):
    """Run backtest with given entry conditions"""
    trades = []
    
    for i in range(len(df) - hold_days):
        if entry_mask.iloc[i] and i + hold_days < len(df):
            entry_price = df['close'].iloc[i]
            exit_idx = i + hold_days
            
            # Check for early exit on profit target or stop loss
            for j in range(i+1, min(i + hold_days + 1, len(df))):
                current_price = df['close'].iloc[j]
                pnl = (current_price - entry_price) / entry_price
                
                if profit_target and pnl >= profit_target:
                    exit_idx = j
                    break
                if stop_loss and pnl <= -stop_loss:
                    exit_idx = j
                    break
            
            exit_price = df['close'].iloc[exit_idx]
            ret = (exit_price - entry_price) / entry_price
            trades.append(ret)
    
    return trades

# ==================== HYPOTHESIS TESTING ====================

def test_h6_stoch_macd_confluence(df, period='test'):
    """H6: Stochastic < 20 + MACD > Signal + Price > SMA50"""
    mask = (df['stoch_k'] < 20) & (df['macd'] > df['macd_signal']) & (df['close'] > df['sma_50'])
    return run_backtest(df, mask, hold_days=5)

def test_h7_adx_volume_breakout(df, period='test'):
    """H7: ADX > 30 + Volume > 1.5x avg + Price breakout (close > sma_20 + atr)"""
    vol_avg = df['volume'].rolling(20).mean()
    breakout_level = df['sma_20'] + df['atr']
    mask = (df['adx'] > 30) & (df['volume'] > 1.5 * vol_avg) & (df['close'] > breakout_level)
    return run_backtest(df, mask, hold_days=3)

def test_h8_rsi_divergence(df, period='test'):
    """H8: Price lower low + RSI higher low (bullish divergence)"""
    # Simplified divergence detection - 5-day lookback
    price_ll = df['close'] < df['close'].shift(5)
    rsi_hl = df['rsi'] > df['rsi'].shift(5)
    vol_confirm = df['volume'] > df['volume'].rolling(20).mean()
    mask = price_ll & rsi_hl & (df['rsi'] < 50) & vol_confirm
    return run_backtest(df, mask, hold_days=5)

def test_h9_bb_mean_reversion_v2(df, period='test'):
    """H9: Price < BB_Lower + RSI < 35 + ADX > 20 (trending mean reversion)"""
    mask = (df['close'] < df['bb_lower']) & (df['rsi'] < 35) & (df['adx'] > 20)
    return run_backtest(df, mask, hold_days=5)

def test_h10_adx_momentum_combo(df, period='test'):
    """H10: ADX > 25 + MACD > 0 + RSI 40-70 (trend continuation)"""
    mask = (df['adx'] > 25) & (df['macd'] > 0) & (df['rsi'] >= 40) & (df['rsi'] <= 70)
    return run_backtest(df, mask, hold_days=5)

def test_h11_stoch_bb_combo(df, period='test'):
    """H11: Stoch < 20 + Price < BB_Lower (double oversold)"""
    mask = (df['stoch_k'] < 20) & (df['close'] < df['bb_lower'])
    return run_backtest(df, mask, hold_days=5)

def test_e5_adx_profit_target(df, period='test'):
    """E5: ADX > 25 + Price > SMA20 with 5% profit target"""
    mask = (df['adx'] > 25) & (df['close'] > df['sma_20'])
    return run_backtest(df, mask, hold_days=10, profit_target=0.05)

def test_e6_bb_walk_trailing(df, period='test'):
    """E6: BB Walk with trailing stop (3% trailing)"""
    # Price near upper BB + ADX > 30 + uptrend
    mask = (df['close'] > 0.98 * df['bb_upper']) & (df['adx'] > 30) & (df['close'] > df['sma_50'])
    return run_backtest(df, mask, hold_days=5, stop_loss=0.03)

# Run all tests
def run_research():
    results = []
    
    for ticker in TICKERS:
        print(f"\n=== Testing {ticker} ===")
        df = load_data(ticker)
        if df is None or df.empty:
            continue
        
        # Split train/test
        train_mask = (df['date'] >= TRAIN_START) & (df['date'] <= TRAIN_END)
        test_mask = (df['date'] >= TEST_START) & (df['date'] <= TEST_END)
        df_train = df[train_mask].copy()
        df_test = df[test_mask].copy()
        
        if len(df_train) == 0 or len(df_test) == 0:
            print(f"  Insufficient data for {ticker}")
            continue
        
        hypotheses = [
            ('H6_Stoch_MACD', test_h6_stoch_macd_confluence),
            ('H7_ADX_Vol_BO', test_h7_adx_volume_breakout),
            ('H8_RSI_Divergence', test_h8_rsi_divergence),
            ('H9_BB_MR_v2', test_h9_bb_mean_reversion_v2),
            ('H10_ADX_Momentum', test_h10_adx_momentum_combo),
            ('H11_Stoch_BB', test_h11_stoch_bb_combo),
            ('E5_ADX_ProfitTarget', test_e5_adx_profit_target),
            ('E6_BB_Walk_Trailing', test_e6_bb_walk_trailing),
        ]
        
        for name, func in hypotheses:
            try:
                train_returns = func(df_train, 'train')
                test_returns = func(df_test, 'test')
                
                train_wr, train_n = calculate_win_rate(train_returns)
                test_wr, test_n = calculate_win_rate(test_returns)
                decay = train_wr - test_wr
                ci_low, ci_high = conf_interval(test_wr, test_n)
                avg_ret = np.mean(test_returns) * 100 if test_returns else 0
                
                # Determine status
                if test_wr >= 70 and test_n >= 30 and decay < 15:
                    status = 'GOLDEN'
                elif test_wr >= 55 and test_n >= 10:
                    status = 'VALIDATED'
                elif test_wr >= 55 and test_n >= 5:
                    status = 'NEAR'
                else:
                    status = 'REJECTED'
                
                result = {
                    'ticker': ticker,
                    'hypothesis': name,
                    'train_wr': round(train_wr, 1),
                    'test_wr': round(test_wr, 1),
                    'train_n': train_n,
                    'test_n': test_n,
                    'decay': round(decay, 1),
                    'ci_low': round(ci_low, 1),
                    'ci_high': round(ci_high, 1),
                    'avg_return': round(avg_ret, 2),
                    'status': status
                }
                results.append(result)
                
                if status == 'GOLDEN':
                    print(f"  🏆 GOLDEN: {name}: {test_wr:.1f}% (n={test_n})")
                elif status == 'VALIDATED':
                    print(f"  ✅ VALID: {name}: {test_wr:.1f}% (n={test_n})")
                    
            except Exception as e:
                print(f"  Error testing {name}: {e}")
    
    return results

if __name__ == '__main__':
    results = run_research()
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'golden': [r for r in results if r['status'] == 'GOLDEN'],
        'validated': [r for r in results if r['status'] == 'VALIDATED'],
        'near': [r for r in results if r['status'] == 'NEAR'],
        'rejected': [r for r in results if r['status'] == 'REJECTED'],
        'all_results': results
    }
    
    output_file = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/continuous_batch_2026-02-24_1325.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"RESEARCH COMPLETE")
    print(f"{'='*60}")
    print(f"Total tests: {len(results)}")
    print(f"Golden: {len(output['golden'])}")
    print(f"Validated: {len(output['validated'])}")
    print(f"Near: {len(output['near'])}")
    print(f"Rejected: {len(output['rejected'])}")
    print(f"\nResults saved to: {output_file}")
