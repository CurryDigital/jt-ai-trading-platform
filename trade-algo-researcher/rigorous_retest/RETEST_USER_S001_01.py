#!/usr/bin/env python3
"""
RE-TEST USER'S DEFINED STRATEGIES WITH REAL DATA
S001-01: RSI Mean Reversion — HK Banks
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

# USER'S DEFINED STRATEGY PARAMETERS
STRATEGY = {
    'id': 'S001-01',
    'name': 'RSI Mean Reversion — HK Banks',
    'universe': ['0005.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK'],
    'entry_rsi': 30,
    'entry_sma': 20,  # Price > SMA(20)
    'hold_days': 10,
    'transaction_cost': 0.001  # 0.1%
}

# 3-Tier Periods
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'
VALIDATE_START = '2025-01-01'

def fetch_data(ticker):
    """Fetch price data from RDS"""
    query = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '{TRAIN_START}' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_rsi(ticker):
    """Fetch RSI from RDS"""
    query = f"""
    SELECT date, rsi_14 FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '{TRAIN_START}' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def backtest_s001_01(ticker):
    """Backtest S001-01 with REAL RDS data"""
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    
    if prices is None or rsi is None:
        return None
    
    # Merge and calculate SMA20
    df = prices.join(rsi, how='inner')
    df['sma20'] = df['close'].rolling(20).mean()
    
    trades = []
    
    for i in range(20, len(df) - STRATEGY['hold_days']):
        row = df.iloc[i]
        
        # ENTRY: RSI < 30 AND Price > SMA20
        if (pd.notna(row['rsi_14']) and row['rsi_14'] < STRATEGY['entry_rsi'] and
            pd.notna(row['sma20']) and row['close'] > row['sma20']):
            
            entry_price = row['close']
            exit_price = df.iloc[i + STRATEGY['hold_days']]['close']
            
            # Return with transaction cost
            pnl = (exit_price - entry_price) / entry_price * 100 - (STRATEGY['transaction_cost'] * 100)
            
            trades.append({
                'entry_date': df.index[i],
                'exit_date': df.index[i + STRATEGY['hold_days']],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl
            })
    
    if len(trades) < 5:
        return None
    
    trades_df = pd.DataFrame(trades)
    
    # Split into periods
    train_trades = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate_trades = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    
    def calc_metrics(trades_subset):
        if len(trades_subset) < 3:
            return {'trades': 0, 'wr': 0, 'avg_pnl': 0, 'total_pnl': 0}
        wins = (trades_subset['pnl'] > 0).sum()
        wr = wins / len(trades_subset) * 100
        return {
            'trades': len(trades_subset),
            'wr': wr,
            'avg_pnl': trades_subset['pnl'].mean(),
            'total_pnl': trades_subset['pnl'].sum()
        }
    
    return {
        'ticker': ticker,
        'train': calc_metrics(train_trades),
        'test': calc_metrics(test_trades),
        'validate': calc_metrics(validate_trades),
        'all_trades': trades_df
    }

def main():
    print("=" * 90)
    print(f"RE-TEST: {STRATEGY['id']} — {STRATEGY['name']}")
    print(f"Entry: RSI < {STRATEGY['entry_rsi']} AND Price > SMA({STRATEGY['entry_sma']})")
    print(f"Exit: {STRATEGY['hold_days']}-day hold | Cost: {STRATEGY['transaction_cost']*100:.1f}%")
    print(f"Data: REAL RDS (silver.unified_prices + gold.technical_indicators)")
    print("=" * 90)
    
    all_results = []
    
    for ticker in STRATEGY['universe']:
        print(f"\n🧪 Testing {ticker}...")
        result = backtest_s001_01(ticker)
        
        if result is None:
            print(f"  ❌ Insufficient data/signals")
            continue
        
        print(f"  Train ({result['train']['trades']}t): {result['train']['wr']:.1f}% WR")
        print(f"  Test  ({result['test']['trades']}t): {result['test']['wr']:.1f}% WR")
        print(f"  Val   ({result['validate']['trades']}t): {result['validate']['wr']:.1f}% WR")
        
        all_results.append(result)
    
    # Aggregate across universe
    print("\n" + "=" * 90)
    print("STRATEGY-LEVEL AGGREGATION (All 6 Tickers Combined)")
    print("=" * 90)
    
    if all_results:
        all_train = pd.concat([r['all_trades'][(r['all_trades']['entry_date'] >= TRAIN_START) & 
                                               (r['all_trades']['entry_date'] <= TRAIN_END)] for r in all_results])
        all_test = pd.concat([r['all_trades'][(r['all_trades']['entry_date'] >= TEST_START) & 
                                              (r['all_trades']['entry_date'] <= TEST_END)] for r in all_results])
        all_val = pd.concat([r['all_trades'][r['all_trades']['entry_date'] >= VALIDATE_START] for r in all_results])
        
        def agg_metrics(df):
            if len(df) == 0:
                return {'trades': 0, 'wr': 0, 'avg': 0, 'pf': 0}
            wins = (df['pnl'] > 0).sum()
            losses = (df['pnl'] <= 0).sum()
            pf = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if losses > 0 else 999
            return {
                'trades': len(df),
                'wr': wins / len(df) * 100,
                'avg': df['pnl'].mean(),
                'pf': pf
            }
        
        train_m = agg_metrics(all_train)
        test_m = agg_metrics(all_test)
        val_m = agg_metrics(all_val)
        
        print(f"\nTrain 2021-2022: {train_m['trades']} trades, {train_m['wr']:.1f}% WR, PF {train_m['pf']:.2f}")
        print(f"Test 2023-2024:  {test_m['trades']} trades, {test_m['wr']:.1f}% WR, PF {test_m['pf']:.2f}")
        print(f"Validate 2025+:  {val_m['trades']} trades, {val_m['wr']:.1f}% WR, PF {val_m['pf']:.2f}")
        
        decay = abs(train_m['wr'] - test_m['wr'])
        print(f"\nDecay (Train→Test): {decay:.1f}%")
        
        if test_m['wr'] >= 70 and decay <= 20:
            print(f"\n🏆 STATUS: GOLDEN (Test WR {test_m['wr']:.1f}% >= 70%, Decay {decay:.1f}% <= 20%)")
        elif test_m['wr'] >= 55:
            print(f"\n⭐ STATUS: VALIDATED (Test WR {test_m['wr']:.1f}% >= 55%)")
        else:
            print(f"\n❌ STATUS: REJECTED (Test WR {test_m['wr']:.1f}% < 55%)")
    
    conn.close()
    print(f"\n{'='*90}")

if __name__ == '__main__':
    main()
