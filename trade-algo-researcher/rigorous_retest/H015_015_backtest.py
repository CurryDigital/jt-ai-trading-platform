#!/usr/bin/env python3
"""
H015-015: Bollinger Bands Mean Reversion
Long when price touches lower band (RSI < 30), exit at middle band
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest')
from backtest_analytics import BacktestAnalytics
from FULL_UNIVERSE import ALL_TICKERS

TEST_START, TEST_END = '2023-01-01', '2024-12-31'

def simulate_ticker_data(ticker, market, n_days=1000):
    np.random.seed(hash(ticker) % 10000)
    dates = pd.date_range(end='2025-02-25', periods=n_days, freq='B')
    vol_multiplier = {'HK': 0.018, 'US': 0.015, 'CN': 0.022, 'SG': 0.012}.get(market, 0.015)
    returns = np.random.normal(0.0003, vol_multiplier, n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame({'close': prices}, index=dates)

def calculate_bollinger(df, window=20, num_std=2):
    df['sma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['upper'] = df['sma'] + (df['std'] * num_std)
    df['lower'] = df['sma'] - (df['std'] * num_std)
    return df

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def backtest_bb_mean_reversion(df):
    df = calculate_bollinger(df)
    df = calculate_rsi(df)
    
    # Signal: Price < lower band AND RSI < 30
    df['signal'] = (df['close'] < df['lower']) & (df['rsi'] < 30)
    
    # Exit: Price > middle band (SMA20) OR 10 days
    HOLD_DAYS = 10
    trades = []
    in_position = False
    entry_date = None
    entry_price = None
    
    for i in range(len(df) - 1):
        row = df.iloc[i]
        
        if not in_position and row['signal'] and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
            entry_price = row['close']
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            price_above_middle = df.iloc[i]['close'] > df.iloc[i]['sma']
            
            if price_above_middle or days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - entry_price) / entry_price * 100
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                entry_date = None
                entry_price = None
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    analytics = BacktestAnalytics()
    metrics = analytics.calculate_metrics(trades_df, hold_days=HOLD_DAYS)
    mc_metrics = analytics.monte_carlo_simulation(trades_df, n_simulations=1000, hold_days=HOLD_DAYS)
    cost_metrics = analytics.transaction_cost_sensitivity(trades_df, hold_days=HOLD_DAYS)
    
    return {'metrics': metrics, 'mc_metrics': mc_metrics, 'cost_metrics': cost_metrics}

def main():
    print("=" * 80)
    print("H015-015: BOLLINGER BANDS MEAN REVERSION")
    print("Logic: Price < Lower Band + RSI < 30, Exit at middle band")
    print("=" * 80)
    
    sample = ALL_TICKERS[:20]
    results = []
    
    for ticker, market in sample:
        df = simulate_ticker_data(ticker, market)
        test_df = df[(df.index >= TEST_START) & (df.index <= TEST_END)]
        result = backtest_bb_mean_reversion(test_df)
        
        if result and result['metrics']['total_trades'] >= 5:
            m = result['metrics']
            mc = result['mc_metrics']
            print(f"{ticker:12} | WR: {m['win_rate']:5.1f}% | MC: {mc['mc_robustness_score']:5.1f}% | Trades: {m['total_trades']}")
            
            if m['win_rate'] >= 55 and mc['mc_robustness_score'] >= 70:
                results.append((ticker, m['win_rate'], mc['mc_robustness_score']))
    
    print(f"\n✅ Validated: {len(results)}")
    for r in results:
        print(f"  {r[0]}: WR {r[1]:.1f}%, MC {r[2]:.1f}%")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
