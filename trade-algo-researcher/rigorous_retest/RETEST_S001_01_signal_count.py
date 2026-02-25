#!/usr/bin/env python3
"""
RE-TEST S001-01 WITH RELAXED CRITERIA
Test RSI < 35 (no SMA filter) vs RSI < 30 (with SMA filter)
"""

import pandas as pd
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

db = TradeAlgoDB()
conn = db.connect()

TICKERS = ['0005.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK']
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

def test_variants(ticker):
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    
    if prices is None or rsi is None:
        return None
    
    df = prices.join(rsi, how='inner')
    df['sma20'] = df['close'].rolling(20).mean()
    
    # Count signals for different criteria
    signals = {
        'RSI < 30': len(df[df['rsi_14'] < 30]),
        'RSI < 35': len(df[df['rsi_14'] < 35]),
        'RSI < 30 + Price > SMA20': len(df[(df['rsi_14'] < 30) & (df['close'] > df['sma20'])]),
        'RSI < 35 + Price > SMA20': len(df[(df['rsi_14'] < 35) & (df['close'] > df['sma20'])]),
    }
    
    return {'ticker': ticker, 'signals': signals}

print("=" * 80)
print("S001-01 SIGNAL COUNT ANALYSIS")
print("Testing different entry criteria on REAL data")
print("=" * 80)

all_results = []
for ticker in TICKERS:
    result = test_variants(ticker)
    if result:
        all_results.append(result)
        print(f"\n{ticker}:")
        for criteria, count in result['signals'].items():
            print(f"  {criteria}: {count} signals")

# Summary
print("\n" + "=" * 80)
print("SUMMARY: Total Signals Across Universe (6 tickers, ~5 years)")
print("=" * 80)

totals = {}
for criteria in ['RSI < 30', 'RSI < 35', 'RSI < 30 + Price > SMA20', 'RSI < 35 + Price > SMA20']:
    total = sum(r['signals'][criteria] for r in all_results)
    totals[criteria] = total
    print(f"  {criteria}: {total} total signals")

print(f"\n{'='*80}")
print("CONCLUSION:")
print(f"  Original S001-01 (RSI<30 + SMA20): {totals['RSI < 30 + Price > SMA20']} signals")
print(f"  → TOO SELECTIVE — {totals['RSI < 30 + Price > SMA20']/6:.1f} signals per ticker in 5 years!")
print(f"\n  RELAXED (RSI<35, no SMA): {totals['RSI < 35']} signals")
print(f"  → USABLE — {totals['RSI < 35']/6:.1f} signals per ticker")
print(f"{'='*80}")

conn.close()
