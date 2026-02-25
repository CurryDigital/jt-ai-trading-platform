#!/usr/bin/env python3
"""
EXPLORE OPTION A vs B: S001-01 Universe (HK Banks)
Option A: RSI < 30 (no SMA filter)
Option B: RSI < 35 (no SMA filter)
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

# S001-01 Universe
TICKERS = ['0005.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK']

# Periods
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'
VALIDATE_START = '2025-01-01'
LAST_Q_START = '2024-10-01'

def fetch_data(ticker):
    query = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_rsi(ticker):
    query = f"""
    SELECT date, rsi_14 FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_option(ticker, rsi_threshold, option_name):
    """Test a specific RSI threshold"""
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    
    if prices is None or rsi is None:
        return None
    
    df = prices.join(rsi, how='inner')
    
    HOLD_DAYS = 10
    COST = 0.001
    
    trades = []
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if row['rsi_14'] < rsi_threshold and not pd.isna(row['close']):
            entry_price = row['close']
            exit_price = df.iloc[i + HOLD_DAYS]['close']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            
            trades.append({
                'entry_date': df.index[i],
                'pnl': pnl
            })
    
    if len(trades) < 10:
        return None
    
    trades_df = pd.DataFrame(trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split periods
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc_metrics(t):
        if len(t) < 3:
            return {'trades': len(t), 'wr': 0, 'total_pnl': 0}
        wins = (t['pnl'] > 0).sum()
        return {
            'trades': len(t),
            'wr': wins / len(t) * 100,
            'total_pnl': t['pnl'].sum()
        }
    
    train_m = calc_metrics(train)
    test_m = calc_metrics(test)
    validate_m = calc_metrics(validate)
    last_q_m = calc_metrics(last_q)
    
    # MC on test
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=HOLD_DAYS) if len(test) >= 10 else {'mc_robustness_score': 0}
    
    decay_tt = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    return {
        'option': option_name,
        'ticker': ticker,
        'train': train_m,
        'test': test_m,
        'validate': validate_m,
        'last_q': last_q_m,
        'mc_robust': mc['mc_robustness_score'],
        'max_decay': decay_tt,
        'all_trades': trades_df
    }

def classify(result):
    """Classify based on strict criteria"""
    score = 0
    checks = {
        'test_wr_55': result['test']['wr'] >= 55,
        'test_trades_20': result['test']['trades'] >= 20,
        'mc_70': result['mc_robust'] >= 70,
        'decay_20': result['max_decay'] <= 20,
        'last_q_pos': result['last_q']['total_pnl'] > 0,
    }
    for check, passed in checks.items():
        if passed:
            score += 1
    
    if score == 5:
        return 'GOLDEN', score
    elif score >= 3:
        return 'VALIDATED', score
    else:
        return 'HYPOTHESIS', score

print("=" * 110)
print("OPTION A vs B: S001-01 Universe (HK Banks)")
print("=" * 110)

all_results = {'A': [], 'B': []}

for ticker in TICKERS:
    print(f"\n{'='*110}")
    print(f"TICKER: {ticker}")
    print(f"{'='*110}")
    
    # Option A: RSI < 30
    result_a = test_option(ticker, 30, 'A')
    if result_a:
        status_a, score_a = classify(result_a)
        print(f"\n  Option A (RSI < 30):")
        print(f"    Train: {result_a['train']['wr']:.1f}% ({result_a['train']['trades']}t)")
        print(f"    Test:  {result_a['test']['wr']:.1f}% ({result_a['test']['trades']}t)")
        print(f"    Val:   {result_a['validate']['wr']:.1f}% ({result_a['validate']['trades']}t)")
        print(f"    LastQ: {result_a['last_q']['total_pnl']:.1f}% ({result_a['last_q']['trades']}t)")
        print(f"    Decay: {result_a['max_decay']:.1f}% | MC: {result_a['mc_robust']:.1f}%")
        print(f"    Score: {score_a}/5 → {status_a}")
        all_results['A'].append(result_a)
    else:
        print(f"  Option A: ❌ Insufficient signals")
    
    # Option B: RSI < 35
    result_b = test_option(ticker, 35, 'B')
    if result_b:
        status_b, score_b = classify(result_b)
        print(f"\n  Option B (RSI < 35):")
        print(f"    Train: {result_b['train']['wr']:.1f}% ({result_b['train']['trades']}t)")
        print(f"    Test:  {result_b['test']['wr']:.1f}% ({result_b['test']['trades']}t)")
        print(f"    Val:   {result_b['validate']['wr']:.1f}% ({result_b['validate']['trades']}t)")
        print(f"    LastQ: {result_b['last_q']['total_pnl']:.1f}% ({result_b['last_q']['trades']}t)")
        print(f"    Decay: {result_b['max_decay']:.1f}% | MC: {result_b['mc_robust']:.1f}%")
        print(f"    Score: {score_b}/5 → {status_b}")
        all_results['B'].append(result_b)
    else:
        print(f"  Option B: ❌ Insufficient signals")

# Aggregate
print(f"\n{'='*110}")
print("STRATEGY-LEVEL AGGREGATION")
print(f"{'='*110}")

for option in ['A', 'B']:
    if all_results[option]:
        all_train = pd.concat([r['all_trades'][(r['all_trades']['entry_date'] >= TRAIN_START) & 
                                               (r['all_trades']['entry_date'] <= TRAIN_END)] for r in all_results[option]])
        all_test = pd.concat([r['all_trades'][(r['all_trades']['entry_date'] >= TEST_START) & 
                                              (r['all_trades']['entry_date'] <= TEST_END)] for r in all_results[option]])
        all_val = pd.concat([r['all_trades'][r['all_trades']['entry_date'] >= VALIDATE_START] for r in all_results[option]])
        all_last_q = pd.concat([r['all_trades'][r['all_trades']['entry_date'] >= LAST_Q_START] for r in all_results[option]])
        
        def agg(t):
            if len(t) == 0:
                return {'trades': 0, 'wr': 0, 'pnl': 0}
            return {'trades': len(t), 'wr': (t['pnl'] > 0).sum() / len(t) * 100, 'pnl': t['pnl'].sum()}
        
        train_agg = agg(all_train)
        test_agg = agg(all_test)
        val_agg = agg(all_val)
        last_q_agg = agg(all_last_q)
        
        threshold = 30 if option == 'A' else 35
        print(f"\n  Option {option} (RSI < {threshold}) — AGGREGATE:")
        print(f"    Train: {train_agg['wr']:.1f}% ({train_agg['trades']}t)")
        print(f"    Test:  {test_agg['wr']:.1f}% ({test_agg['trades']}t)")
        print(f"    Val:   {val_agg['wr']:.1f}% ({val_agg['trades']}t)")
        print(f"    LastQ: {last_q_agg['pnl']:.1f}% ({last_q_agg['trades']}t)")
        
        # Classify aggregate
        analytics = BacktestAnalytics()
        mc = analytics.monte_carlo_simulation(all_test, n_simulations=1000, hold_days=10) if len(all_test) >= 10 else {'mc_robustness_score': 0}
        decay = abs(train_agg['wr'] - test_agg['wr'])
        
        score = 0
        if test_agg['wr'] >= 55: score += 1
        if test_agg['trades'] >= 20: score += 1
        if mc['mc_robustness_score'] >= 70: score += 1
        if decay <= 20: score += 1
        if last_q_agg['pnl'] > 0: score += 1
        
        if score == 5:
            status = "🏆 GOLDEN"
        elif score >= 3:
            status = "⭐ VALIDATED"
        else:
            status = "📝 MOVE TO HYPOTHESIS BUCKET"
        
        print(f"    Decay: {decay:.1f}% | MC: {mc['mc_robustness_score']:.1f}% | Score: {score}/5")
        print(f"    STATUS: {status}")

conn.close()
print(f"\n{'='*110}")
