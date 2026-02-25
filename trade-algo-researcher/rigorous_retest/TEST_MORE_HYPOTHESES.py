#!/usr/bin/env python3
"""
TEST ADDITIONAL HYPOTHESES — FULL UNIVERSE
RSI+MACD, Golden Cross, BB Squeeze, Stochastic, VWAP, Breakout, Gap, Inside Bar
"""

import pandas as pd
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

db = TradeAlgoDB()
conn = db.connect()

TEST_START, TEST_END = '2023-01-01', '2024-12-31'
LAST_Q_START = '2024-10-01'
POSITION_SIZE = 10000

# Load tickers
print("Loading universe...")
ticker_query = """
SELECT ticker, CASE 
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

def fetch_data(ticker):
    query = f"SELECT date, close, volume, open, high, low FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    query = f"SELECT date, rsi_14, macd_line, macd_signal, adx, bb_upper, bb_lower, bb_middle, stoch_k, stoch_d FROM gold.technical_indicators_calculated WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def quick_test(name, entry_fn, hold_days=10):
    """Quick test on all tickers — test period only"""
    print(f"\nTesting: {name}...")
    all_trades = []
    
    for i, ticker_info in enumerate(all_tickers):
        if i % 50 == 0:
            print(f"  {i}/{len(all_tickers)}")
        
        ticker = ticker_info['ticker']
        market = ticker_info['market']
        
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        if len(df) == 0:
            continue
        
        # Calculate additional indicators
        if 'close' in df.columns:
            df['sma20'] = df['close'].rolling(20).mean()
            df['sma50'] = df['close'].rolling(50).mean()
            df['sma200'] = df['close'].rolling(200).mean()
        if 'volume' in df.columns:
            df['vol_sma20'] = df['volume'].rolling(20).mean()
            df['vol_ratio'] = df['volume'] / df['vol_sma20']
        if all(c in df.columns for c in ['high', 'low', 'close']):
            df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        in_position = False
        exit_date = None
        
        for j in range(200, len(df)-hold_days):
            current_date = df.index[j]
            
            if in_position and current_date >= exit_date:
                in_position = False
            
            if not in_position and TEST_START <= str(current_date) <= TEST_END:
                try:
                    if entry_fn(df, j):
                        entry_price = df.iloc[j]['close']
                        exit_idx = j + hold_days
                        exit_price = df.iloc[exit_idx]['close']
                        exit_date = df.index[exit_idx]
                        
                        shares = POSITION_SIZE / entry_price
                        gross_pnl = (exit_price - entry_price) * shares
                        cost = POSITION_SIZE * 0.001 * 2
                        net_pnl = gross_pnl - cost
                        pnl_pct = (net_pnl / POSITION_SIZE) * 100
                        
                        all_trades.append({
                            'ticker': ticker, 'market': market,
                            'entry_date': current_date, 'pnl': pnl_pct
                        })
                        in_position = True
                except:
                    continue
    
    if len(all_trades) < 50:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Test period metrics
    test_wr = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
    
    # Market breakdown
    market_stats = {}
    for m in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
        m_data = trades_df[trades_df['market'] == m]
        if len(m_data) >= 10:
            market_stats[m] = {
                'wr': (m_data['pnl'] > 0).sum() / len(m_data) * 100,
                'trades': len(m_data)
            }
    
    return {
        'name': name,
        'test_trades': len(trades_df),
        'test_wr': test_wr,
        'markets': market_stats
    }

# Define hypotheses to test
hypotheses = [
    # RSI + MACD Confluence
    ('H5: RSI + MACD Confluence', lambda df,i: df.iloc[i]['rsi_14'] < 30 and df.iloc[i]['macd_line'] > df.iloc[i]['macd_signal'] and df.iloc[i]['macd_line'].shift(1) <= df.iloc[i]['macd_signal'].shift(1), 10),
    
    # Golden Cross (SMA50 crosses above SMA200)
    ('H6: Golden Cross', lambda df,i: df.iloc[i]['sma50'] > df.iloc[i]['sma200'] and df.iloc[i-1]['sma50'] <= df.iloc[i-1]['sma200'], 15),
    
    # Bollinger Band Squeeze + Breakout
    ('H7: BB Squeeze Breakout', lambda df,i: ((df.iloc[i-10:i]['bb_upper'] - df.iloc[i-10:i]['bb_lower']) / df.iloc[i-10:i]['bb_middle']).mean() < 0.08 and df.iloc[i]['close'] > df.iloc[i]['bb_upper'] and df.iloc[i]['vol_ratio'] > 1.5, 10),
    
    # Stochastic Oversold Cross
    ('H8: Stochastic Cross', lambda df,i: df.iloc[i]['stoch_k'] < 20 and df.iloc[i]['stoch_k'] > df.iloc[i]['stoch_d'] and df.iloc[i-1]['stoch_k'] <= df.iloc[i-1]['stoch_d'], 10),
    
    # VWAP Bounce (simplified)
    ('H9: VWAP Bounce', lambda df,i: abs(df.iloc[i]['close'] - df.iloc[i]['vwap']) / df.iloc[i]['close'] < 0.01 and df.iloc[i]['close'] > df.iloc[i]['sma20'], 5),
    
    # Breakout with Volume
    ('H10: Volume Breakout', lambda df,i: df.iloc[i]['close'] > df.iloc[i-20:i]['high'].max() and df.iloc[i]['vol_ratio'] > 2.0, 5),
    
    # Gap and Go (simplified)
    ('H11: Gap Up', lambda df,i: df.iloc[i]['open'] > df.iloc[i-1]['close'] * 1.02 and df.iloc[i]['close'] > df.iloc[i]['open'], 3),
    
    # Inside Bar Breakout
    ('H12: Inside Bar Breakout', lambda df,i: df.iloc[i-1]['high'] < df.iloc[i-2]['high'] and df.iloc[i-1]['low'] > df.iloc[i-2]['low'] and df.iloc[i]['close'] > df.iloc[i-2]['high'], 5),
]

print("="*100)
print("TESTING HYPOTHESES — FULL UNIVERSE")
print("="*100)

results = []
for name, fn, hold in hypotheses:
    result = quick_test(name, fn, hold)
    if result:
        results.append(result)
        print(f"  ✓ {result['test_wr']:.1f}% WR | {result['test_trades']} trades")
        for m, s in result['markets'].items():
            print(f"    {m}: {s['wr']:.1f}% ({s['trades']}t)")

# Summary
print("\n" + "="*100)
print("SUMMARY — HYPOTHESIS TESTING")
print("="*100)
print(f"{'Strategy':<40} {'Test WR':<10} {'Trades':<10} {'Best Market':<15}")
print("-"*100)

for r in sorted(results, key=lambda x: x['test_wr'], reverse=True):
    best_m = max(r['markets'].items(), key=lambda x: x[1]['wr']) if r['markets'] else ('N/A', {'wr': 0})
    print(f"{r['name']:<40} {r['test_wr']:>8.1f}% {r['test_trades']:>8} {best_m[0]:<10} {best_m[1]['wr']:.1f}%")

conn.close()
print("\n" + "="*100)
