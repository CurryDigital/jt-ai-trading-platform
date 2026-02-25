#!/usr/bin/env python3
"""
TEST 4 NEW STRATEGIES — HK + US + SG ONLY
Full tickers, all markets
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
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
VALIDATE_START = '2025-01-01'
POSITION_SIZE = 10000

# Get HK + US + SG tickers only
print("Loading HK + US + SG tickers...")
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
GROUP BY ticker
HAVING COUNT(*) >= 500
"""

ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df.to_dict('records')

print(f"Total tickers: {len(all_tickers)}")
print(f"  HK: {len([t for t in all_tickers if t['market']=='HK'])}")
print(f"  SG: {len([t for t in all_tickers if t['market']=='SG'])}")
print(f"  US: {len([t for t in all_tickers if t['market']=='US'])}")

def fetch_data(ticker):
    query = f"SELECT date, close, volume FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
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

def test_strategy(name, entry_fn, hold_days, desc):
    """Full 3-tier test on HK+US+SG"""
    print(f"\n{'='*100}")
    print(f"TESTING: {name}")
    print(f"LOGIC: {desc}")
    print(f"{'='*100}")
    
    all_trades = []
    
    for i, ticker_info in enumerate(all_tickers):
        if i % 25 == 0:
            print(f"  {i}/{len(all_tickers)}...")
        
        ticker = ticker_info['ticker']
        market = ticker_info['market']
        
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        if len(df) < 200:
            continue
        
        # Calculate indicators
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df['sma200'] = df['close'].rolling(200).mean()
        df['vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        in_position = False
        exit_date = None
        
        for j in range(200, len(df)-hold_days):
            current_date = df.index[j]
            if in_position and current_date >= exit_date:
                in_position = False
            
            if not in_position:
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
                            'entry_date': current_date,
                            'pnl': pnl_pct, 'net_pnl': net_pnl
                        })
                        in_position = True
                except:
                    continue
    
    if len(all_trades) < 50:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Period breakdown
    train = trades_df[(trades_df['entry_date']>=TRAIN_START) & (trades_df['entry_date']<=TRAIN_END)]
    test = trades_df[(trades_df['entry_date']>=TEST_START) & (trades_df['entry_date']<=TEST_END)]
    validate = trades_df[trades_df['entry_date']>=VALIDATE_START]
    last_q = trades_df[trades_df['entry_date']>=LAST_Q_START]
    
    def calc(t):
        if len(t) < 3: return {'trades':0, 'wr':0, 'pnl':0}
        return {'trades':len(t), 'wr':(t['pnl']>0).sum()/len(t)*100, 'pnl':t['net_pnl'].sum()}
    
    train_m, test_m, val_m, last_q_m = calc(train), calc(test), calc(validate), calc(last_q)
    
    # Market breakdown
    print("\n  MARKET BREAKDOWN:")
    for m in ['HK', 'SG', 'US']:
        m_test = test[test['market']==m]
        if len(m_test) >= 10:
            m_wr = (m_test['pnl']>0).sum()/len(m_test)*100
            print(f"    {m}: {m_wr:.1f}% WR | {len(m_test)} trades | ${m_test['net_pnl'].sum():,.0f}")
    
    decay = abs(train_m['wr']-test_m['wr']) if train_m['trades']>0 and test_m['trades']>0 else 999
    score = sum([test_m['wr']>=55, test_m['trades']>=50, decay<=20, last_q_m['pnl']>0])
    status = "🏆 GOLDEN" if score>=4 else "⭐ VALIDATED" if score>=2 else "📝 TESTING"
    
    return {
        'name': name, 'desc': desc, 'status': status,
        'train': train_m, 'test': test_m, 'validate': val_m, 'last_q': last_q_m,
        'decay': decay, 'score': score,
        'tickers': len(set([t['ticker'] for t in all_trades]))
    }

# 4 strategies
strategies = [
    ('Golden Cross', lambda df,i: df.iloc[i]['sma50']>df.iloc[i]['sma200'] and df.iloc[i-1]['sma50']<=df.iloc[i-1]['sma200'], 15, 'SMA50 crosses above SMA200'),
    ('Stochastic Cross', lambda df,i: df.iloc[i]['stoch_k']<25 and df.iloc[i]['stoch_k']>df.iloc[i-1]['stoch_k'] and df.iloc[i-1]['stoch_k']<20, 10, 'Stoch K < 25 and rising from oversold'),
    ('BB Squeeze Break', lambda df,i: df.iloc[i]['bb_width']<0.08 and df.iloc[i]['close']>df.iloc[i]['bb_upper'], 10, 'BB width < 8% + breaks upper'),
    ('Volume Breakout', lambda df,i: df.iloc[i]['close']>df.iloc[i-20:i]['close'].max() and df.iloc[i]['vol_ratio']>2, 5, 'Breaks 20d high + volume >2x'),
]

results = []
for name, fn, hold, desc in strategies:
    result = test_strategy(name, fn, hold, desc)
    if result:
        results.append(result)

# Summary
print("\n" + "="*100)
print("SUMMARY — 4 STRATEGIES ON HK+US+SG")
print("="*100)

for r in results:
    print(f"\n{r['name']}: {r['status']}")
    print(f"  Buy: {r['desc']}")
    print(f"  Sell: {r['test']['trades']}d hold")
    print(f"  Train: {r['train']['wr']:.1f}% | Test: {r['test']['wr']:.1f}% | Decay: {r['decay']:.1f}%")
    print(f"  Last Q: ${r['last_q']['pnl']:,.0f} | Tickers: {r['tickers']}")

print("\n" + "="*100)
print(f"{'Strategy':<25} {'Status':<12} {'Test WR':<10} {'Trades':<10} {'Last Q':<15}")
print("-"*100)
for r in sorted(results, key=lambda x: x['test']['wr'], reverse=True):
    print(f"{r['name']:<25} {r['status']:<12} {r['test']['wr']:>8.1f}% {r['test']['trades']:>8} ${r['last_q']['pnl']:>12,.0f}")

conn.close()
print("="*100)
