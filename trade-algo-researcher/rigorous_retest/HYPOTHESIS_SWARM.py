#!/usr/bin/env python3
"""
HYPOTHESIS SWARM — Test Many Combinations
Find what works across different indicators and thresholds
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

TEST_START, TEST_END = '2023-01-01', '2024-12-31'
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
    SELECT date, rsi_14, bb_upper, bb_lower, bb_middle, adx, macd_line, macd_signal, stoch_k, stoch_d FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def quick_test(tickers, entry_fn, hold_days=10, min_trades=20):
    """Quick test without full 3-tier, just test period"""
    trades = []
    
    for ticker in tickers:
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None:
            continue
        
        df = prices.join(ind, how='inner') if ind is not None else prices
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        if 'volume' in df.columns:
            df['vol_sma20'] = df['volume'].rolling(20).mean()
            df['vol_ratio'] = df['volume'] / df['vol_sma20']
        
        for i in range(50, len(df) - hold_days):
            try:
                if entry_fn(df, i):
                    entry_price = df.iloc[i]['close']
                    exit_price = df.iloc[i + hold_days]['close']
                    pnl = (exit_price - entry_price) / entry_price * 100 - 0.1
                    trades.append({'pnl': pnl, 'entry_date': df.index[i]})
            except:
                continue
    
    if len(trades) < min_trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    last_q_trades = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    if len(test_trades) < 10:
        return None
    
    wr = (test_trades['pnl'] > 0).sum() / len(test_trades) * 100
    last_q_pnl = last_q_trades['pnl'].sum() if len(last_q_trades) > 0 else 0
    
    return {
        'total_trades': len(trades),
        'test_wr': wr,
        'test_trades': len(test_trades),
        'last_q_pnl': last_q_pnl
    }

# Test tickers
tickers = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AMD', '0700.HK', '1398.HK', 'BTC-USD', 'COIN']

# Hypothesis swarm
hypotheses = []

# RSI variants
for rsi_val in [20, 25, 30, 35, 40]:
    for hold in [5, 10, 15]:
        hypotheses.append((f'RSI < {rsi_val}, {hold}d', lambda df, i, r=rsi_val: df.iloc[i]['rsi_14'] < r, hold))
        hypotheses.append((f'RSI < {rsi_val} + Price < SMA20, {hold}d', lambda df, i, r=rsi_val: df.iloc[i]['rsi_14'] < r and df.iloc[i]['close'] < df.iloc[i]['sma20'], hold))
        hypotheses.append((f'RSI < {rsi_val} + Price < SMA50, {hold}d', lambda df, i, r=rsi_val: df.iloc[i]['rsi_14'] < r and df.iloc[i]['close'] < df.iloc[i]['sma50'], hold))

# BB variants
for bb_width in [0.05, 0.06, 0.08, 0.10]:
    for hold in [5, 10]:
        hypotheses.append((f'BB width < {bb_width}, {hold}d', lambda df, i, w=bb_width: (df.iloc[i]['bb_upper'] - df.iloc[i]['bb_lower']) / df.iloc[i]['bb_middle'] < w, hold))

# Price vs SMA
for sma in [20, 50]:
    for hold in [10, 15]:
        hypotheses.append((f'Price > SMA{sma}, {hold}d', lambda df, i, s=sma: df.iloc[i]['close'] > df.iloc[i][f'sma{sma}'], hold))
        hypotheses.append((f'Price < SMA{sma}, {hold}d', lambda df, i, s=sma: df.iloc[i]['close'] < df.iloc[i][f'sma{sma}'], hold))

# Volume
for vol_mult in [1.5, 2.0, 2.5]:
    for hold in [3, 5]:
        hypotheses.append((f'Volume > {vol_mult}x, {hold}d', lambda df, i, v=vol_mult: 'vol_ratio' in df.columns and df.iloc[i]['vol_ratio'] > v, hold))

# ADX
for adx_val in [20, 25, 30]:
    for hold in [10, 15]:
        hypotheses.append((f'ADX > {adx_val}, {hold}d', lambda df, i, a=adx_val: df.iloc[i]['adx'] > a, hold))

print("=" * 90)
print("HYPOTHESIS SWARM — Testing", len(hypotheses), "combinations")
print("=" * 90)

results = []
for name, fn, hold in hypotheses:
    result = quick_test(tickers, fn, hold)
    if result and result['test_wr'] >= 55 and result['test_trades'] >= 20:
        results.append({
            'name': name,
            'wr': result['test_wr'],
            'trades': result['test_trades'],
            'last_q': result['last_q_pnl']
        })
        print(f"  ⭐ {name}: {result['test_wr']:.1f}% ({result['test_trades']}t), LastQ: {result['last_q_pnl']:.1f}%")

# Sort by win rate
results.sort(key=lambda x: x['wr'], reverse=True)

print(f"\n{'='*90}")
print(f"TOP {min(15, len(results))} RESULTS (sorted by win rate):")
print(f"{'='*90}")

for i, r in enumerate(results[:15], 1):
    print(f"{i:2d}. {r['name']:50s} | WR: {r['wr']:5.1f}% | Trades: {r['trades']:3d} | LastQ: {r['last_q']:+6.1f}%")

conn.close()
print(f"\n{'='*90}")
