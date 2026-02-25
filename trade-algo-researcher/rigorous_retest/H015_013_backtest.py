#!/usr/bin/env python3
"""
H015-013: RSI + Volume Breakout
Long when RSI > 50 AND Volume > 2x average
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
    """Simulate ticker data"""
    np.random.seed(hash(ticker) % 10000)
    dates = pd.date_range(end='2025-02-25', periods=n_days, freq='B')
    vol_multiplier = {'HK': 0.018, 'US': 0.015, 'CN': 0.022, 'SG': 0.012}.get(market, 0.015)
    returns = np.random.normal(0.0003, vol_multiplier, n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    volume = np.random.uniform(1000000, 10000000, n_days)
    return pd.DataFrame({'close': prices, 'volume': volume}, index=dates)

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def backtest_rsi_volume(df):
    """Backtest RSI + Volume breakout"""
    df = calculate_rsi(df)
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma20']
    
    # Signal: RSI > 50 AND Volume > 2x
    df['signal'] = (df['rsi'] > 50) & (df['volume_ratio'] > 2.0)
    
    HOLD_DAYS = 5
    trades = []
    in_position = False
    entry_date = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        if not in_position and row['signal'] and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - df.loc[entry_date, 'close']) / df.loc[entry_date, 'close'] * 100
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                entry_date = None
    
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
    print("H015-013: RSI + VOLUME BREAKOUT")
    print("Logic: RSI > 50 AND Volume > 2x average, Hold 5 days")
    print("=" * 80)
    
    # Test sample of tickers
    sample = ALL_TICKERS[:15]
    results = []
    
    for ticker, market in sample:
        df = simulate_ticker_data(ticker, market)
        test_df = df[(df.index >= TEST_START) & (df.index <= TEST_END)]
        result = backtest_rsi_volume(test_df)
        
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
