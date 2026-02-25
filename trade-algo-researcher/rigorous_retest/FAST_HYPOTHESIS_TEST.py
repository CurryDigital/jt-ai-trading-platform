#!/usr/bin/env python3
"""
FAST HYPOTHESIS TEST — 8 Strategies
"""

import pandas as pd
import numpy as np
import sys
warnings = __import__('warnings')
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

db = TradeAlgoDB()
conn = db.connect()

TEST_START, TEST_END = '2023-01-01', '2024-12-31'
POSITION_SIZE = 10000

# Sample tickers (faster)
sample_tickers = [
    'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META', 'GOOGL', 'AMZN',
    '0700.HK', '0005.HK', '1398.HK', '3988.HK', '9988.HK',
    '000001.SZ', '000858.SZ', '002594.SZ', '600900.SS',
    'BTC-USD', 'SOL-USD', 'ETH-USD'
]

def get_data(ticker):
    q1 = f"SELECT date, close, volume FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    q2 = f"SELECT date, rsi_14, macd_line, macd_signal, adx, bb_upper, bb_lower, stoch_k FROM gold.technical_indicators_calculated WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    
    p = pd.read_sql(q1, conn)
    i = pd.read_sql(q2, conn)
    
    if len(p)==0 or len(i)==0: return None
    p['date'] = pd.to_datetime(p['date'])
    i['date'] = pd.to_datetime(i['date'])
    p.set_index('date', inplace=True)
    i.set_index('date', inplace=True)
    
    df = p.join(i, how='inner')
    if len(df) < 200: return None
    
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    return df

def test_strategy(name, condition_fn, hold_days):
    trades = []
    
    for ticker in sample_tickers:
        df = get_data(ticker)
        if df is None: continue
        
        for i in range(200, len(df)-hold_days):
            d = str(df.index[i])
            if TEST_START <= d <= TEST_END:
                try:
                    if condition_fn(df, i):
                        entry = df.iloc[i]['close']
                        exit_p = df.iloc[i+hold_days]['close']
                        pnl = ((exit_p - entry)/entry - 0.002) * 100
                        trades.append({'pnl': pnl})
                except: continue
    
    if len(trades) < 20: return None
    
    wr = sum([t['pnl'] > 0 for t in trades]) / len(trades) * 100
    return {'name': name, 'trades': len(trades), 'wr': wr}

print("="*80)
print("FAST HYPOTHESIS TEST — 20 Tickers")
print("="*80)

strategies = [
    ('RSI+MACD Confluence', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['macd_line']>df.iloc[i]['macd_signal'] and df.iloc[i-1]['macd_line']<=df.iloc[i-1]['macd_signal'], 10),
    ('Golden Cross', lambda df,i: df.iloc[i]['sma50']>df.iloc[i]['sma200'] and df.iloc[i-1]['sma50']<=df.iloc[i-1]['sma200'], 15),
    ('BB Squeeze Break', lambda df,i: ((df['bb_upper']-df['bb_lower'])/df['close']).iloc[i-10:i].mean()<0.1 and df.iloc[i]['close']>df.iloc[i]['bb_upper'], 10),
    ('Stochastic Cross', lambda df,i: df.iloc[i]['stoch_k']<20 and df.iloc[i]['stoch_k']>df.iloc[i-1]['stoch_k'] and df.iloc[i-1]['stoch_k']<15, 10),
    ('Volume Breakout', lambda df,i: df.iloc[i]['close']>df.iloc[i-20:i]['close'].max() and df.iloc[i]['vol_ratio']>2, 5),
    ('Gap Up', lambda df,i: df.iloc[i]['close']/df.iloc[i-1]['close']>1.02 and df.iloc[i]['close']>df.iloc[i]['close'], 3),
]

results = []
for name, fn, hold in strategies:
    print(f"\nTesting {name}...")
    r = test_strategy(name, fn, hold)
    if r:
        results.append(r)
        print(f"  {r['wr']:.1f}% WR | {r['trades']} trades")

print("\n" + "="*80)
print("RESULTS (Ranked by Win Rate)")
print("="*80)
print(f"{'{'}{'Strategy':<30} {'WR':<8} {'Trades':<8}{'}'}")
print("-"*80)

for r in sorted(results, key=lambda x: x['wr'], reverse=True):
    print(f"{'{'}{r['name']:<30} {r['wr']:>6.1f}% {r['trades']:>6}{'}'}")

conn.close()
print("="*80)
