#!/usr/bin/env python3
"""
TEST S007-01: Sector Rotation XLK/XLF
Special handling for ratio-based strategy
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

# Fetch XLK and XLF
def fetch_data(ticker):
    query = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.rename(columns={'close': ticker}, inplace=True)
    return df

print("Testing S007-01: Sector Rotation XLK/XLF...")

xlk = fetch_data('XLK')
xlf = fetch_data('XLF')

# Merge and calculate ratio
df = xlk.join(xlf, how='inner')
df['ratio'] = df['XLK'] / df['XLF']
df['ratio_sma20'] = df['ratio'].rolling(20).mean()

# Generate signals
HOLD_DAYS = 10
COST = 0.001

trades = []
in_position = False
entry_idx = None

for i in range(20, len(df) - HOLD_DAYS):
    row = df.iloc[i]
    
    # Entry: ratio > ratio_sma20
    if not in_position and row['ratio'] > row['ratio_sma20']:
        in_position = True
        entry_idx = i
    elif in_position:
        days_held = i - entry_idx
        if days_held >= HOLD_DAYS:
            entry_price = df.iloc[entry_idx]['XLK']
            exit_price = row['XLK']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            trades.append({
                'entry_date': df.index[entry_idx],
                'exit_date': df.index[i],
                'pnl': pnl
            })
            in_position = False
            entry_idx = None

print(f"Total trades: {len(trades)}")

if len(trades) >= 10:
    trades_df = pd.DataFrame(trades)
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
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=HOLD_DAYS) if len(test) >= 10 else {'mc_robustness_score': 0}
    decay = abs(train_m['wr'] - test_m['wr'])
    
    print(f"\n  Train: {train_m['wr']:.1f}% ({train_m['trades']}t)")
    print(f"  Test:  {test_m['wr']:.1f}% ({test_m['trades']}t)")
    print(f"  Val:   {validate_m['wr']:.1f}% ({validate_m['trades']}t)")
    print(f"  LastQ: {last_q_m['pnl']:.1f}% ({last_q_m['trades']}t)")
    print(f"  Decay: {decay:.1f}% | MC: {mc['mc_robustness_score']:.1f}%")
    
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
    
    print(f"  Score: {score}/5 → {status}")
else:
    print("❌ Insufficient trades")

conn.close()
