#!/usr/bin/env python3
"""
COMPLETE SECTOR ANALYSIS
Test ALL tickers, group by market, side-by-side comparison
"""

import pandas as pd
import numpy as np
import sys
warnings = __import__('warnings')
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

# Get all tickers with market classification
print("Loading all tickers from database...")
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
ORDER BY market, ticker
"""

ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df.to_dict('records')

print(f"Total tickers to test: {len(all_tickers)}")
print(f"  HK: {len([t for t in all_tickers if t['market'] == 'HK'])}")
print(f"  SG: {len([t for t in all_tickers if t['market'] == 'SG'])}")
print(f"  CN: {len([t for t in all_tickers if t['market'] == 'CN'])}")
print(f"  US: {len([t for t in all_tickers if t['market'] == 'US'])}")
print(f"  CRYPTO: {len([t for t in all_tickers if t['market'] == 'CRYPTO'])}")

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

def test_ticker(ticker_info, rsi_threshold=30, hold_days=10):
    """Test single ticker, return all metrics by period"""
    ticker = ticker_info['ticker']
    market = ticker_info['market']
    
    prices = fetch_data(ticker)
    ind = fetch_indicators(ticker)
    
    if prices is None or ind is None:
        return None
    
    df = prices.join(ind, how='inner')
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    trades = []
    in_position = False
    exit_date = None
    
    for i in range(50, len(df) - hold_days):
        current_date = df.index[i]
        
        if in_position and current_date >= exit_date:
            in_position = False
        
        if not in_position:
            try:
                if df.iloc[i]['rsi_14'] < rsi_threshold:
                    entry_price = df.iloc[i]['close']
                    exit_idx = i + hold_days
                    exit_price = df.iloc[exit_idx]['close']
                    exit_date = df.index[exit_idx]
                    
                    shares = POSITION_SIZE / entry_price
                    gross_pnl = (exit_price - entry_price) * shares
                    cost = POSITION_SIZE * 0.001 * 2
                    net_pnl = gross_pnl - cost
                    pnl_pct = (net_pnl / POSITION_SIZE) * 100
                    
                    trades.append({
                        'entry_date': current_date,
                        'pnl': pnl_pct,
                        'net_pnl': net_pnl
                    })
                    in_position = True
            except:
                continue
    
    if len(trades) < 5:
        return None
    
    trades_df = pd.DataFrame(trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split by period
    train = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    def calc(t):
        if len(t) < 3:
            return {'trades': 0, 'wr': 0, 'pnl': 0}
        wins = (t['pnl'] > 0).sum()
        return {'trades': len(t), 'wr': wins / len(t) * 100, 'pnl': t['net_pnl'].sum()}
    
    train_m = calc(train)
    test_m = calc(test)
    validate_m = calc(validate)
    last_q_m = calc(last_q)
    
    return {
        'ticker': ticker,
        'market': market,
        'train_wr': train_m['wr'],
        'train_trades': train_m['trades'],
        'test_wr': test_m['wr'],
        'test_trades': test_m['trades'],
        'validate_wr': validate_m['wr'],
        'validate_trades': validate_m['trades'],
        'last_q_pnl': last_q_m['pnl'],
        'last_q_trades': last_q_m['trades'],
        'total_trades': len(trades)
    }

# Test all tickers
print("\n" + "="*80)
print("TESTING ALL TICKERS — RSI < 30, 10d")
print("="*80)

results = []
for i, ticker_info in enumerate(all_tickers):
    if i % 25 == 0:
        print(f"  Progress: {i}/{len(all_tickers)}")
    
    result = test_ticker(ticker_info, rsi_threshold=30, hold_days=10)
    if result:
        results.append(result)

print(f"\nCompleted: {len(results)}/{len(all_tickers)} tickers with signals")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print("\n" + "="*80)
print("RESULTS BY MARKET — SIDE BY SIDE COMPARISON")
print("="*80)

market_summary = []
for market in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
    market_data = results_df[results_df['market'] == market]
    if len(market_data) == 0:
        continue
    
    summary = {
        'Market': market,
        'Tickers': len(market_data),
        'Test_WR': market_data['test_wr'].mean(),
        'Test_Trades': market_data['test_trades'].sum(),
        'Train_WR': market_data['train_wr'].mean(),
        'Decay': abs(market_data['train_wr'].mean() - market_data['test_wr'].mean()),
        'Last_Q_PnL': market_data['last_q_pnl'].sum(),
        'Best_Ticker': market_data.loc[market_data['test_wr'].idxmax(), 'ticker'],
        'Best_WR': market_data['test_wr'].max()
    }
    market_summary.append(summary)

summary_df = pd.DataFrame(market_summary)
summary_df = summary_df.sort_values('Test_WR', ascending=False)

print("\n" + summary_df.to_string(index=False))

print("\n" + "="*80)
print("TOP 15 INDIVIDUAL TICKERS (by Test Win Rate)")
print("="*80)

top_15 = results_df[results_df['test_trades'] >= 5].nlargest(15, 'test_wr')
print(top_15[['ticker', 'market', 'test_wr', 'test_trades', 'train_wr', 'last_q_pnl']].to_string(index=False))

print("\n" + "="*80)
print("BOTTOM 10 TICKERS (by Test Win Rate)")
print("="*80)

bottom_10 = results_df[results_df['test_trades'] >= 5].nsmallest(10, 'test_wr')
print(bottom_10[['ticker', 'market', 'test_wr', 'test_trades', 'train_wr', 'last_q_pnl']].to_string(index=False))

print("\n" + "="*80)
print("DEPLOYMENT RECOMMENDATION")
print("="*80)

# Find tickers with >55% WR and >10 trades in test period
good_tickers = results_df[(results_df['test_wr'] >= 55) & (results_df['test_trades'] >= 10)]
print(f"\nTickers passing criteria (Test WR >= 55%, Trades >= 10): {len(good_tickers)}")
print("\nBy Market:")
for market in ['HK', 'SG', 'CN', 'US', 'CRYPTO']:
    count = len(good_tickers[good_tickers['market'] == market])
    total = len(results_df[results_df['market'] == market])
    pct = count/total*100 if total > 0 else 0
    print(f"  {market}: {count}/{total} ({pct:.1f}%)")

conn.close()
print("\n" + "="*80)
