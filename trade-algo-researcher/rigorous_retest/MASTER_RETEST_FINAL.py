#!/usr/bin/env python3
"""
MASTER RE-TEST — ALL STRATEGIES
Full universe → Sector breakdown → Side-by-side comparison
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

# Load all tickers
print("="*100)
print("MASTER RE-TEST — ALL STRATEGIES")
print("="*100)

ticker_query = """
SELECT ticker, COUNT(*) as records,
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
print(f"Total tickers: {len(all_tickers)}")

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

def test_strategy(name, entry_fn, hold_days):
    """Test strategy on ALL tickers"""
    all_trades = []
    
    for i, ticker_info in enumerate(all_tickers):
        if i % 50 == 0:
            print(f"    Progress: {i}/{len(all_tickers)}")
        
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
    
    train = trades_df[(trades_df['entry_date']>=TRAIN_START) & (trades_df['entry_date']<=TRAIN_END)]
    test = trades_df[(trades_df['entry_date']>=TEST_START) & (trades_df['entry_date']<=TEST_END)]
    validate = trades_df[trades_df['entry_date']>=VALIDATE_START]
    last_q = trades_df[trades_df['entry_date']>=LAST_Q_START]
    
    def calc(t):
        if len(t) < 3: return {'trades':0, 'wr':0, 'pnl':0}
        return {'trades':len(t), 'wr':(t['pnl']>0).sum()/len(t)*100, 'pnl':t['net_pnl'].sum()}
    
    train_m, test_m, val_m, last_q_m = calc(train), calc(test), calc(validate), calc(last_q)
    
    # Market breakdown
    market_data = {}
    for m in ['HK','SG','CN','US','CRYPTO']:
        m_test = test[test['market']==m]
        if len(m_test) >= 10:
            market_data[m] = {'wr': (m_test['pnl']>0).sum()/len(m_test)*100, 'trades': len(m_test), 'pnl': m_test['net_pnl'].sum()}
    
    score = sum([test_m['wr']>=55, test_m['trades']>=100, test_m['wr']>0, abs(train_m['wr']-test_m['wr'])<=20, last_q_m['pnl']>0])
    status = "🏆 GOLDEN" if score>=4 else "⭐ VALIDATED" if score>=2 else "📝 HYPOTHESIS"
    
    return {
        'name': name, 'status': status, 'score': score,
        'train': train_m, 'test': test_m, 'validate': val_m, 'last_q': last_q_m,
        'decay': abs(train_m['wr']-test_m['wr']),
        'markets': market_data,
        'buy': name.split(',')[0] if ',' in name else name.split(':')[1] if ':' in name else name,
        'sell': f"{hold_days}-day hold",
        'tickers': len(set([t['ticker'] for t in all_trades]))
    }

# Test strategies
strategies = [
    ('S001-01: RSI < 35 HK Banks', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    ('S001-02: RSI < 30 + Price < SMA20', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['close']<df.iloc[i]['sma20'], 10),
    ('S001-03: RSI < 35 CN Banks', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    ('S001-09: RSI < 35 + Price < SMA50', lambda df,i: df.iloc[i]['rsi_14']<35 and df.iloc[i]['close']<df.iloc[i]['sma50'], 10),
    ('S001-10: RSI < 35 US Staples', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    ('S002-01: Price > SMA50', lambda df,i: df.iloc[i]['close']>df.iloc[i]['sma50'], 15),
    ('H2: ADX > 25', lambda df,i: df.iloc[i]['adx']>25, 10),
    ('H4: RSI < 20', lambda df,i: df.iloc[i]['rsi_14']<20, 5),
    ('RSI < 25, 15d', lambda df,i: df.iloc[i]['rsi_14']<25, 15),
    ('RSI < 30 + Price < SMA50, 10d', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['close']<df.iloc[i]['sma50'], 10),
]

print("\n" + "="*100)
print("TESTING ALL STRATEGIES")
print("="*100)

results = []
for name, fn, hold in strategies:
    print(f"\nTesting: {name}...")
    result = test_strategy(name, fn, hold)
    if result:
        results.append(result)
        print(f"  ✓ {result['status']} | Test: {result['test']['wr']:.1f}% | Trades: {result['test']['trades']}")
    else:
        print(f"  ✗ No results")

# Print report
print("\n" + "="*100)
print("COMPLETE RESULTS")
print("="*100)

for r in sorted(results, key=lambda x: x['test']['wr'], reverse=True):
    print(f"\n{'='*100}")
    print(f"STRATEGY: {r['name']}")
    print(f"STATUS: {r['status']} (Score: {r['score']}/5)")
    print(f"{'='*100}")
    print(f"\nBUY SIGNAL: {r['buy']}")
    print(f"SELL SIGNAL: {r['sell']}")
    print(f"\nPERFORMANCE:")
    print(f"  Train 2021-22: {r['train']['wr']:.1f}% | {r['train']['trades']} trades | ${r['train']['pnl']:,.0f}")
    print(f"  Test 2023-24:  {r['test']['wr']:.1f}% | {r['test']['trades']} trades | ${r['test']['pnl']:,.0f}")
    print(f"  Validate 2025+: {r['validate']['wr']:.1f}% | {r['validate']['trades']} trades | ${r['validate']['pnl']:,.0f}")
    print(f"  LAST Q P&L: ${r['last_q']['pnl']:,.0f} | {r['last_q']['trades']} trades")
    print(f"\nMETRICS: Decay {r['decay']:.1f}% | Tickers {r['tickers']}")
    print(f"\nMARKET BREAKDOWN:")
    for m, d in sorted(r['markets'].items(), key=lambda x: x[1]['wr'], reverse=True):
        print(f"  {m}: {d['wr']:.1f}% WR | {d['trades']} trades | ${d['pnl']:,.0f}")

# Summary table
print(f"\n{'='*100}")
print("SUMMARY TABLE")
print(f"{'='*100}")
print(f"{'Strategy':<55} {'Status':<12} {'Test WR':<10} {'Trades':<10} {'Last Q P&L':<15}")
print("-"*100)
for r in sorted(results, key=lambda x: x['test']['wr'], reverse=True):
    print(f"{r['name']:<55} {r['status']:<12} {r['test']['wr']:>8.1f}% {r['test']['trades']:>8} ${r['last_q']['pnl']:>12,.0f}")

conn.close()
print(f"\n{'='*100}")
