#!/usr/bin/env python3
"""
RE-TEST PART 2: Other Strategies (Not RSI)
H015-014 MACD + Trend, H015-012 Pairs, H015-009 FX
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
from backtest_analytics import BacktestAnalytics

# Connect to DB
db = TradeAlgoDB()
conn = db.connect()

# Test periods
TEST_START, TEST_END = '2023-01-01', '2024-12-31'

def fetch_prices(ticker):
    """Fetch real price data"""
    query = f"""
    SELECT date, close
    FROM silver.unified_prices
    WHERE ticker = '{ticker}'
    AND date >= '2021-01-01'
    ORDER BY date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    """Fetch real indicators"""
    query = f"""
    SELECT date, macd_line, macd_signal, adx
    FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}'
    AND date >= '2021-01-01'
    ORDER BY date
    """
    try:
        df = pd.read_sql(query, conn)
        if len(df) == 0:
            return None
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except:
        return None

def test_macd_trend(ticker):
    """H015-014: MACD + Trend Filter"""
    prices = fetch_prices(ticker)
    indicators = fetch_indicators(ticker)
    
    if prices is None or indicators is None or len(prices) < 100:
        return None
    
    # Merge
    df = prices.join(indicators, how='inner')
    df['sma50'] = df['close'].rolling(50).mean()
    
    # Signal: MACD cross above signal AND price > SMA50 AND ADX > 25
    df['macd_cross'] = (df['macd_line'] > df['macd_signal']) & (df['macd_line'].shift(1) <= df['macd_signal'].shift(1))
    df['signal'] = df['macd_cross'] & (df['close'] > df['sma50']) & (df['adx'] > 25)
    
    HOLD_DAYS = 10
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
    
    if len(trades) < 10:  # Relaxed for this test
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
        'strategy': 'MACD_Trend',
        'trades': len(test_trades),
        'wr': metrics['win_rate'],
        'mc_robust': mc['mc_robustness_score'],
        'expectancy': metrics['expectancy']
    }

def main():
    print("=" * 80)
    print("RE-TEST PART 2: MACD + Trend Strategy")
    print("=" * 80)
    
    # Test tickers with data
    tickers = [
        '0700.HK', '9988.HK', '1398.HK', '2388.HK',  # HK
        'PLTR', 'AMD', 'NVDA',  # US
        'D05.SI', 'O39.SI', 'U11.SI'  # SG
    ]
    
    results = []
    
    for ticker in tickers:
        print(f"\n🧪 Testing {ticker}...")
        result = test_macd_trend(ticker)
        
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
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ VALIDATED: {len(results)}")
    for r in results:
        print(f"  {r['ticker']}: WR {r['wr']:.1f}%, MC {r['mc_robust']:.1f}%")
    
    conn.close()
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
