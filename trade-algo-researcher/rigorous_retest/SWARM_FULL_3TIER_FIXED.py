#!/usr/bin/env python3
"""
FULL 3-TIER VALIDATION — TOP SWARM DISCOVERIES
Fixed: No overlapping trades, proper position sizing, realistic P&L
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

POSITION_SIZE = 10000  # Fixed position size per trade

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

def fetch_indicators(ticker):
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

def full_3tier_test(name, tickers, entry_fn, hold_days, cost_pct=0.001):
    """
    Proper backtest with:
    - No overlapping trades per ticker
    - Fixed position sizing
    - Proper P&L calculation
    """
    all_trades = []
    
    for ticker in tickers:
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        # Track positions per ticker
        in_position = False
        exit_date = None
        
        for i in range(50, len(df) - hold_days):
            current_date = df.index[i]
            
            # Check if we should exit current position
            if in_position and current_date >= exit_date:
                in_position = False
            
            # Check entry (only if not already in position)
            if not in_position:
                try:
                    if entry_fn(df, i):
                        entry_price = df.iloc[i]['close']
                        exit_idx = i + hold_days
                        exit_price = df.iloc[exit_idx]['close']
                        exit_date = df.index[exit_idx]
                        
                        # Calculate P&L with fixed position size
                        shares = POSITION_SIZE / entry_price
                        gross_pnl = (exit_price - entry_price) * shares
                        cost = POSITION_SIZE * cost_pct * 2  # Entry + exit
                        net_pnl = gross_pnl - cost
                        pnl_pct = (net_pnl / POSITION_SIZE) * 100
                        
                        all_trades.append({
                            'ticker': ticker,
                            'entry_date': current_date,
                            'exit_date': exit_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl': pnl_pct,  # Use 'pnl' for MC function
                            'net_pnl': net_pnl
                        })
                        
                        in_position = True
                except:
                    continue
    
    if len(all_trades) < 20:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split by period
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc_metrics(t):
        if len(t) < 3:
            return {'trades': len(t), 'wr': 0, 'total_pnl': 0, 'avg_pnl': 0}
        wins = (t['pnl'] > 0).sum()
        return {
            'trades': len(t),
            'wr': wins / len(t) * 100,
            'total_pnl': t['net_pnl'].sum(),
            'avg_pnl': t['net_pnl'].mean()
        }
    
    train_m = calc_metrics(train)
    test_m = calc_metrics(test)
    validate_m = calc_metrics(validate)
    last_q_m = calc_metrics(last_q)
    
    # MC on test
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=hold_days) if len(test) >= 10 else {'mc_robustness_score': 0}
    
    decay = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    score = sum([
        test_m['wr'] >= 55,
        test_m['trades'] >= 20,
        mc['mc_robustness_score'] >= 70,
        decay <= 20,
        last_q_m['total_pnl'] > 0
    ])
    
    status = "🏆 GOLDEN" if score == 5 else "⭐ VALIDATED" if score >= 3 else "📝 HYPOTHESIS"
    
    return {
        'name': name,
        'train': train_m,
        'test': test_m,
        'validate': validate_m,
        'last_q': last_q_m,
        'decay': decay,
        'mc_robust': mc['mc_robustness_score'],
        'score': score,
        'status': status,
        'trades_df': trades_df
    }

# Test tickers
tickers = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AMD', '0700.HK', '1398.HK', 'BTC-USD', 'COIN']

# Top swarm discoveries to validate
tests = [
    ('RSI < 25, 15d', lambda df, i: df.iloc[i]['rsi_14'] < 25, 15),
    ('RSI < 30 + Price < SMA50, 10d', lambda df, i: df.iloc[i]['rsi_14'] < 30 and df.iloc[i]['close'] < df.iloc[i]['sma50'], 10),
    ('RSI < 30 + Price < SMA50, 15d', lambda df, i: df.iloc[i]['rsi_14'] < 30 and df.iloc[i]['close'] < df.iloc[i]['sma50'], 15),
    ('RSI < 25 + Price < SMA50, 10d', lambda df, i: df.iloc[i]['rsi_14'] < 25 and df.iloc[i]['close'] < df.iloc[i]['sma50'], 10),
]

print("=" * 100)
print("FULL 3-TIER VALIDATION — FIXED POSITION SIZING, NO OVERLAPPING TRADES")
print(f"Position Size: ${POSITION_SIZE:,} per trade")
print("=" * 100)

results = []
for name, fn, hold in tests:
    print(f"\n{'='*100}")
    print(f"Testing: {name}")
    print(f"{'='*100}")
    
    result = full_3tier_test(name, tickers, fn, hold)
    
    if result:
        print(f"  Train: {result['train']['wr']:.1f}% ({result['train']['trades']}t) | P&L: ${result['train']['total_pnl']:,.0f}")
        print(f"  Test:  {result['test']['wr']:.1f}% ({result['test']['trades']}t) | P&L: ${result['test']['total_pnl']:,.0f}")
        print(f"  Val:   {result['validate']['wr']:.1f}% ({result['validate']['trades']}t) | P&L: ${result['validate']['total_pnl']:,.0f}")
        print(f"  LastQ: {result['last_q']['wr']:.1f}% ({result['last_q']['trades']}t) | P&L: ${result['last_q']['total_pnl']:,.0f}")
        print(f"  Decay: {result['decay']:.1f}% | MC: {result['mc_robust']:.1f}%")
        print(f"  Score: {result['score']}/5 → {result['status']}")
        results.append(result)
    else:
        print(f"  ❌ Insufficient trades")

# Summary
print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

golden = [r for r in results if '🏆' in r['status']]
validated = [r for r in results if '⭐' in r['status']]
hypothesis = [r for r in results if '📝' in r['status']]

print(f"\n🏆 GOLDEN: {len(golden)}")
for r in golden:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, Decay {r['decay']:.1f}%, LastQ ${r['last_q']['total_pnl']:,.0f}")

print(f"\n⭐ VALIDATED: {len(validated)}")
for r in validated:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, Decay {r['decay']:.1f}%, LastQ ${r['last_q']['total_pnl']:,.0f}")

print(f"\n📝 HYPOTHESIS: {len(hypothesis)}")
for r in hypothesis:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, Score {r['score']}/5")

conn.close()
print(f"\n{'='*100}")
