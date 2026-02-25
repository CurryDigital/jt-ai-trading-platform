#!/usr/bin/env python3
"""
MASTER RE-TEST — ALL STRATEGIES
Golden + Near-Golden + Validated + Hypothesis
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
print(f"  HK: {len([t for t in all_tickers if t['market']=='HK'])}")
print(f"  SG: {len([t for t in all_tickers if t['market']=='SG'])}")
print(f"  CN: {len([t for t in all_tickers if t['market']=='CN'])}")
print(f"  US: {len([t for t in all_tickers if t['market']=='US'])}")
print(f"  CRYPTO: {len([t for t in all_tickers if t['market']=='CRYPTO'])}")

def fetch_data(ticker):
    query = f"SELECT date, close FROM silver.unified_prices WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    query = f"SELECT date, rsi_14, adx, bb_upper, bb_lower, bb_middle FROM gold.technical_indicators_calculated WHERE ticker='{ticker}' AND date>='2021-01-01' ORDER BY date"
    df = pd.read_sql(query, conn)
    if len(df)==0: return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_strategy_full_universe(name, entry_fn, hold_days, cost_pct=0.001):
    """Test strategy on ALL tickers, return detailed breakdown"""
    all_trades = []
    ticker_results = []
    
    for ticker_info in all_tickers:
        ticker = ticker_info['ticker']
        market = ticker_info['market']
        
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        if prices is None or ind is None:
            continue
        
        df = prices.join(ind, how='inner')
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        ticker_trades = []
        in_position = False
        exit_date = None
        
        for i in range(50, len(df)-hold_days):
            current_date = df.index[i]
            if in_position and current_date >= exit_date:
                in_position = False
            
            if not in_position:
                try:
                    if entry_fn(df, i):
                        entry_price = df.iloc[i]['close']
                        exit_idx = i + hold_days
                        exit_price = df.iloc[exit_idx]['close']
                        exit_date = df.index[exit_idx]
                        
                        shares = POSITION_SIZE / entry_price
                        gross_pnl = (exit_price - entry_price) * shares
                        cost = POSITION_SIZE * cost_pct * 2
                        net_pnl = gross_pnl - cost
                        pnl_pct = (net_pnl / POSITION_SIZE) * 100
                        
                        trade = {
                            'ticker': ticker, 'market': market,
                            'entry_date': current_date, 'exit_date': exit_date,
                            'entry_price': entry_price, 'exit_price': exit_price,
                            'pnl': pnl_pct, 'net_pnl': net_pnl
                        }
                        all_trades.append(trade)
                        ticker_trades.append(trade)
                        in_position = True
                except:
                    continue
        
        # Calculate per-ticker metrics
        if len(ticker_trades) >= 3:
            tdf = pd.DataFrame(ticker_trades)
            test_trades = tdf[(tdf['entry_date']>=TEST_START) & (tdf['entry_date']<=TEST_END)]
            if len(test_trades) >= 3:
                ticker_results.append({
                    'ticker': ticker, 'market': market,
                    'total_trades': len(ticker_trades),
                    'test_trades': len(test_trades),
                    'test_wr': (test_trades['pnl_pct']>0).sum()/len(test_trades)*100,
                    'total_pnl': tdf['net_pnl'].sum()
                })
    
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
        return {'trades':len(t), 'wr':(t['pnl_pct']>0).sum()/len(t)*100, 'pnl':t['net_pnl'].sum()}
    
    train_m, test_m, validate_m, last_q_m = calc(train), calc(test), calc(validate), calc(last_q)
    
    # MC on test
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=hold_days) if len(test)>=20 else {'mc_robustness_score':0}
    decay = abs(train_m['wr']-test_m['wr']) if train_m['trades']>0 and test_m['trades']>0 else 999
    
    # Market breakdown
    market_breakdown = {}
    for m in ['HK','SG','CN','US','CRYPTO']:
        m_data = trades_df[trades_df['market']==m]
        m_test = m_data[(m_data['entry_date']>=TEST_START) & (m_data['entry_date']<=TEST_END)]
        if len(m_test) >= 10:
            market_breakdown[m] = {
                'trades': len(m_test),
                'wr': (m_test['pnl_pct']>0).sum()/len(m_test)*100,
                'pnl': m_test['net_pnl'].sum()
            }
    
    # Classification
    score = sum([test_m['wr']>=55, test_m['trades']>=100, mc['mc_robustness_score']>=70, decay<=20, last_q_m['pnl']>0])
    status = "🏆 GOLDEN" if score==5 else "⭐ VALIDATED" if score>=3 else "📝 HYPOTHESIS"
    
    return {
        'name': name, 'status': status, 'score': score,
        'train': train_m, 'test': test_m, 'validate': validate_m, 'last_q': last_q_m,
        'decay': decay, 'mc_robust': mc['mc_robustness_score'],
        'market_breakdown': market_breakdown,
        'ticker_results': ticker_results,
        'total_tickers': len(set([t['ticker'] for t in all_trades])),
        'buy_signal': f"{name.split(',')[0]}",
        'sell_signal': f"{hold_days}-day hold"
    }

# Define all strategies to test
strategies = [
    # GOLDEN strategies
    ('S001-01: RSI < 35 HK Banks', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    ('S002-01: Trend US ETF (Price > SMA50)', lambda df,i: df.iloc[i]['close']>df.iloc[i]['sma50'], 15),
    ('H2: ADX Trend (ADX > 25)', lambda df,i: df.iloc[i]['adx']>25, 10),
    ('H3: Volume Breakout', lambda df,i: False, 5),  # Skip - needs volume data
    ('H4: RSI < 20 Extreme', lambda df,i: df.iloc[i]['rsi_14']<20, 5),
    
    # Near-golden / Validated
    ('S001-02: RSI < 30 US Consumer', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['close']<df.iloc[i]['sma20'], 10),
    ('S001-03: RSI < 35 CN Banks', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    ('S001-09: RSI < 35 HK Property', lambda df,i: df.iloc[i]['rsi_14']<35 and df.iloc[i]['close']<df.iloc[i]['sma50'], 10),
    ('S001-10: RSI < 35 US Staples', lambda df,i: df.iloc[i]['rsi_14']<35, 10),
    
    # Hypotheses
    ('RSI < 25, 15d', lambda df,i: df.iloc[i]['rsi_14']<25, 15),
    ('RSI < 30 + Price < SMA50, 10d', lambda df,i: df.iloc[i]['rsi_14']<30 and df.iloc[i]['close']<df.iloc[i]['sma50'], 10),
    ('RSI < 30, 10d', lambda df,i: df.iloc[i]['rsi_14']<30, 10),
]

print("\n" + "="*100)
print("TESTING ALL STRATEGIES")
print("="*100)

all_results = []
for name, fn, hold in strategies:
    print(f"\nTesting: {name}...")
    result = test_strategy_full_universe(name, fn, hold)
    if result:
        all_results.append(result)
        print(f"  Status: {result['status']} | Test WR: {result['test']['wr']:.1f}% | Trades: {result['test']['trades']}")
    else:
        print(f"  ❌ Insufficient data")

# Print comprehensive report
print("\n" + "="*100)
print("COMPREHENSIVE RESULTS REPORT")
print("="*100)

for r in sorted(all_results, key=lambda x: x['test']['wr'], reverse=True):
    print(f"\n{'='*100}")
    print(f"STRATEGY: {r['name']}")
    print(f"STATUS: {r['status']} (Score: {r['score']}/5)")
    print(f"{'='*100}")
    
    print(f"\nBUY SIGNAL: {r['buy_signal']}")
    print(f"SELL SIGNAL: {r['sell_signal']}")
    
    print(f"\nPERFORMANCE BY PERIOD:")
    print(f"  Train (2021-2022): {r['train']['wr']:.1f}% WR | {r['train']['trades']} trades | ${r['train']['pnl']:,.0f}")
    print(f"  Test (2023-2024):  {r['test']['wr']:.1f}% WR | {r['test']['trades']} trades | ${r['test']['pnl']:,.0f}")
    print(f"  Validate (2025+):  {r['validate']['wr']:.1f}% WR | {r['validate']['trades']} trades | ${r['validate']['pnl']:,.0f}")
    print(f"  Last Q:            ${r['last_q']['pnl']:,.0f} | {r['last_q']['trades']} trades")
    
    print(f"\nMETRICS:")
    print(f"  Decay: {r['decay']:.1f}% | MC Robust: {r['mc_robust']:.1f}%")
    print(f"  Total Tickers: {r['total_tickers']}")
    
    print(f"\nMARKET BREAKDOWN:")
    for m, data in sorted(r['market_breakdown'].items(), key=lambda x: x[1]['wr'], reverse=True):
        print(f"  {m}: {data['wr']:.1f}% WR | {data['trades']} trades | ${data['pnl']:,.0f}")

# Summary table
print(f"\n{'='*100}")
print("SUMMARY TABLE")
print(f"{'='*100}")
print(f"{'Strategy':<50} {'Status':<15} {'Test WR':<10} {'Trades':<10} {'Last Q P&L':<15}")
print("-"*100)
for r in sorted(all_results, key=lambda x: x['test']['wr'], reverse=True):
    print(f"{r['name']:<50} {r['status']:<15} {r['test']['wr']:>8.1f}% {r['test']['trades']:>8} ${r['last_q']['pnl']:>12,.0f}")

conn.close()
print(f"\n{'='*100}")
