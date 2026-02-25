#!/usr/bin/env python3
"""
RE-TEST PART 3: Pairs Trading (0700.HK / 9988.HK)
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

TEST_START, TEST_END = '2023-01-01', '2024-12-31'

def fetch_pair_data(ticker1, ticker2):
    """Fetch both tickers"""
    query1 = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker1}' AND date >= '2021-01-01' ORDER BY date
    """
    query2 = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker2}' AND date >= '2021-01-01' ORDER BY date
    """
    
    df1 = pd.read_sql(query1, conn)
    df2 = pd.read_sql(query2, conn)
    
    df1['date'] = pd.to_datetime(df1['date'])
    df2['date'] = pd.to_datetime(df2['date'])
    df1.set_index('date', inplace=True)
    df2.set_index('date', inplace=True)
    
    df1.rename(columns={'close': 'close_1'}, inplace=True)
    df2.rename(columns={'close': 'close_2'}, inplace=True)
    
    # Merge
    df = df1.join(df2, how='inner')
    return df

def test_pairs_trading(ticker1, ticker2):
    """Pairs trading: long underperformer, short outperformer"""
    df = fetch_pair_data(ticker1, ticker2)
    
    if len(df) < 200:
        return None
    
    # Calculate spread
    df['ratio'] = df['close_1'] / df['close_2']
    df['ratio_ma'] = df['ratio'].rolling(20).mean()
    df['ratio_std'] = df['ratio'].rolling(20).std()
    df['z_score'] = (df['ratio'] - df['ratio_ma']) / df['ratio_std']
    
    HOLD_DAYS = 5
    trades = []
    in_position = False
    position_type = None
    entry_date = None
    entry_ratio = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if pd.isna(row['z_score']):
            continue
        
        # Entry
        if not in_position:
            if row['z_score'] > 2.0:  # Spread too high
                in_position = True
                position_type = 'short_spread'
                entry_date = df.index[i]
                entry_ratio = row['ratio']
            elif row['z_score'] < -2.0:  # Spread too low
                in_position = True
                position_type = 'long_spread'
                entry_date = df.index[i]
                entry_ratio = row['ratio']
        
        # Exit
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            exit_signal = abs(row['z_score']) < 0.5 or days_held >= HOLD_DAYS
            
            if exit_signal:
                exit_ratio = row['ratio']
                
                if position_type == 'long_spread':
                    pnl = (exit_ratio - entry_ratio) / entry_ratio * 100
                else:
                    pnl = (entry_ratio - exit_ratio) / entry_ratio * 100
                
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                position_type = None
                entry_date = None
                entry_ratio = None
    
    if len(trades) < 5:
        return None
    
    trades_df = pd.DataFrame(trades)
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    
    if len(test_trades) < 3:
        return None
    
    analytics = BacktestAnalytics()
    metrics = analytics.calculate_metrics(test_trades, hold_days=HOLD_DAYS)
    mc = analytics.monte_carlo_simulation(test_trades, n_simulations=1000, hold_days=HOLD_DAYS)
    
    return {
        'pair': f"{ticker1}/{ticker2}",
        'trades': len(test_trades),
        'wr': metrics['win_rate'],
        'mc_robust': mc['mc_robustness_score'],
        'expectancy': metrics['expectancy']
    }

def main():
    print("=" * 80)
    print("RE-TEST PART 3: Pairs Trading")
    print("=" * 80)
    
    # Test pairs
    pairs = [
        ('0700.HK', '9988.HK'),  # Tencent/Alibaba
        ('JPM', 'BAC'),          # JPM/Bank of America
    ]
    
    results = []
    
    for t1, t2 in pairs:
        print(f"\n🧪 Testing {t1}/{t2}...")
        result = test_pairs_trading(t1, t2)
        
        if result:
            print(f"  Trades: {result['trades']} | WR: {result['wr']:.1f}% | MC: {result['mc_robust']:.1f}%")
            if result['wr'] >= 55 and result['mc_robust'] >= 70:
                print(f"  ⭐ VALIDATED")
                results.append(result)
            elif result['wr'] >= 50:
                print(f"  ⚠️  MARGINAL")
            else:
                print(f"  ❌ WEAK")
        else:
            print(f"  ❌ No results")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ VALIDATED: {len(results)}")
    for r in results:
        print(f"  {r['pair']}: WR {r['wr']:.1f}%, MC {r['mc_robust']:.1f}%")
    
    conn.close()
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
