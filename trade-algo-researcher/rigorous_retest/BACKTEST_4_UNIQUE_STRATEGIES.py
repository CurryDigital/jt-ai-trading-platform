#!/usr/bin/env python3
"""
BACKTEST 4 UNIQUE STRATEGIES — FULL UNIVERSE
No overlaps, no inflation, honest reporting
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
POSITION_SIZE = 10000

print("="*100)
print("4 UNIQUE STRATEGIES — FULL UNIVERSE BACKTEST")
print("="*100)

# Load all tickers
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
GROUP BY ticker
HAVING COUNT(*) >= 500
"""
ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df.to_dict('records')
print(f"Testing on {len(all_tickers)} tickers")

def fetch_data(ticker):
    query = f"SELECT date, close FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    query = f"SELECT date, rsi_14, adx FROM gold.technical_indicators_calculated WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_strategy(name, entry_fn, hold_days, description):
    """Test one strategy on all tickers"""
    print(f"\n{'='*100}")
    print(f"STRATEGY: {name}")
    print(f"LOGIC: {description}")
    print(f"{'='*100}")
    
    all_trades = []
    
    for i, ticker_info in enumerate(all_tickers):
        if i % 50 == 0:
            print(f"  {i}/{len(all_tickers)}...")
        
        ticker = ticker_info['ticker']
        market = ticker_info['market']
        
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        in_position = False
        exit_date = None
        
        for j in range(50, len(df)-hold_days):
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
    for m in ['HK','SG','CN','US','CRYPTO']:
        m_test = test[test['market']==m]
        if len(m_test) >= 10:
            m_wr = (m_test['pnl']>0).sum()/len(m_test)*100
            print(f"    {m}: {m_wr:.1f}% WR | {len(m_test)} trades | ${m_test['net_pnl'].sum():,.0f}")
    
    decay = abs(train_m['wr']-test_m['wr'])
    score = sum([test_m['wr']>=55, test_m['trades']>=100, decay<=20, last_q_m['pnl']>0])
    status = "🏆 GOLDEN" if score>=4 else "⭐ VALIDATED" if score>=2 else "📝 TESTING"
    
    return {
        'name': name, 'description': description,
        'train': train_m, 'test': test_m, 'validate': val_m, 'last_q': last_q_m,
        'decay': decay, 'status': status, 'score': score,
        'tickers': len(set([t['ticker'] for t in all_trades])),
        'trades_df': trades_df
    }

# 4 UNIQUE STRATEGIES
strategies = [
    ('S1: RSI Mean Reversion', lambda df,i: df.iloc[i]['rsi_14']<25, 15, 'RSI < 25, 15-day hold'),
    ('S2: RSI + SMA Filter', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['close']<df.iloc[i]['sma50'], 10, 'RSI < 30 AND Price < SMA50'),
    ('S3: Trend Following', lambda df,i: df.iloc[i]['close']>df.iloc[i]['sma50'], 15, 'Price > SMA50, 15-day hold'),
    ('S4: ADX Trend', lambda df,i: df.iloc[i]['adx']>25, 10, 'ADX > 25, 10-day hold'),
]

results = []
for name, fn, hold, desc in strategies:
    result = test_strategy(name, fn, hold, desc)
    if result:
        results.append(result)

# Summary
print("\n" + "="*100)
print("SUMMARY — 4 UNIQUE STRATEGIES")
print("="*100)

for r in results:
    print(f"\n{r['name']}: {r['status']}")
    print(f"  Buy: {r['description']}")
    print(f"  Sell: {r['description'].split(',')[1] if ',' in r['description'] else str(r['train']['trades'])+'-day hold'}")
    print(f"  Train: {r['train']['wr']:.1f}% | {r['train']['trades']} trades")
    print(f"  Test:  {r['test']['wr']:.1f}% | {r['test']['trades']} trades | ${r['test']['pnl']:,.0f}")
    print(f"  Validate: {r['validate']['wr']:.1f}% | {r['last_q']['pnl']:+,.0f} Last Q")
    print(f"  Decay: {r['decay']:.1f}% | Tickers: {r['tickers']}")

# Table
print("\n" + "="*100)
print(f"{'Strategy':<30} {'Status':<12} {'Test WR':<10} {'Trades':<10} {'Last Q P&L':<15}")
print("-"*100)
for r in results:
    print(f"{r['name']:<30} {r['status']:<12} {r['test']['wr']:>8.1f}% {r['test']['trades']:>8} ${r['last_q']['pnl']:>12,.0f}")

conn.close()
print("\n" + "="*100)
