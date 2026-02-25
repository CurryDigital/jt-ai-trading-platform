#!/usr/bin/env python3
"""
CONTINUOUS HYPOTHESIS TESTING — FULL UNIVERSE
Testing until 12pm HKT
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

# Load tickers
print("Loading universe...")
ticker_query = """
SELECT ticker, 
    CASE 
        WHEN ticker LIKE '%.HK' THEN 'HK'
        WHEN ticker LIKE '%.SI' THEN 'SG'
        WHEN ticker LIKE '%.SS' OR ticker LIKE '%.SZ' THEN 'CN'
        WHEN ticker LIKE '%-USD' THEN 'CRYPTO'
        ELSE 'US'
    END as market
FROM silver.unified_prices 
WHERE date >= '2021-01-01'
GROUP BY ticker HAVING COUNT(*) >= 500
"""
ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df.to_dict('records')
print(f"Testing {len(all_tickers)} tickers")

def get_data(ticker):
    q1 = f"SELECT date, close, volume, open, high, low FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    q2 = f"SELECT date, rsi_14, macd_line, macd_signal, adx, bb_upper, bb_lower, bb_middle, stoch_k, stoch_d FROM gold.technical_indicators_calculated WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    
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
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
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
        print(f"  Insufficient: {len(trades)}")
        return None
    
    wr = sum([p > 0 for p in [t['pnl'] for t in trades]]) / len(trades) * 100
    
    # Market breakdown
    market_stats = {}
    for m in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
        m_trades = [t['pnl'] for t in trades if t['market'] == m]
        if len(m_trades) >= 10:
            market_stats[m] = sum([p > 0 for p in m_trades]) / len(m_trades) * 100
    
    print(f"  WR: {wr:.1f}% | Trades: {len(trades)}")
    for m, w in market_stats.items():
        print(f"    {m}: {w:.1f}%")
    
    return {'name': name, 'wr': wr, 'trades': len(trades), 'markets': market_stats}

print("="*100)
print("BATCH 3 — MORE HYPOTHESES")
print("="*100)

# More hypotheses
strategies = [
    # Moving Average variants
    ('SMA20 Bounce', lambda df,i: df.iloc[i]['close'] < df.iloc[i]['sma20']*1.02 and df.iloc[i]['close'] > df.iloc[i]['sma20']*0.98 and df.iloc[i]['rsi_14'] < 40, 10),
    
    # Double bottom pattern (simplified)
    ('Double Bottom', lambda df,i: abs(df.iloc[i]['close'] - df.iloc[i-5]['close'])/df.iloc[i]['close'] < 0.03 and df.iloc[i]['close'] < df.iloc[i-10:i]['close'].min()*1.05, 15),
    
    # High volume pullback
    ('High Vol Pullback', lambda df,i: df.iloc[i]['close'] < df.iloc[i-1]['close'] and df.iloc[i]['vol_ratio'] > 2 and df.iloc[i]['rsi_14'] < 45, 10),
    
    # RSI divergence (simplified)
    ('RSI Bull Div', lambda df,i: df.iloc[i]['close'] < df.iloc[i-5]['close'] and df.iloc[i]['rsi_14'] > df.iloc[i-5]['rsi_14'] and df.iloc[i]['rsi_14'] < 40, 10),
    
    # Channel breakout
    ('Channel Break', lambda df,i: df.iloc[i]['close'] > df.iloc[i-20:i]['high'].max() * 0.98 and df.iloc[i]['close'] < df.iloc[i-20:i]['high'].max() * 1.02, 5),
    
    # Oversold bounce
    ('Oversold Bounce', lambda df,i: df.iloc[i]['rsi_14'] < 25 and df.iloc[i]['close'] > df.iloc[i-1]['close'], 5),
]

results = []
for name, fn, hold in strategies:
    result = test_strategy(name, fn, hold)
    if result:
        results.append(result)

print("\n" + "="*100)
print("RESULTS — BATCH 3")
print("="*100)
print(f"{'{'}{'Strategy':<30} {'WR':<8} {'Trades':<8}{'}'}")
print("-"*100)

for r in sorted(results, key=lambda x: x['wr'], reverse=True):
    print(f"{'{'}{r['name']:<30} {r['wr']:>6.1f}% {r['trades']:>6}{'}'}")

conn.close()
print("="*100)
