#!/usr/bin/env python3
"""
Hypothesis Testing Batch - 3 Bearish/Multi-Timeframe Strategies
Tests H1, H2, H3 with walk-forward validation (Train: 2021-2022, Test: 2023-2024)
"""
import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

def get_auth_token():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    return rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    )

def get_connection():
    token = get_auth_token()
    return psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432,
        database='aitrading',
        user='openclaw_user',
        password=token,
        sslmode='require'
    )

def get_price_data(ticker: str, conn) -> pd.DataFrame:
    """Get price data from silver schema (try unified_prices first, then historical_stock_data)"""
    # Try unified_prices first (for COIN, MSTR, SPY, QQQ)
    query = """
        SELECT date, open, high, low, close, volume
        FROM silver.unified_prices
        WHERE ticker = %s
        ORDER BY date
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    
    if len(df) == 0:
        # Fall back to historical_stock_data
        query = """
            SELECT date, open, high, low, close, volume
            FROM silver.historical_stock_data
            WHERE ticker = %s
            ORDER BY date
        """
        df = pd.read_sql(query, conn, params=(ticker,))
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def get_indicator_data(ticker: str, conn) -> pd.DataFrame:
    """Get indicator data from gold schema"""
    query = """
        SELECT date, rsi_14, stoch_k, stoch_d, adx, bb_upper, bb_middle, bb_lower
        FROM gold.technical_indicators_calculated
        WHERE ticker = %s
        ORDER BY date
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def calculate_weekly_sma(prices: pd.Series, window: int = 20) -> pd.Series:
    """Calculate weekly SMA from daily data"""
    weekly = prices.resample('W-FRI').last()
    weekly_sma = weekly.rolling(window=window).mean()
    # Forward fill to daily frequency
    return weekly_sma.reindex(prices.index, method='ffill')

def calculate_95_ci(wins: int, n: int) -> Tuple[float, float]:
    """Calculate 95% confidence interval for win rate"""
    if n == 0:
        return (0, 0)
    p = wins / n
    # Wilson score interval
    z = 1.96  # 95% CI
    denominator = 1 + z**2/n
    centre = (p + z**2/(2*n)) / denominator
    half_width = z * np.sqrt((p*(1-p) + z**2/(4*n)) / n) / denominator
    return (max(0, centre - half_width) * 100, min(100, centre + half_width) * 100)

def backtest_h1_bearish_rsi(ticker: str, conn, train_start='2021-01-01', train_end='2022-12-31', 
                             test_start='2023-01-01', test_end='2024-12-31') -> Dict:
    """
    H1: Bearish RSI Overbought Short
    Entry: RSI > 70
    Exit: RSI < 50 OR 5 days OR -5% stop (profit target for short)
    """
    try:
        prices = get_price_data(ticker, conn)
        indicators = get_indicator_data(ticker, conn)
        
        if len(prices) == 0 or len(indicators) == 0:
            return {'error': 'No data available'}
        
        # Merge data
        data = prices.join(indicators, how='inner')
        if len(data) == 0:
            return {'error': 'No overlapping data'}
        
        results = {'ticker': ticker, 'train': {}, 'test': {}}
        
        for period, start, end in [('train', train_start, train_end), ('test', test_start, test_end)]:
            period_data = data[(data.index >= start) & (data.index <= end)].copy()
            if len(period_data) < 30:
                results[period] = {'error': 'Insufficient data', 'n': len(period_data)}
                continue
            
            trades = []
            in_position = False
            entry_date = None
            entry_price = None
            days_held = 0
            
            for i in range(1, len(period_data)):
                date = period_data.index[i]
                prev_row = period_data.iloc[i-1]
                curr_row = period_data.iloc[i]
                
                # Skip if RSI is NaN
                if pd.isna(prev_row['rsi_14']):
                    continue
                
                if not in_position:
                    # Entry: RSI > 70 (short signal)
                    if prev_row['rsi_14'] > 70:
                        in_position = True
                        entry_date = date
                        entry_price = curr_row['open']  # Enter at next open
                        days_held = 0
                else:
                    days_held += 1
                    exit_price = None
                    exit_reason = None
                    
                    # Check exit conditions
                    # 1. RSI < 50
                    if prev_row['rsi_14'] < 50:
                        exit_price = curr_row['open']
                        exit_reason = 'RSI<50'
                    # 2. 5 days elapsed
                    elif days_held >= 5:
                        exit_price = curr_row['close']
                        exit_reason = 'Time'
                    # 3. -5% stop (for short, price went up 5% means loss)
                    elif (curr_row['high'] - entry_price) / entry_price >= 0.05:
                        exit_price = entry_price * 1.05  # Stop loss
                        exit_reason = 'Stop'
                    # 4. +5% profit target (for short, price dropped 5%)
                    elif (entry_price - curr_row['low']) / entry_price >= 0.05:
                        exit_price = entry_price * 0.95  # Take profit
                        exit_reason = 'Profit'
                    
                    if exit_price:
                        pnl_pct = (entry_price - exit_price) / entry_price * 100  # Short profit
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pct': pnl_pct,
                            'days': days_held,
                            'reason': exit_reason
                        })
                        in_position = False
            
            # Calculate metrics
            if trades:
                wins = sum(1 for t in trades if t['pnl_pct'] > 0)
                n = len(trades)
                win_pct = wins / n * 100
                ci_lower, ci_upper = calculate_95_ci(wins, n)
                avg_return = np.mean([t['pnl_pct'] for t in trades])
                avg_days = np.mean([t['days'] for t in trades])
                
                results[period] = {
                    'n': n,
                    'wins': wins,
                    'win_pct': round(win_pct, 1),
                    'ci_95': (round(ci_lower, 1), round(ci_upper, 1)),
                    'avg_return': round(avg_return, 2),
                    'avg_days': round(avg_days, 1),
                    'trades': trades
                }
            else:
                results[period] = {'n': 0, 'win_pct': 0, 'ci_95': (0, 0)}
        
        # Calculate decay
        if 'win_pct' in results['train'] and 'win_pct' in results['test']:
            train_wr = results['train']['win_pct']
            test_wr = results['test']['win_pct']
            if train_wr > 0:
                decay = (train_wr - test_wr) / train_wr * 100
            else:
                decay = 0
            results['decay'] = round(decay, 1)
        
        return results
    except Exception as e:
        return {'error': str(e)}

def backtest_h2_bearish_stoch(ticker: str, conn, train_start='2021-01-01', train_end='2022-12-31',
                               test_start='2023-01-01', test_end='2024-12-31') -> Dict:
    """
    H2: Bearish Stochastic Overbought Short
    Entry: %K > 80 AND %D > 75
    Exit: %K < 50 OR 5 days OR -5% stop
    """
    try:
        prices = get_price_data(ticker, conn)
        indicators = get_indicator_data(ticker, conn)
        
        if len(prices) == 0 or len(indicators) == 0:
            return {'error': 'No data available'}
        
        data = prices.join(indicators, how='inner')
        if len(data) == 0:
            return {'error': 'No overlapping data'}
        
        results = {'ticker': ticker, 'train': {}, 'test': {}}
        
        for period, start, end in [('train', train_start, train_end), ('test', test_start, test_end)]:
            period_data = data[(data.index >= start) & (data.index <= end)].copy()
            if len(period_data) < 30:
                results[period] = {'error': 'Insufficient data', 'n': len(period_data)}
                continue
            
            trades = []
            in_position = False
            entry_date = None
            entry_price = None
            days_held = 0
            
            for i in range(1, len(period_data)):
                date = period_data.index[i]
                prev_row = period_data.iloc[i-1]
                curr_row = period_data.iloc[i]
                
                if pd.isna(prev_row['stoch_k']) or pd.isna(prev_row['stoch_d']):
                    continue
                
                if not in_position:
                    # Entry: %K > 80 AND %D > 75
                    if prev_row['stoch_k'] > 80 and prev_row['stoch_d'] > 75:
                        in_position = True
                        entry_date = date
                        entry_price = curr_row['open']
                        days_held = 0
                else:
                    days_held += 1
                    exit_price = None
                    exit_reason = None
                    
                    # Exit: %K < 50
                    if prev_row['stoch_k'] < 50:
                        exit_price = curr_row['open']
                        exit_reason = 'Stoch<50'
                    elif days_held >= 5:
                        exit_price = curr_row['close']
                        exit_reason = 'Time'
                    elif (curr_row['high'] - entry_price) / entry_price >= 0.05:
                        exit_price = entry_price * 1.05
                        exit_reason = 'Stop'
                    elif (entry_price - curr_row['low']) / entry_price >= 0.05:
                        exit_price = entry_price * 0.95
                        exit_reason = 'Profit'
                    
                    if exit_price:
                        pnl_pct = (entry_price - exit_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pct': pnl_pct,
                            'days': days_held,
                            'reason': exit_reason
                        })
                        in_position = False
            
            if trades:
                wins = sum(1 for t in trades if t['pnl_pct'] > 0)
                n = len(trades)
                win_pct = wins / n * 100
                ci_lower, ci_upper = calculate_95_ci(wins, n)
                avg_return = np.mean([t['pnl_pct'] for t in trades])
                
                results[period] = {
                    'n': n,
                    'wins': wins,
                    'win_pct': round(win_pct, 1),
                    'ci_95': (round(ci_lower, 1), round(ci_upper, 1)),
                    'avg_return': round(avg_return, 2),
                    'trades': trades
                }
            else:
                results[period] = {'n': 0, 'win_pct': 0, 'ci_95': (0, 0)}
        
        if 'win_pct' in results['train'] and 'win_pct' in results['test']:
            train_wr = results['train']['win_pct']
            test_wr = results['test']['win_pct']
            if train_wr > 0:
                decay = (train_wr - test_wr) / train_wr * 100
            else:
                decay = 0
            results['decay'] = round(decay, 1)
        
        return results
    except Exception as e:
        return {'error': str(e)}

def backtest_h3_weekly_trend_daily_mr(ticker: str, conn, train_start='2021-01-01', train_end='2022-12-31',
                                        test_start='2023-01-01', test_end='2024-12-31') -> Dict:
    """
    H3: Weekly Trend + Daily Mean Reversion (LONG)
    Entry: Weekly Close > Weekly 20-SMA AND Daily RSI < 30
    Exit: RSI > 50 OR 5 days OR +5% profit
    """
    try:
        prices = get_price_data(ticker, conn)
        indicators = get_indicator_data(ticker, conn)
        
        if len(prices) == 0 or len(indicators) == 0:
            return {'error': 'No data available'}
        
        data = prices.join(indicators, how='inner')
        if len(data) == 0:
            return {'error': 'No overlapping data'}
        
        # Calculate weekly 20-SMA
        data['weekly_sma20'] = calculate_weekly_sma(data['close'], 20)
        
        results = {'ticker': ticker, 'train': {}, 'test': {}}
        
        for period, start, end in [('train', train_start, train_end), ('test', test_start, test_end)]:
            period_data = data[(data.index >= start) & (data.index <= end)].copy()
            if len(period_data) < 30:
                results[period] = {'error': 'Insufficient data', 'n': len(period_data)}
                continue
            
            trades = []
            in_position = False
            entry_date = None
            entry_price = None
            days_held = 0
            
            for i in range(1, len(period_data)):
                date = period_data.index[i]
                prev_row = period_data.iloc[i-1]
                curr_row = period_data.iloc[i]
                
                if pd.isna(prev_row['rsi_14']) or pd.isna(prev_row['weekly_sma20']):
                    continue
                
                weekly_uptrend = prev_row['close'] > prev_row['weekly_sma20']
                
                if not in_position:
                    # Entry: Weekly uptrend AND Daily RSI < 30 (LONG)
                    if weekly_uptrend and prev_row['rsi_14'] < 30:
                        in_position = True
                        entry_date = date
                        entry_price = curr_row['open']
                        days_held = 0
                else:
                    days_held += 1
                    exit_price = None
                    exit_reason = None
                    
                    # Exit: RSI > 50
                    if prev_row['rsi_14'] > 50:
                        exit_price = curr_row['open']
                        exit_reason = 'RSI>50'
                    elif days_held >= 5:
                        exit_price = curr_row['close']
                        exit_reason = 'Time'
                    elif (entry_price - curr_row['low']) / entry_price >= 0.05:
                        exit_price = entry_price * 0.95  # Stop loss
                        exit_reason = 'Stop'
                    elif (curr_row['high'] - entry_price) / entry_price >= 0.05:
                        exit_price = entry_price * 1.05  # Profit target
                        exit_reason = 'Profit'
                    
                    if exit_price:
                        pnl_pct = (exit_price - entry_price) / entry_price * 100  # Long profit
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pct': pnl_pct,
                            'days': days_held,
                            'reason': exit_reason
                        })
                        in_position = False
            
            if trades:
                wins = sum(1 for t in trades if t['pnl_pct'] > 0)
                n = len(trades)
                win_pct = wins / n * 100
                ci_lower, ci_upper = calculate_95_ci(wins, n)
                avg_return = np.mean([t['pnl_pct'] for t in trades])
                
                results[period] = {
                    'n': n,
                    'wins': wins,
                    'win_pct': round(win_pct, 1),
                    'ci_95': (round(ci_lower, 1), round(ci_upper, 1)),
                    'avg_return': round(avg_return, 2),
                    'trades': trades
                }
            else:
                results[period] = {'n': 0, 'win_pct': 0, 'ci_95': (0, 0)}
        
        if 'win_pct' in results['train'] and 'win_pct' in results['test']:
            train_wr = results['train']['win_pct']
            test_wr = results['test']['win_pct']
            if train_wr > 0:
                decay = (train_wr - test_wr) / train_wr * 100
            else:
                decay = 0
            results['decay'] = round(decay, 1)
        
        return results
    except Exception as e:
        return {'error': str(e)}

def determine_status(test_wr: float, n: int, decay: float, is_long: bool = True) -> str:
    """Determine strategy status based on criteria"""
    if n < 30:
        return "INSUFFICIENT"
    
    if is_long:
        if test_wr >= 70 and decay < 15:
            return "GOLDEN"
        elif test_wr >= 55:
            return "VALIDATED"
        else:
            return "REJECTED"
    else:
        # Short strategies use slightly lower threshold
        if test_wr >= 70 and decay < 15:
            return "GOLDEN"
        elif test_wr >= 55:
            return "VALIDATED"
        else:
            return "REJECTED"

def run_all_tests():
    """Run all hypothesis tests"""
    conn = get_connection()
    
    print("="*80)
    print("HYPOTHESIS TESTING BATCH - BEARISH & MULTI-TIMEFRAME STRATEGIES")
    print("="*80)
    
    # H1: Bearish RSI Overbought Short
    print("\n" + "="*80)
    print("H1: Bearish RSI Overbought Short (RSI > 70)")
    print("="*80)
    h1_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR']
    h1_results = {}
    
    for ticker in h1_tickers:
        print(f"\nTesting {ticker}...")
        result = backtest_h1_bearish_rsi(ticker, conn)
        h1_results[ticker] = result
        
        if 'error' not in result:
            test_wr = result['test'].get('win_pct', 0)
            n = result['test'].get('n', 0)
            decay = result.get('decay', 0)
            ci = result['test'].get('ci_95', (0, 0))
            status = determine_status(test_wr, n, decay, is_long=False)
            
            print(f"  Test Win%: {test_wr}% (95% CI: {ci[0]}%-{ci[1]}%)")
            print(f"  n: {n} | Decay: {decay}% | Status: {status}")
    
    # H2: Bearish Stochastic Overbought Short
    print("\n" + "="*80)
    print("H2: Bearish Stochastic Overbought Short (%K > 80 AND %D > 75)")
    print("="*80)
    h2_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'QQQ']
    h2_results = {}
    
    for ticker in h2_tickers:
        print(f"\nTesting {ticker}...")
        result = backtest_h2_bearish_stoch(ticker, conn)
        h2_results[ticker] = result
        
        if 'error' not in result:
            test_wr = result['test'].get('win_pct', 0)
            n = result['test'].get('n', 0)
            decay = result.get('decay', 0)
            ci = result['test'].get('ci_95', (0, 0))
            status = determine_status(test_wr, n, decay, is_long=False)
            
            print(f"  Test Win%: {test_wr}% (95% CI: {ci[0]}%-{ci[1]}%)")
            print(f"  n: {n} | Decay: {decay}% | Status: {status}")
    
    # H3: Weekly Trend + Daily Mean Reversion
    print("\n" + "="*80)
    print("H3: Weekly Trend + Daily Mean Reversion (LONG)")
    print("="*80)
    h3_tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
    h3_results = {}
    
    for ticker in h3_tickers:
        print(f"\nTesting {ticker}...")
        result = backtest_h3_weekly_trend_daily_mr(ticker, conn)
        h3_results[ticker] = result
        
        if 'error' not in result:
            test_wr = result['test'].get('win_pct', 0)
            n = result['test'].get('n', 0)
            decay = result.get('decay', 0)
            ci = result['test'].get('ci_95', (0, 0))
            status = determine_status(test_wr, n, decay, is_long=True)
            
            print(f"  Test Win%: {test_wr}% (95% CI: {ci[0]}%-{ci[1]}%)")
            print(f"  n: {n} | Decay: {decay}% | Status: {status}")
    
    conn.close()
    
    return {
        'H1': h1_results,
        'H2': h2_results,
        'H3': h3_results
    }

if __name__ == "__main__":
    results = run_all_tests()
    
    # Save results to JSON
    with open('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/hypothesis_batch_results.json', 'w') as f:
        # Convert trades to serializable format
        serializable = {}
        for h, tickers in results.items():
            serializable[h] = {}
            for ticker, data in tickers.items():
                serializable[h][ticker] = data
        json.dump(serializable, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("Results saved to results/hypothesis_batch_results.json")
