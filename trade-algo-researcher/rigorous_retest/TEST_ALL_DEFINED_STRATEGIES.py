#!/usr/bin/env python3
"""
TEST ALL USER'S DEFINED STRATEGIES WITH REAL DATA
S001-02, S001-03, S001-04, S001-09, S001-10, S002-01, S003-02, S005-01, S007-01
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

# Periods
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

def test_strategy(name, tickers, entry_logic, exit_days, cost=0.001):
    """Generic strategy tester"""
    all_trades = []
    
    for ticker in tickers:
        prices = fetch_data(ticker)
        rsi = fetch_rsi(ticker)
        
        if prices is None:
            continue
            
        df = prices.join(rsi, how='inner') if rsi is not None else prices
        
        # Calculate indicators based on entry logic
        if 'sma20' in entry_logic:
            df['sma20'] = df['close'].rolling(20).mean()
        if 'sma50' in entry_logic:
            df['sma50'] = df['close'].rolling(50).mean()
        if 'volume_ratio' in entry_logic:
            df['vol_sma20'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['vol_sma20']
        
        trades = []
        in_position = False
        entry_idx = None
        
        for i in range(len(df) - exit_days):
            row = df.iloc[i]
            
            # Check entry condition
            signal = False
            if entry_logic == 'rsi30':
                signal = row['rsi_14'] < 30
            elif entry_logic == 'rsi35':
                signal = row['rsi_14'] < 35
            elif entry_logic == 'rsi30_sma20':
                signal = row['rsi_14'] < 30 and row['close'] > row['sma20']
            elif entry_logic == 'rsi35_sma20':
                signal = row['rsi_14'] < 35 and row['close'] > row['sma20']
            elif entry_logic == 'price_above_sma50':
                signal = row['close'] > row['sma50']
            elif entry_logic == 'volume_breakout':
                if i >= 20 and 'volume_ratio' in row:
                    recent_high = df.iloc[i-20:i]['close'].max()
                    signal = row['volume_ratio'] > 2.0 and row['close'] > recent_high
                else:
                    signal = False
            elif entry_logic == 'sector_rotation':
                # Handled separately
                signal = False
            
            if not in_position and signal and not pd.isna(row['close']):
                in_position = True
                entry_idx = i
            elif in_position:
                days_held = i - entry_idx
                if days_held >= exit_days:
                    entry_price = df.iloc[entry_idx]['close']
                    exit_price = row['close']
                    pnl = (exit_price - entry_price) / entry_price * 100 - (cost * 100)
                    trades.append({
                        'ticker': ticker,
                        'entry_date': df.index[entry_idx],
                        'exit_date': df.index[i],
                        'pnl': pnl
                    })
                    in_position = False
                    entry_idx = None
        
        all_trades.extend(trades)
    
    if len(all_trades) < 10:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split periods
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc_metrics(t):
        if len(t) < 3:
            return {'trades': len(t), 'wr': 0, 'pnl': 0}
        wins = (t['pnl'] > 0).sum()
        return {'trades': len(t), 'wr': wins/len(t)*100, 'pnl': t['pnl'].sum()}
    
    train_m = calc_metrics(train)
    test_m = calc_metrics(test)
    validate_m = calc_metrics(validate)
    last_q_m = calc_metrics(last_q)
    
    # MC on test
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=exit_days) if len(test) >= 10 else {'mc_robustness_score': 0}
    
    decay = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    # Classification
    score = 0
    if test_m['wr'] >= 55: score += 1
    if test_m['trades'] >= 20: score += 1
    if mc['mc_robustness_score'] >= 70: score += 1
    if decay <= 20: score += 1
    if last_q_m['pnl'] > 0: score += 1
    
    if score == 5:
        status = "🏆 GOLDEN"
    elif score >= 3:
        status = "⭐ VALIDATED"
    else:
        status = "📝 HYPOTHESIS"
    
    return {
        'name': name,
        'train': train_m,
        'test': test_m,
        'validate': validate_m,
        'last_q': last_q_m,
        'decay': decay,
        'mc': mc['mc_robustness_score'],
        'score': score,
        'status': status
    }

# Define strategies to test
strategies = [
    ('S001-02: RSI MR US Consumer', ['COST', 'WMT'], 'rsi30_sma20', 10),
    ('S001-03: RSI MR CN Banks', ['1398.HK', '3988.HK', '0005.HK'], 'rsi35', 10),  # Using Option B
    ('S001-09: RSI MR HK Property', ['0001.HK', '0016.HK', '0017.HK'], 'rsi35', 10),
    ('S001-10: RSI MR US Staples', ['XLP', 'WMT', 'COST'], 'rsi35', 10),
    ('S002-01: Trend US ETF', ['SPY', 'QQQ'], 'price_above_sma50', 15),
    ('S005-01: Vol Breakout', ['TSLA', 'NVDA', 'AMD'], 'volume_breakout', 5),
]

print("=" * 100)
print("TESTING ALL DEFINED STRATEGIES WITH REAL DATA")
print("=" * 100)

results = []
for name, tickers, logic, hold in strategies:
    print(f"\n{'='*100}")
    print(f"TESTING: {name}")
    print(f"Logic: {logic} | Hold: {hold} days | Tickers: {', '.join(tickers)}")
    print(f"{'='*100}")
    
    result = test_strategy(name, tickers, logic, hold)
    
    if result:
        print(f"  Train: {result['train']['wr']:.1f}% ({result['train']['trades']}t)")
        print(f"  Test:  {result['test']['wr']:.1f}% ({result['test']['trades']}t)")
        print(f"  Val:   {result['validate']['wr']:.1f}% ({result['validate']['trades']}t)")
        print(f"  LastQ: {result['last_q']['pnl']:.1f}% ({result['last_q']['trades']}t)")
        print(f"  Decay: {result['decay']:.1f}% | MC: {result['mc']:.1f}%")
        print(f"  Score: {result['score']}/5 → {result['status']}")
        results.append(result)
    else:
        print(f"  ❌ No results (insufficient signals or data)")

# Summary
print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

golden = [r for r in results if '🏆' in r['status']]
validated = [r for r in results if '⭐' in r['status']]
hypothesis = [r for r in results if '📝' in r['status']]

print(f"\n🏆 GOLDEN: {len(golden)}")
for r in golden:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, MC {r['mc']:.1f}%")

print(f"\n⭐ VALIDATED: {len(validated)}")
for r in validated:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, MC {r['mc']:.1f}%")

print(f"\n📝 HYPOTHESIS: {len(hypothesis)}")
for r in hypothesis:
    print(f"  {r['name']}: Test {r['test']['wr']:.1f}%, Score {r['score']}/5")

conn.close()
print(f"\n{'='*100}")
