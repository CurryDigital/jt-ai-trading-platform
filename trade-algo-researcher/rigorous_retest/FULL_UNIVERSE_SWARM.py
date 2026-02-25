#!/usr/bin/env python3
"""
FULL UNIVERSE SWARM — 420 TICKERS ACROSS 4 MARKETS
Testing top strategies on complete universe
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

# Get ALL tickers from database
print("Loading full ticker universe...")
ticker_query = """
SELECT ticker, COUNT(*) as records 
FROM silver.unified_prices 
GROUP BY ticker 
HAVING COUNT(*) >= 500
ORDER BY COUNT(*) DESC
"""
ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df['ticker'].tolist()

print(f"Testing {len(all_tickers)} tickers with 500+ records")

def fetch_data(ticker):
    query = f"""
    SELECT date, close FROM silver.unified_prices
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
    SELECT date, rsi_14 FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_strategy_full_universe(name, entry_fn, hold_days):
    """Test on all tickers, aggregate results"""
    all_trades = []
    tickers_tested = 0
    tickers_with_signals = 0
    
    for i, ticker in enumerate(all_tickers):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(all_tickers)} tickers...")
        
        prices = fetch_data(ticker)
        ind = fetch_indicators(ticker)
        
        if prices is None:
            continue
        
        tickers_tested += 1
        
        df = prices.join(ind, how='inner') if ind is not None else prices
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        ticker_trades = 0
        in_position = False
        exit_date = None
        
        for j in range(50, len(df) - hold_days):
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
                            'ticker': ticker,
                            'entry_date': current_date,
                            'pnl': pnl_pct,
                            'net_pnl': net_pnl
                        })
                        ticker_trades += 1
                        in_position = True
                except:
                    continue
        
        if ticker_trades > 0:
            tickers_with_signals += 1
    
    print(f"  Tickers tested: {tickers_tested}")
    print(f"  Tickers with signals: {tickers_with_signals}")
    print(f"  Total trades: {len(all_trades)}")
    
    if len(all_trades) < 50:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split periods
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc(t):
        if len(t) < 10:
            return {'trades': len(t), 'wr': 0, 'total_pnl': 0}
        return {
            'trades': len(t),
            'wr': (t['pnl'] > 0).sum() / len(t) * 100,
            'total_pnl': t['net_pnl'].sum()
        }
    
    train_m = calc(train)
    test_m = calc(test)
    validate_m = calc(validate)
    last_q_m = calc(last_q)
    
    analytics = BacktestAnalytics()
    mc = analytics.monte_carlo_simulation(test, n_simulations=1000, hold_days=hold_days) if len(test) >= 20 else {'mc_robustness_score': 0}
    decay = abs(train_m['wr'] - test_m['wr']) if train_m['trades'] > 0 and test_m['trades'] > 0 else 999
    
    score = sum([
        test_m['wr'] >= 55,
        test_m['trades'] >= 100,  # Higher threshold for full universe
        mc['mc_robustness_score'] >= 70,
        decay <= 20,
        last_q_m['total_pnl'] > 0
    ])
    
    status = "🏆 GOLDEN" if score == 5 else "⭐ VALIDATED" if score >= 3 else "📝 HYPOTHESIS"
    
    return {
        'name': name,
        'tickers_tested': tickers_tested,
        'tickers_with_signals': tickers_with_signals,
        'train': train_m, 'test': test_m, 'validate': validate_m, 'last_q': last_q_m,
        'decay': decay, 'mc_robust': mc['mc_robustness_score'],
        'score': score, 'status': status
    }

# Test top 3 swarm strategies on full universe
strategies = [
    ('RSI < 25, 15d', lambda df, i: df.iloc[i]['rsi_14'] < 25, 15),
    ('RSI < 30 + Price < SMA50, 10d', lambda df, i: df.iloc[i]['rsi_14'] < 30 and df.iloc[i]['close'] < df.iloc[i]['sma50'], 10),
    ('RSI < 30, 10d', lambda df, i: df.iloc[i]['rsi_14'] < 30, 10),
]

print("=" * 100)
print("FULL UNIVERSE SWARM — 420 TICKERS")
print("=" * 100)

results = []
for name, fn, hold in strategies:
    print(f"\n{'='*100}")
    print(f"Testing: {name}")
    print(f"{'='*100}")
    
    result = test_strategy_full_universe(name, fn, hold)
    
    if result:
        print(f"\n  Tickers: {result['tickers_with_signals']}/{result['tickers_tested']} had signals")
        print(f"  Train: {result['train']['wr']:.1f}% ({result['train']['trades']}t) | P&L: ${result['train']['total_pnl']:,.0f}")
        print(f"  Test:  {result['test']['wr']:.1f}% ({result['test']['trades']}t) | P&L: ${result['test']['total_pnl']:,.0f}")
        print(f"  Val:   {result['validate']['wr']:.1f}% ({result['validate']['trades']}t) | P&L: ${result['validate']['total_pnl']:,.0f}")
        print(f"  LastQ: {result['last_q']['wr']:.1f}% ({result['last_q']['trades']}t) | P&L: ${result['last_q']['total_pnl']:,.0f}")
        print(f"  Decay: {result['decay']:.1f}% | MC: {result['mc_robust']:.1f}%")
        print(f"  Score: {result['score']}/5 → {result['status']}")
        results.append(result)

# Summary
print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

for r in results:
    print(f"\n{r['name']}:")
    print(f"  Tickers with signals: {r['tickers_with_signals']}/{r['tickers_tested']}")
    print(f"  Test: {r['test']['wr']:.1f}% WR | ${r['test']['total_pnl']:,.0f} P&L | {r['status']}")

conn.close()
print(f"\n{'='*100}")
