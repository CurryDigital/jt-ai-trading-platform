#!/usr/bin/env python3
"""
TEST HYPOTHESES WITH REAL DATA
Testable hypotheses only (those with available data)
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
    SELECT date, rsi_14, bb_upper, bb_middle, bb_lower, adx FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def classify(score):
    if score == 5:
        return "🏆 GOLDEN"
    elif score >= 3:
        return "⭐ VALIDATED"
    else:
        return "📝 HYPOTHESIS"

def calc_metrics(trades_df):
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
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=10) if len(test) >= 10 else {'mc_robustness_score': 0}
    decay = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    score = 0
    if test_m['wr'] >= 55: score += 1
    if test_m['trades'] >= 20: score += 1
    if mc['mc_robustness_score'] >= 70: score += 1
    if decay <= 20: score += 1
    if last_q_m['pnl'] > 0: score += 1
    
    return {
        'train': train_m, 'test': test_m, 'validate': validate_m, 'last_q': last_q_m,
        'decay': decay, 'mc': mc['mc_robustness_score'], 'score': score,
        'status': classify(score)
    }

# ==================== H1: BOLLINGER SQUEEZE BREAKOUT ====================
print("=" * 100)
print("H1: BOLLINGER SQUEEZE + BREAKOUT")
print("=" * 100)

bb_tickers = ['TSLA', 'NVDA', 'AMD', 'BTC-USD', 'SOL-USD']
bb_trades = []

for ticker in bb_tickers:
    prices = fetch_data(ticker)
    ind = fetch_indicators(ticker)
    
    if prices is None or ind is None:
        continue
    
    df = prices.join(ind, how='inner')
    df['bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_sma20']
    
    HOLD_DAYS = 10
    COST = 0.001
    
    for i in range(30, len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        # Squeeze: bandwidth < 0.06 for 10+ days
        squeeze_period = df.iloc[i-10:i]['bandwidth'] < 0.06
        squeeze = squeeze_period.all() if len(squeeze_period) > 0 else False
        
        # Breakout above upper band with volume
        if squeeze and row['close'] > row['bb_upper'] and row['vol_ratio'] > 1.5:
            entry_price = row['close']
            exit_price = df.iloc[i + HOLD_DAYS]['close']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            bb_trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})

if len(bb_trades) >= 10:
    bb_df = pd.DataFrame(bb_trades)
    bb_result = calc_metrics(bb_df)
    print(f"\nTrades: {len(bb_trades)}")
    print(f"Train: {bb_result['train']['wr']:.1f}% ({bb_result['train']['trades']}t)")
    print(f"Test:  {bb_result['test']['wr']:.1f}% ({bb_result['test']['trades']}t)")
    print(f"LastQ: {bb_result['last_q']['pnl']:.1f}% | Decay: {bb_result['decay']:.1f}%")
    print(f"MC: {bb_result['mc']:.1f}% | Score: {bb_result['score']}/5 → {bb_result['status']}")
else:
    print(f"\nInsufficient signals: {len(bb_trades)}")

# ==================== H2: ADX TREND FOLLOWING ====================
print("\n" + "=" * 100)
print("H2: ADX TREND STRENGTH (ADX > 25)")
print("=" * 100)

adx_tickers = ['SPY', 'QQQ', 'TSLA', 'NVDA', '0700.HK']
adx_trades = []

for ticker in adx_tickers:
    prices = fetch_data(ticker)
    ind = fetch_indicators(ticker)
    
    if prices is None or ind is None:
        continue
    
    df = prices.join(ind, how='inner')
    df['sma50'] = df['close'].rolling(50).mean()
    
    HOLD_DAYS = 15
    COST = 0.001
    
    for i in range(50, len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        # ADX > 25 (trend) + Price > SMA50
        if row['adx'] > 25 and row['close'] > row['sma50']:
            entry_price = row['close']
            exit_price = df.iloc[i + HOLD_DAYS]['close']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            adx_trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})

if len(adx_trades) >= 10:
    adx_df = pd.DataFrame(adx_trades)
    adx_result = calc_metrics(adx_df)
    print(f"\nTrades: {len(adx_trades)}")
    print(f"Train: {adx_result['train']['wr']:.1f}% ({adx_result['train']['trades']}t)")
    print(f"Test:  {adx_result['test']['wr']:.1f}% ({adx_result['test']['trades']}t)")
    print(f"LastQ: {adx_result['last_q']['pnl']:.1f}% | Decay: {adx_result['decay']:.1f}%")
    print(f"MC: {adx_result['mc']:.1f}% | Score: {adx_result['score']}/5 → {adx_result['status']}")
else:
    print(f"\nInsufficient signals: {len(adx_trades)}")

# ==================== H3: VOLUME BREAKOUT ====================
print("\n" + "=" * 100)
print("H3: VOLUME BREAKOUT (>2x avg + new 20d high)")
print("=" * 100)

vol_tickers = ['TSLA', 'NVDA', 'AMD', 'COIN', 'MSTR']
vol_trades = []

for ticker in vol_tickers:
    prices = fetch_data(ticker)
    if prices is None:
        continue
    
    df = prices.copy()
    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_sma20']
    df['high_20'] = df['close'].rolling(20).max().shift(1)
    
    HOLD_DAYS = 5
    COST = 0.001
    
    for i in range(20, len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        # Volume > 2x + new 20d high
        if row['vol_ratio'] > 2.0 and row['close'] > row['high_20']:
            entry_price = row['close']
            exit_price = df.iloc[i + HOLD_DAYS]['close']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            vol_trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})

if len(vol_trades) >= 10:
    vol_df = pd.DataFrame(vol_trades)
    vol_result = calc_metrics(vol_df)
    print(f"\nTrades: {len(vol_trades)}")
    print(f"Train: {vol_result['train']['wr']:.1f}% ({vol_result['train']['trades']}t)")
    print(f"Test:  {vol_result['test']['wr']:.1f}% ({vol_result['test']['trades']}t)")
    print(f"LastQ: {vol_result['last_q']['pnl']:.1f}% | Decay: {vol_result['decay']:.1f}%")
    print(f"MC: {vol_result['mc']:.1f}% | Score: {vol_result['score']}/5 → {vol_result['status']}")
else:
    print(f"\nInsufficient signals: {len(vol_trades)}")

# ==================== H4: RSI EXTREME (<20) ====================
print("\n" + "=" * 100)
print("H4: RSI EXTREME MEAN REVERSION (RSI < 20)")
print("=" * 100)

ext_tickers = ['TSLA', 'NVDA', 'AMD', 'COIN', 'BTC-USD', '0700.HK']
ext_trades = []

for ticker in ext_tickers:
    prices = fetch_data(ticker)
    ind = fetch_indicators(ticker)
    
    if prices is None or ind is None:
        continue
    
    df = prices.join(ind, how='inner')
    
    HOLD_DAYS = 5  # Shorter hold for extreme reversions
    COST = 0.001
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        # RSI < 20 (extreme oversold)
        if row['rsi_14'] < 20:
            entry_price = row['close']
            exit_price = df.iloc[i + HOLD_DAYS]['close']
            pnl = (exit_price - entry_price) / entry_price * 100 - (COST * 100)
            ext_trades.append({'ticker': ticker, 'entry_date': df.index[i], 'pnl': pnl})

if len(ext_trades) >= 10:
    ext_df = pd.DataFrame(ext_trades)
    ext_result = calc_metrics(ext_df)
    print(f"\nTrades: {len(ext_trades)}")
    print(f"Train: {ext_result['train']['wr']:.1f}% ({ext_result['train']['trades']}t)")
    print(f"Test:  {ext_result['test']['wr']:.1f}% ({ext_result['test']['trades']}t)")
    print(f"LastQ: {ext_result['last_q']['pnl']:.1f}% | Decay: {ext_result['decay']:.1f}%")
    print(f"MC: {ext_result['mc']:.1f}% | Score: {ext_result['score']}/5 → {ext_result['status']}")
else:
    print(f"\nInsufficient signals: {len(ext_trades)}")

conn.close()
print(f"\n{'='*100}")
