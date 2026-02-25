#!/usr/bin/env python3
"""
RE-TEST PART 6: SG Tickers with RSI < 35
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
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_rsi(ticker):
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

def test_sg_rsi(ticker):
    """Test RSI < 35 on SG tickers"""
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    
    if prices is None or rsi is None:
        return None
    
    df = prices.join(rsi, how='inner')
    
    HOLD_DAYS = 10
    trades = []
    in_position = False
    entry_date = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['rsi_14'] < 35 and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - df.loc[entry_date, 'close']) / df.loc[entry_date, 'close'] * 100
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                entry_date = None
    
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
        'ticker': ticker,
        'trades': len(test_trades),
        'wr': metrics['win_rate'],
        'mc_robust': mc['mc_robustness_score'],
    }

def main():
    print("=" * 80)
    print("RE-TEST PART 6: SG Tickers (RSI < 35)")
    print("=" * 80)
    
    sg_tickers = [
        'D05.SI', 'O39.SI', 'U11.SI',  # Banks
        'Z74.SI', 'G13.SI', 'C6L.SI',  # Others
        'C38U.SI', 'A17U.SI', 'N2IU.SI', 'ME8U.SI',  # REITs
    ]
    
    results = []
    
    for ticker in sg_tickers:
        print(f"\n🧪 Testing {ticker}...")
        result = test_sg_rsi(ticker)
        
        if result:
            print(f"  Trades={result['trades']}, WR={result['wr']:.1f}%, MC={result['mc_robust']:.1f}%")
            if result['wr'] >= 55 and result['mc_robust'] >= 70:
                print(f"  ⭐ VALIDATED")
                results.append(result)
            elif result['wr'] >= 50:
                print(f"  ⚠️  MARGINAL")
        else:
            print(f"  ❌ No results (insufficient data)")
    
    print("\n" + "=" * 80)
    print(f"✅ VALIDATED SG TICKERS: {len(results)}")
    for r in results:
        print(f"  {r['ticker']}: WR {r['wr']:.1f}%, MC {r['mc_robust']:.1f}%")
    
    conn.close()
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
