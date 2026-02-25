#!/usr/bin/env python3
"""
FIX FAILING STRATEGIES - Try Different Metrics
S001-02, S001-09, S007-01
"""

import pandas as pd
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
from backtest_analytics import BacktestAnalytics

db = TradeAlgoDB()
conn = db.connect()

TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'
VALIDATE_START = '2025-01-01'
LAST_Q_START = '2024-10-01'

def fetch_data(ticker):
    query = f"""
    SELECT date, close, volume FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    query = f"""
    SELECT date, rsi_14, bb_upper, bb_lower, bb_middle, adx, macd_line, macd_signal FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def calc_metrics(trades_df, hold_days=10):
    if len(trades_df) < 5:
        return None
    
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc(t):
        if len(t) < 3:
            return {'trades': len(t), 'wr': 0, 'pnl': 0}
        return {'trades': len(t), 'wr': (t['pnl'] > 0).sum()/len(t)*100, 'pnl': t['pnl'].sum()}
    
    train_m = calc(train)
    test_m = calc(test)
    validate_m = calc(validate)
    last_q_m = calc(last_q)
    
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=hold_days) if len(test) >= 10 else {'mc_robustness_score': 0}
    decay = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    score = sum([
        test_m['wr'] >= 55,
        test_m['trades'] >= 20,
        mc['mc_robustness_score'] >= 70,
        decay <= 20,
        last_q_m['pnl'] > 0
    ])
    
    status = "🏆 GOLDEN" if score == 5 else "⭐ VALIDATED" if score >= 3 else "📝 HYPOTHESIS"
    
    return {
        'train': train_m, 'test': test_m, 'validate': validate_m, 'last_q': last_q_m,
        'decay': decay, 'mc': mc['mc_robustness_score'], 'score': score, 'status': status
    }

# ==================== FIX S001-02: US Consumer ====================
print("=" * 100)
print("FIXING S001-02: RSI MR US Consumer")
print("=" * 100)

consumer_tickers = ['COST', 'WMT']

# Try different combinations
fixes = [
    ('RSI < 35 only', 'rsi35'),
    ('RSI < 30 + Price < SMA20', 'rsi30_below_sma'),
    ('RSI < 35 + Volume > 1.5x', 'rsi35_vol'),
]

for fix_name, fix_type in fixes:
    trades = []
    for ticker in consumer_tickers:
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        df['sma20'] = df['close'].rolling(20).mean()
        df['vol_sma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['vol_sma20']
        
        for i in range(20, len(df) - 10):
            row = df.iloc[i]
            signal = False
            
            if fix_type == 'rsi35':
                signal = row['rsi_14'] < 35
            elif fix_type == 'rsi30_below_sma':
                signal = row['rsi_14'] < 30 and row['close'] < row['sma20']
            elif fix_type == 'rsi35_vol':
                signal = row['rsi_14'] < 35 and row['vol_ratio'] > 1.5
            
            if signal and not pd.isna(row['close']):
                entry_price = row['close']
                exit_price = df.iloc[i + 10]['close']
                pnl = (exit_price - entry_price) / entry_price * 100 - 0.1
                trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})
    
    if len(trades) >= 10:
        result = calc_metrics(pd.DataFrame(trades))
        print(f"\n  {fix_name}:")
        print(f"    Trades: {len(trades)} | Test: {result['test']['wr']:.1f}% | Score: {result['score']}/5 → {result['status']}")
    else:
        print(f"\n  {fix_name}: {len(trades)} trades (insufficient)")

# ==================== FIX S001-09: HK Property ====================
print("\n" + "=" * 100)
print("FIXING S001-09: RSI MR HK Property")
print("=" * 100)

property_tickers = ['0001.HK', '0016.HK', '0017.HK']

fixes = [
    ('RSI < 35 + 5d hold', 'rsi35_5d'),
    ('RSI < 35 + 15d hold', 'rsi35_15d'),
    ('RSI < 40', 'rsi40'),
    ('RSI < 35 + Price < SMA50', 'rsi35_below_sma50'),
]

for fix_name, fix_type in fixes:
    trades = []
    hold_days = 10
    
    for ticker in property_tickers:
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        df['sma50'] = df['close'].rolling(50).mean()
        
        if '5d' in fix_type:
            hold_days = 5
        elif '15d' in fix_type:
            hold_days = 15
        
        rsi_threshold = 35
        if '40' in fix_type:
            rsi_threshold = 40
        
        for i in range(50, len(df) - hold_days):
            row = df.iloc[i]
            signal = False
            
            if 'below_sma50' in fix_type:
                signal = row['rsi_14'] < rsi_threshold and row['close'] < row['sma50']
            else:
                signal = row['rsi_14'] < rsi_threshold
            
            if signal and not pd.isna(row['close']):
                entry_price = row['close']
                exit_price = df.iloc[i + hold_days]['close']
                pnl = (exit_price - entry_price) / entry_price * 100 - 0.1
                trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})
    
    if len(trades) >= 10:
        result = calc_metrics(pd.DataFrame(trades), hold_days)
        print(f"\n  {fix_name}:")
        print(f"    Trades: {len(trades)} | Test: {result['test']['wr']:.1f}% | Score: {result['score']}/5 → {result['status']}")
    else:
        print(f"\n  {fix_name}: {len(trades)} trades (insufficient)")

# ==================== FIX S007-01: Sector Rotation ====================
print("\n" + "=" * 100)
print("FIXING S007-01: Sector Rotation XLK/XLF")
print("=" * 100)

# Try different approaches
fixes = [
    ('Ratio > SMA10', 10),
    ('Ratio > SMA5', 5),
    ('Ratio cross above SMA20', 20),
]

xlk = fetch_data('XLK')
xlf = fetch_data('XLF')

if xlk is not None and xlf is not None:
    df = xlk.join(xlf, how='inner', lsuffix='_xlk', rsuffix='_xlf')
    df['ratio'] = df['close_xlk'] / df['close_xlf']
    
    for fix_name, sma_period in fixes:
        trades = []
        df[f'ratio_sma{sma_period}'] = df['ratio'].rolling(sma_period).mean()
        
        for i in range(sma_period, len(df) - 10):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Different entry conditions
            if 'cross' in fix_name:
                signal = row['ratio'] > row[f'ratio_sma{sma_period}'] and prev_row['ratio'] <= prev_row[f'ratio_sma{sma_period}']
            else:
                signal = row['ratio'] > row[f'ratio_sma{sma_period}']
            
            if signal:
                entry_price = row['close_xlk']
                exit_price = df.iloc[i + 10]['close_xlk']
                pnl = (exit_price - entry_price) / entry_price * 100 - 0.1
                trades.append({'entry_date': df.index[i], 'pnl': pnl})
        
        if len(trades) >= 10:
            result = calc_metrics(pd.DataFrame(trades))
            print(f"\n  {fix_name}:")
            print(f"    Trades: {len(trades)} | Test: {result['test']['wr']:.1f}% | Score: {result['score']}/5 → {result['status']}")
        else:
            print(f"\n  {fix_name}: {len(trades)} trades (insufficient)")

conn.close()
print(f"\n{'='*100}")
