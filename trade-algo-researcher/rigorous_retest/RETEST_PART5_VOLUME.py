#!/usr/bin/env python3
"""
RE-TEST PART 5: Volume + Breakout Strategies
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

def fetch_data(ticker):
    query = f"""
    SELECT date, close, volume FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_volume_breakout(ticker):
    """Volume > 2x average + price breakout"""
    df = fetch_data(ticker)
    if len(df) < 100:
        return None
    
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma20']
    df['high_20'] = df['close'].rolling(20).max()
    
    # Signal: Volume > 2x AND break above 20-day high
    df['signal'] = (df['volume_ratio'] > 2.0) & (df['close'] > df['high_20'].shift(1))
    
    HOLD_DAYS = 5
    trades = []
    in_position = False
    entry_date = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['signal'] and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - df.loc[entry_date, 'close']) / df.loc[entry_date, 'close'] * 100
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                entry_date = None
    
    if len(trades) < 10:
        return None
    
    trades_df = pd.DataFrame(trades)
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    
    if len(test_trades) < 5:
        return None
    
    analytics = BacktestAnalytics()
    metrics = analytics.calculate_metrics(test_trades, hold_days=HOLD_DAYS)
    mc = analytics.monte_carlo_simulation(test_trades, n_simulations=1000, hold_days=HOLD_DAYS)
    
    return {
        'ticker': ticker,
        'strategy': 'Volume_Breakout',
        'trades': len(test_trades),
        'wr': metrics['win_rate'],
        'mc_robust': mc['mc_robustness_score'],
        'expectancy': metrics['expectancy']
    }

def main():
    print("=" * 80)
    print("RE-TEST PART 5: Volume + Breakout")
    print("=" * 80)
    
    tickers = [
        '0700.HK', '9988.HK', '1398.HK', '2388.HK',
        'PLTR', 'AMD', 'NVDA', 'TSLA',
        'SOL-USD', 'BTC-USD',
    ]
    
    results = []
    
    for ticker in tickers:
        print(f"\n🧪 Testing {ticker}...")
        result = test_volume_breakout(ticker)
        
        if result:
            print(f"  Trades={result['trades']}, WR={result['wr']:.1f}%, MC={result['mc_robust']:.1f}%")
            if result['wr'] >= 55 and result['mc_robust'] >= 70:
                print(f"  ⭐ VALIDATED")
                results.append(result)
            elif result['wr'] >= 50:
                print(f"  ⚠️  MARGINAL")
        else:
            print(f"  ❌ No results")
    
    print("\n" + "=" * 80)
    print(f"✅ VALIDATED: {len(results)}")
    for r in results:
        print(f"  {r['ticker']}: WR {r['wr']:.1f}%, MC {r['mc_robust']:.1f}%")
    
    conn.close()
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
