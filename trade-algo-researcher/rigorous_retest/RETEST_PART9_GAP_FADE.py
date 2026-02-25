#!/usr/bin/env python3
"""
RE-TEST PART 9: Gap Fade Strategy
Fade overnight gaps > 2%
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
MIN_TRADES = 20

def fetch_data(ticker):
    query = f"""
    SELECT date, open, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_gap_fade(ticker):
    """Gap Fade: Gap down > 2%, buy at open, sell at close"""
    df = fetch_data(ticker)
    if df is None or len(df) < 100:
        return None
    
    # Calculate gap
    df['prev_close'] = df['close'].shift(1)
    df['gap_pct'] = (df['open'] - df['prev_close']) / df['prev_close'] * 100
    
    # Signal: Gap down > 2%
    df['signal'] = df['gap_pct'] < -2.0
    
    HOLD_DAYS = 1  # Intraday
    trades = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        if row['signal'] and not pd.isna(row['open']) and not pd.isna(row['close']):
            pnl = (row['close'] - row['open']) / row['open'] * 100
            trades.append({'entry_date': df.index[i], 'exit_date': df.index[i], 'pnl': pnl})
    
    if len(trades) < MIN_TRADES:
        return None
    
    trades_df = pd.DataFrame(trades)
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    
    if len(test_trades) < 10:
        return None
    
    analytics = BacktestAnalytics()
    metrics = analytics.calculate_metrics(test_trades, hold_days=HOLD_DAYS)
    mc = analytics.monte_carlo_simulation(test_trades, n_simulations=1000, hold_days=HOLD_DAYS)
    
    return {
        'ticker': ticker,
        'trades': len(test_trades),
        'wr': metrics['win_rate'],
        'mc_robust': mc['mc_robustness_score'],
    }

def main():
    print("=" * 80)
    print(f"RE-TEST PART 9: Gap Fade Strategy (Minimum {MIN_TRADES} trades)")
    print("=" * 80)
    
    tickers = [
        '0700.HK', '9988.HK', '1398.HK', '2388.HK', '0005.HK', '0001.HK',
        'PLTR', 'AMD', 'NVDA', 'TSLA', 'META', 'NFLX', 'COIN',
        'MSFT', 'AAPL', 'GOOGL', 'AMZN',
        'SPY', 'QQQ', 'IWM',
    ]
    
    results = []
    
    for ticker in tickers:
        print(f"\n🧪 Testing {ticker}...")
        result = test_gap_fade(ticker)
        
        if result:
            status = "⭐ VALIDATED" if result['wr'] >= 55 and result['mc_robust'] >= 70 else "⚠️  MARGINAL" if result['wr'] >= 50 else ""
            print(f"  Trades={result['trades']}, WR={result['wr']:.1f}%, MC={result['mc_robust']:.1f}% {status}")
            if result['wr'] >= 55 and result['mc_robust'] >= 70:
                results.append(result)
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
