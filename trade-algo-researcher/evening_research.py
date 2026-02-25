#!/usr/bin/env python3
"""
Continuous Strategy Research - Batch 2026-02-23 Evening
Tests: Bearish strategies, Multi-indicator combos, Volatility expansion
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Available tickers
TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'AMZN', 'GOOGL', 'DIS', 'CRM',
           'SPY', 'QQQ', 'IWM', 'MSTR', 'COIN']

def load_data(ticker):
    """Load indicator data for ticker"""
    try:
        df = pd.read_csv(f'data/{ticker}_indicators.csv')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except:
        return None

def calculate_returns(df, entry_idx, exit_days=5):
    """Calculate forward returns from entry point"""
    if entry_idx + exit_days >= len(df):
        return None
    entry_price = df.iloc[entry_idx]['close']
    exit_price = df.iloc[entry_idx + exit_days]['close']
    return (exit_price - entry_price) / entry_price

def walk_forward_split(df, train_end='2022-12-31'):
    """Split data into train and test periods"""
    train = df[df['date'] <= train_end].copy().reset_index(drop=True)
    test = df[df['date'] > train_end].copy().reset_index(drop=True)
    return train, test

def test_bearish_rsi(df, period=5):
    """Test bearish strategy: RSI > 70 (overbought) -> short"""
    signals = df[df['rsi'] > 70].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(-ret)  # Negative because we're shorting
    return returns, len(signals)

def test_bearish_stoch(df, period=5):
    """Test bearish strategy: Stoch %K > 80 -> short"""
    signals = df[df['stoch_k'] > 80].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(-ret)
    return returns, len(signals)

def test_multi_indicator_bullish(df, period=5):
    """Test: RSI < 30 + MACD bullish + Volume > avg"""
    df['volume_avg'] = df['volume'].rolling(20).mean()
    macd_bullish = df['macd'] > df['macd_signal']
    volume_high = df['volume'] > df['volume_avg']
    rsi_oversold = df['rsi'] < 30
    
    signals = df[rsi_oversold & macd_bullish & volume_high].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(ret)
    return returns, len(signals)

def test_bb_squeeze_breakout(df, period=5):
    """Test: BB squeeze (low volatility) -> volatility expansion"""
    df['bb_width_calc'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_width_avg'] = df['bb_width_calc'].rolling(20).mean()
    
    # Squeeze followed by breakout
    squeeze = df['bb_width_calc'] < df['bb_width_avg'] * 0.8
    breakout = df['close'] > df['bb_upper'].shift(1)
    
    signals = df[squeeze.shift(1).fillna(False) & breakout].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(ret)
    return returns, len(signals)

def test_atr_expansion(df, period=5):
    """Test: Low ATR period followed by expansion"""
    df['atr_low'] = df['atr'] < df['atr'].rolling(20).quantile(0.3)
    df['price_up'] = df['close'] > df['close'].shift(1) * 1.01
    
    signals = df[df['atr_low'].shift(1).fillna(False) & df['price_up']].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(ret)
    return returns, len(signals)

def test_rsi_macd_combo(df, period=5):
    """Test: RSI < 35 + MACD turning up"""
    macd_turning = df['macd'] > df['macd'].shift(1)
    macd_below_signal = df['macd'] < df['macd_signal']
    rsi_oversold = df['rsi'] < 35
    
    signals = df[rsi_oversold & macd_turning & macd_below_signal].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(ret)
    return returns, len(signals)

def test_stoch_bb_combo(df, period=5):
    """Test: Stoch < 20 + Price near BB lower"""
    near_bb_lower = df['close'] < df['bb_lower'] * 1.02
    stoch_oversold = df['stoch_k'] < 20
    
    signals = df[stoch_oversold & near_bb_lower].index.tolist()
    returns = []
    for idx in signals:
        ret = calculate_returns(df, idx, period)
        if ret is not None:
            returns.append(ret)
    return returns, len(signals)

def calculate_stats(returns, n_signals):
    """Calculate strategy statistics"""
    if not returns or n_signals == 0:
        return None
    
    returns = np.array(returns)
    wins = np.sum(returns > 0)
    win_rate = wins / len(returns) * 100
    avg_return = np.mean(returns) * 100
    
    # 95% confidence interval for win rate
    if len(returns) >= 10:
        p = win_rate / 100
        margin = 1.96 * np.sqrt(p * (1 - p) / len(returns))
        ci_lower = max(0, (p - margin) * 100)
        ci_upper = min(100, (p + margin) * 100)
    else:
        ci_lower = ci_upper = None
    
    return {
        'win_rate': round(win_rate, 1),
        'n_trades': len(returns),
        'avg_return': round(avg_return, 2),
        'ci_95': [round(ci_lower, 1), round(ci_upper, 1)] if ci_lower else None
    }

def run_research():
    """Run full research batch"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'hypotheses': {}
    }
    
    strategies = {
        'H1_Bearish_RSI_70': test_bearish_rsi,
        'H2_Bearish_Stoch_80': test_bearish_stoch,
        'H3_Multi_Ind_Bull': test_multi_indicator_bullish,
        'H4_BB_Squeeze_BO': test_bb_squeeze_breakout,
        'H5_ATR_Expansion': test_atr_expansion,
        'H6_RSI_MACD_Combo': test_rsi_macd_combo,
        'H7_Stoch_BB_Combo': test_stoch_bb_combo
    }
    
    for strat_name, strat_func in strategies.items():
        print(f"\n{'='*60}")
        print(f"Testing: {strat_name}")
        print('='*60)
        
        strat_results = {}
        
        for ticker in TICKERS:
            df = load_data(ticker)
            if df is None or len(df) < 100:
                continue
            
            train, test = walk_forward_split(df)
            
            # Test on test period (2023-2024)
            returns, n_signals = strat_func(test)
            stats = calculate_stats(returns, n_signals)
            
            if stats:
                strat_results[ticker] = stats
                print(f"  {ticker}: {stats['win_rate']}% win, n={stats['n_trades']}, avg={stats['avg_return']}%")
        
        results['hypotheses'][strat_name] = strat_results
    
    # Save results
    with open('results/evening_research_2026-02-23.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == '__main__':
    results = run_research()
    print("\n" + "="*60)
    print("RESEARCH COMPLETE")
    print("="*60)
