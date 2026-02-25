#!/usr/bin/env python3
"""
TEST MORE HYPOTHESES — VWAP, Pairs, Mean Reversion, Support/Resistance
HK + US + SG Full Universe
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
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
LAST_Q_START = '2024-10-01'
POSITION_SIZE = 10000

print("Loading tickers...")
ticker_query = """
SELECT ticker, 
    CASE 
        WHEN ticker LIKE '%.HK' THEN 'HK'
        WHEN ticker LIKE '%.SI' THEN 'SG'
        ELSE 'US'
    END as market
FROM silver.unified_prices 
WHERE date >= '2021-01-01'
  AND (ticker LIKE '%.HK' OR ticker LIKE '%.SI' OR ticker NOT LIKE '%.%')
GROUP BY ticker HAVING COUNT(*) >= 500
"""
ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df.to_dict('records')
print(f"Testing {len(all_tickers)} tickers")

def get_data(ticker):
    q1 = f"SELECT date, close, volume, open, high, low FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
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
    
    # Calculate indicators
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # VWAP calculation
    tp = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (tp * df['volume']).cumsum() / df['volume'].cumsum()
    
    return df

def test_strategy(name, condition_fn, hold_days):
    print(f"\nTesting {name}...")
    trades = []
    
    for ticker_info in all_tickers:
        ticker = ticker_info['ticker']
        market = ticker_info['market']
        
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
                        trades.append({'pnl': pnl, 'market': market})
                except: continue
    
    if len(trades) < 50:
        print(f"  Insufficient trades: {len(trades)}")
        return None
    
    # Calculate metrics
    pnls = [t['pnl'] for t in trades]
    wr = sum([p > 0 for p in pnls]) / len(pnls) * 100
    
    # Market breakdown
    for m in ['HK', 'SG', 'US']:
        m_trades = [t['pnl'] for t in trades if t['market'] == m]
        if len(m_trades) >= 10:
            m_wr = sum([p > 0 for p in m_trades]) / len(m_trades) * 100
            print(f"  {m}: {m_wr:.1f}% WR ({len(m_trades)}t)")
    
    print(f"  OVERALL: {wr:.1f}% WR | {len(trades)} trades")
    return {'name': name, 'wr': wr, 'trades': len(trades)}

# Test more hypotheses
strategies = [
    # VWAP Bounce
    ('H13: VWAP Bounce', lambda df,i: abs(df.iloc[i]['close']-df.iloc[i]['vwap'])/df.iloc[i]['close']<0.01 and df.iloc[i]['close']>df.iloc[i]['sma20'], 5),
    
    # Support Level Bounce (20-day low)
    ('H14: Support Bounce', lambda df,i: df.iloc[i]['close']<=df.iloc[i-20:i]['low'].min()*1.02 and df.iloc[i]['close']>=df.iloc[i-20:i]['low'].min() and df.iloc[i]['rsi_14']<35, 10),
    
    # RSI Divergence (simplified)
    ('H15: RSI Bullish', lambda df,i: df.iloc[i]['close']<df.iloc[i]['sma50'] and df.iloc[i]['rsi_14']>40 and df.iloc[i]['rsi_14']<50, 10),
    
    # Low Volatility Expansion
    ('H16: Low Vol Breakout', lambda df,i: df.iloc[i-10:i]['close'].std()/df.iloc[i]['close']<0.02 and df.iloc[i]['close']>df.iloc[i-10:i]['high'].max(), 5),
    
    # MACD Histogram Turn
    ('H17: MACD Turn', lambda df,i: df.iloc[i]['macd_line']-df.iloc[i]['macd_signal']>0 and df.iloc[i-1]['macd_line']-df.iloc[i-1]['macd_signal']<0, 10),
    
    # 3-Day Momentum
    ('H18: 3-Day Momentum', lambda df,i: df.iloc[i]['close']/df.iloc[i-3]['close']>1.03 and df.iloc[i]['vol_ratio']>1.5, 5),
]

print("="*100)
print("TESTING MORE HYPOTHESES — HK+US+SG")
print("="*100)

results = []
for name, fn, hold in strategies:
    result = test_strategy(name, fn, hold)
    if result:
        results.append(result)

# Summary
print("\n" + "="*100)
print("SUMMARY — MORE HYPOTHESES")
print("="*100)
print(f"{'{'}{'Strategy':<35} {'WR':<8} {'Trades':<8}{'}'}")
print("-"*100)

for r in sorted(results, key=lambda x: x['wr'], reverse=True):
    print(f"{'{'}{r['name']:<35} {r['wr']:>6.1f}% {r['trades']:>6}{'}'}")

conn.close()
print("="*100)
