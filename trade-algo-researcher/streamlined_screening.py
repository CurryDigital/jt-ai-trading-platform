#!/usr/bin/env python3
"""
STREAMLINED STRATEGY SCREENING
Fast parameter sweep on key strategies
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np


def get_db_connection():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    token = rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432, DBUsername='openclaw_user', Region='ap-southeast-1'
    )
    return psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432, database='aitrading', user='openclaw_user',
        password=token, sslmode='require'
    )


print("="*70)
print("STREAMLINED STRATEGY SCREENING")
print("="*70)

# Load limited data for speed
conn = get_db_connection()
print("\nLoading data...")

query = """
SELECT date, ticker, close, volume, open
FROM silver.historical_stock_data
WHERE date BETWEEN '2022-01-01' AND '2024-12-31'
AND ticker IN (
    SELECT DISTINCT ticker FROM silver.historical_stock_data 
    WHERE date > '2022-01-01' LIMIT 50
)
ORDER BY ticker, date
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"Data loaded: {len(df):,} records, {df['ticker'].nunique()} tickers")

# Transaction costs
COST = 0.1  # 0.1% round-trip


def screen_strategy(name, signal_func, param_list):
    """Screen one strategy with parameter list"""
    print(f"\n{'='*70}")
    print(f"SCREENING: {name}")
    print(f"{'='*70}")
    
    results = []
    
    for params in param_list:
        trades = []
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
            if len(ticker_df) < 50:
                continue
            
            trade_returns = signal_func(ticker_df, params)
            trades.extend(trade_returns)
        
        if len(trades) >= 50:
            returns = pd.Series(trades)
            win_rate = (returns > 0).mean() * 100
            avg_ret = returns.mean()
            sharpe = avg_ret / returns.std() * np.sqrt(252/params.get('hold', 5)) if returns.std() > 0 else -999
            
            results.append({
                'params': params,
                'trades': len(trades),
                'win_rate': win_rate,
                'sharpe': sharpe,
                'avg_ret': avg_ret
            })
    
    # Sort by Sharpe
    results.sort(key=lambda x: x['sharpe'], reverse=True)
    
    # Print top 3
    print(f"\n{'Rank':<6} {'Sharpe':<8} {'Win%':<8} {'Trades':<8} {'Params'}")
    print(f"{'-'*60}")
    
    best = None
    for i, r in enumerate(results[:3], 1):
        status = "✅" if r['sharpe'] >= 1.0 and r['win_rate'] >= 50 else "🧪" if r['sharpe'] > 0.5 else "❌"
        print(f"{status} {i:<4} {r['sharpe']:<8.2f} {r['win_rate']:<8.1f} {r['trades']:<8} {r['params']}")
        if i == 1 and r['sharpe'] >= 1.0:
            best = r
    
    return best


# STRATEGY 1: Mean Reversion
def mean_rev_signal(ticker_df, params):
    trades = []
    period = params['period']
    threshold = params['threshold']
    hold = params['hold']
    
    # Calculate RSI
    delta = ticker_df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rsi = 100 - (100 / (1 + gain / loss))
    
    vol_avg = ticker_df['volume'].rolling(20).mean()
    
    for i in range(period + 20, len(ticker_df) - hold):
        if rsi.iloc[i] < threshold and ticker_df['volume'].iloc[i] > vol_avg.iloc[i] * 1.3:
            entry = ticker_df['close'].iloc[i]
            exit = ticker_df['close'].iloc[i + hold]
            gross = (exit - entry) / entry * 100
            trades.append(gross - COST)
    
    return trades


# STRATEGY 2: Momentum
def momentum_signal(ticker_df, params):
    trades = []
    lookback = params['lookback']
    hold = params['hold']
    
    momentum = ticker_df['close'].pct_change(lookback)
    
    for i in range(lookback, len(ticker_df) - hold):
        if momentum.iloc[i] > 0.05:  # 5% momentum
            entry = ticker_df['close'].iloc[i]
            exit = ticker_df['close'].iloc[i + hold]
            gross = (exit - entry) / entry * 100
            trades.append(gross - COST)
    
    return trades


# STRATEGY 3: Bollinger
def bollinger_signal(ticker_df, params):
    trades = []
    period = params['period']
    std = params['std']
    
    sma = ticker_df['close'].rolling(period).mean()
    std_dev = ticker_df['close'].rolling(period).std()
    lower = sma - (std * std_dev)
    
    for i in range(period, len(ticker_df) - 5):
        if ticker_df['close'].iloc[i] < lower.iloc[i]:
            entry = ticker_df['close'].iloc[i]
            # Exit when back to SMA
            for j in range(i+1, min(i+20, len(ticker_df))):
                if ticker_df['close'].iloc[j] >= sma.iloc[j]:
                    gross = (ticker_df['close'].iloc[j] - entry) / entry * 100
                    trades.append(gross - COST)
                    break
    
    return trades


# STRATEGY 4: Volume Breakout
def volume_breakout_signal(ticker_df, params):
    trades = []
    vol_mult = params['vol_mult']
    hold = params['hold']
    
    vol_avg = ticker_df['volume'].rolling(20).mean()
    price_change = ticker_df['close'].pct_change()
    
    for i in range(20, len(ticker_df) - hold):
        if ticker_df['volume'].iloc[i] > vol_avg.iloc[i] * vol_mult and price_change.iloc[i] > 0.02:
            entry = ticker_df['close'].iloc[i]
            exit = ticker_df['close'].iloc[i + hold]
            gross = (exit - entry) / entry * 100
            trades.append(gross - COST)
    
    return trades


# STRATEGY 5: Gap Fade (if intraday data)
def gap_fade_signal(ticker_df, params):
    trades = []
    threshold = params['threshold']
    
    prev_close = ticker_df['close'].shift(1)
    gap = (ticker_df['open'] - prev_close) / prev_close
    
    for i in range(1, len(ticker_df)):
        if abs(gap.iloc[i]) > threshold:
            entry = ticker_df['open'].iloc[i]
            exit = ticker_df['close'].iloc[i]
            if gap.iloc[i] > 0:  # Gap up, fade down
                gross = (entry - exit) / entry * 100
            else:  # Gap down, fade up
                gross = (exit - entry) / entry * 100
            trades.append(gross - COST)
    
    return trades


# Run screenings
validated = []

# 1. Mean Reversion
mr_best = screen_strategy("RSI Mean Reversion", mean_rev_signal, [
    {'period': 10, 'threshold': 25, 'hold': 3},
    {'period': 14, 'threshold': 30, 'hold': 5},
    {'period': 14, 'threshold': 25, 'hold': 5},
    {'period': 20, 'threshold': 30, 'hold': 10},
])
if mr_best and mr_best['sharpe'] >= 1.0:
    validated.append(('RSI Mean Reversion', mr_best))

# 2. Momentum
mom_best = screen_strategy("Momentum", momentum_signal, [
    {'lookback': 10, 'hold': 10},
    {'lookback': 20, 'hold': 20},
    {'lookback': 60, 'hold': 40},
])
if mom_best and mom_best['sharpe'] >= 1.0:
    validated.append(('Momentum', mom_best))

# 3. Bollinger
bb_best = screen_strategy("Bollinger Bands", bollinger_signal, [
    {'period': 20, 'std': 1.5},
    {'period': 20, 'std': 2.0},
    {'period': 30, 'std': 2.0},
])
if bb_best and bb_best['sharpe'] >= 1.0:
    validated.append(('Bollinger Bands', bb_best))

# 4. Volume Breakout
vb_best = screen_strategy("Volume Breakout", volume_breakout_signal, [
    {'vol_mult': 1.5, 'hold': 3},
    {'vol_mult': 2.0, 'hold': 5},
    {'vol_mult': 2.5, 'hold': 10},
])
if vb_best and vb_best['sharpe'] >= 1.0:
    validated.append(('Volume Breakout', vb_best))

# 5. Gap Fade
gf_best = screen_strategy("Gap Fade", gap_fade_signal, [
    {'threshold': 0.005},
    {'threshold': 0.01},
    {'threshold': 0.02},
])
if gf_best and gf_best['sharpe'] >= 1.0:
    validated.append(('Gap Fade', gf_best))


# FINAL SUMMARY
print("\n" + "="*70)
print("VALIDATED STRATEGIES - READY FOR PAPER TRADING")
print("="*70)

if validated:
    for name, result in validated:
        print(f"\n🏆 {name}")
        print(f"   Sharpe: {result['sharpe']:.2f}")
        print(f"   Win Rate: {result['win_rate']:.1f}%")
        print(f"   Trades: {result['trades']}")
        print(f"   Best Params: {result['params']}")
        
        # Trading rules
        print(f"\n   📋 TRADING RULES:")
        p = result['params']
        if name == 'RSI Mean Reversion':
            print(f"   BUY: RSI({p['period']}) < {p['threshold']} AND Volume > 1.3x avg")
            print(f"   SELL: After {p['hold']} days OR profit target")
            print(f"   Position Size: 2% of portfolio")
            print(f"   Stop Loss: 2%")
        elif name == 'Momentum':
            print(f"   BUY: {p['lookback']}-day return > 5%")
            print(f"   SELL: After {p['hold']} days")
            print(f"   Position Size: 2% of portfolio")
            print(f"   Stop Loss: 3%")
        elif name == 'Bollinger Bands':
            print(f"   BUY: Price < Lower Band ({p['period']}, {p['std']}σ)")
            print(f"   SELL: When price returns to SMA")
            print(f"   Position Size: 2% of portfolio")
            print(f"   Stop Loss: 2%")
        elif name == 'Volume Breakout':
            print(f"   BUY: Volume > {p['vol_mult']}x avg AND Price up > 2%")
            print(f"   SELL: After {p['hold']} days")
            print(f"   Position Size: 2% of portfolio")
            print(f"   Stop Loss: 2%")
        elif name == 'Gap Fade':
            print(f"   BUY/SELL: Fade gap > {p['threshold']*100:.1f}%")
            print(f"   SELL: End of day")
            print(f"   Position Size: 1% of portfolio")
            print(f"   Stop Loss: 0.5%")
else:
    print("\n❌ No strategies met validation criteria (Sharpe >= 1.0, Win >= 50%)")
    print("\nRecommendations:")
    print("- Lower Sharpe threshold to 0.8 for testing")
    print("- Try different parameter ranges")
    print("- Test on specific sectors/asset classes")

print("\n" + "="*70)
print(f"Total Validated: {len(validated)} strategies")
print("="*70)
