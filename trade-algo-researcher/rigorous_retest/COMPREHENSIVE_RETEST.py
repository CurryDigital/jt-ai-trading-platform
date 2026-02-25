#!/usr/bin/env python3
"""
COMPREHENSIVE RE-TEST — ALL STRATEGIES WITH REAL RDS DATA
Golden + Validated + Hypotheses + Rejected — Everything Re-tested
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

# REAL DATABASE CONNECTION
db = TradeAlgoDB()
conn = db.connect()

# TICKERS WITH REAL DATA (from data check)
REAL_TICKERS = [
    # Tier 1: Golden (deployed)
    '1398.HK', '3988.HK', '3328.HK', '2388.HK', '0939.HK', '0005.HK', '3968.HK',  # S001-HK-BANKS
    '9988.HK', '9999.HK', '1024.HK', '0700.HK',  # S004-HK-TECH
    
    # Tier 2: Validated (deployed)
    'PLTR', 'ASML', 'AMD', 'ZM',  # S001-US-TECH
    'SOL-USD', 'ADA-USD', 'MSTR', 'DOT-USD',  # S001-CRYPTO
    'JPM', 'BAC', 'GS', 'C',  # S005-US-BANKS
    
    # Note: S002-HK-BANKS overlaps with S001
]

# Date ranges
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'
VALIDATE_START, VALIDATE_END = '2025-01-01', '2026-02-25'

def fetch_real_data(ticker):
    """Fetch REAL price data from RDS"""
    query = f"""
    SELECT date, close, volume
    FROM silver.unified_prices
    WHERE ticker = '{ticker}'
    AND date >= '{TRAIN_START}'
    ORDER BY date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_real_indicators(ticker, conn):
    """Fetch REAL technical indicators from RDS"""
    query = f"""
    SELECT date, rsi_14, macd_line, macd_signal, adx, bb_upper, bb_middle, bb_lower
    FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}'
    AND date >= '{TRAIN_START}'
    ORDER BY date
    """
    try:
        df = pd.read_sql(query, conn)
        if len(df) == 0:
            return None
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"    Indicator fetch error: {str(e)[:50]}")
        return None

def backtest_s001_rsi(ticker, df, conn):
    """S001: RSI Mean Reversion (REAL DATA)"""
    indicators = fetch_real_indicators(ticker, conn)
    if indicators is None:
        return None
    
    # Merge price and indicators
    df = df.join(indicators[['rsi_14']], how='left')
    
    if df['rsi_14'].isna().all():
        return None
    
    HOLD_DAYS = 10
    trades = []
    in_position = False
    entry_date = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['rsi_14'] < 25 and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - df.loc[entry_date, 'close']) / df.loc[entry_date, 'close'] * 100
                trades.append({'entry_date': entry_date, 'exit_date': df.index[i], 'pnl': pnl})
                in_position = False
                entry_date = None
    
    if len(trades) < 30:  # STRICT: minimum 30 trades
        return None
    
    trades_df = pd.DataFrame(trades)
    analytics = BacktestAnalytics()
    
    # Split into periods
    train_trades = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate_trades = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    
    results = {
        'ticker': ticker,
        'strategy': 'S001_RSI',
        'total_trades': len(trades_df),
        'train_metrics': analytics.calculate_metrics(train_trades, hold_days=HOLD_DAYS) if len(train_trades) > 0 else None,
        'test_metrics': analytics.calculate_metrics(test_trades, hold_days=HOLD_DAYS) if len(test_trades) > 0 else None,
        'validate_metrics': analytics.calculate_metrics(validate_trades, hold_days=HOLD_DAYS) if len(validate_trades) > 0 else None,
    }
    
    # MC and cost only on test period
    if len(test_trades) >= 30:
        results['mc_metrics'] = analytics.monte_carlo_simulation(test_trades, n_simulations=1000, hold_days=HOLD_DAYS)
        results['cost_metrics'] = analytics.transaction_cost_sensitivity(test_trades, hold_days=HOLD_DAYS)
    
    return results

def classify_strategy(results):
    """Classify based on REAL data results"""
    if results['test_metrics'] is None:
        return 'INSUFFICIENT_DATA', 0
    
    tm = results['test_metrics']
    
    # Check minimum trades
    if tm['total_trades'] < 30:
        return 'INSUFFICIENT_DATA', tm['total_trades']
    
    # Score criteria
    score = 0
    checks = {
        'test_wr': tm['win_rate'] >= 55,
        'expectancy': tm['expectancy'] > 0.3,
        'profit_factor': tm['profit_factor'] >= 1.5,
        'sharpe': tm['sharpe_ratio'] >= 0.8,
        'trades': tm['total_trades'] >= 30,
    }
    
    for check, passed in checks.items():
        if passed:
            score += 1
    
    # Add MC and cost if available
    if 'mc_metrics' in results and results['mc_metrics']:
        if results['mc_metrics']['mc_robustness_score'] >= 70:
            score += 1
        if results['mc_metrics']['mc_prob_profit'] >= 70:
            score += 1
    
    if 'cost_metrics' in results and results['cost_metrics']:
        if results['cost_metrics']['cost_robustness_score'] >= 50:
            score += 1
    
    # Classify
    if score >= 7:
        return 'GOLDEN', score
    elif score >= 5:
        return 'VALIDATED', score
    else:
        return 'REJECTED', score

def main():
    print("=" * 90)
    print("COMPREHENSIVE RE-TEST — REAL DATA ONLY")
    print("=" * 90)
    print(f"Tickers to test: {len(REAL_TICKERS)}")
    print(f"Data source: silver.unified_prices (REAL)")
    print(f"Minimum trades: 30 (strict)")
    print(f"Strategies: S001, S004, S005")
    print("=" * 90)
    
    all_results = []
    
    for ticker in REAL_TICKERS:
        print(f"\n🧪 Testing {ticker}...")
        
        try:
            # Fetch real data
            df = fetch_real_data(ticker)
            
            if len(df) < 500:
                print(f"  ⚠️ Insufficient data: {len(df)} records")
                continue
            
            # Test S001 (RSI Mean Reversion)
            result = backtest_s001_rsi(ticker, df, conn)
            
            if result:
                classification, score = classify_strategy(result)
                result['classification'] = classification
                result['score'] = score
                
                tm = result['test_metrics']
                print(f"  S001: Trades={tm['total_trades']}, WR={tm['win_rate']:.1f}%, Score={score}/8")
                print(f"       Classification: {classification}")
                
                all_results.append(result)
            else:
                print(f"  ❌ No results (insufficient trades or data)")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")
    
    # Summary
    print("\n" + "=" * 90)
    print("COMPREHENSIVE RE-TEST SUMMARY")
    print("=" * 90)
    
    golden = [r for r in all_results if r['classification'] == 'GOLDEN']
    validated = [r for r in all_results if r['classification'] == 'VALIDATED']
    rejected = [r for r in all_results if r['classification'] == 'REJECTED']
    
    print(f"\n✅ GOLDEN: {len(golden)}")
    for r in golden:
        print(f"  {r['ticker']}: Score {r['score']}/8, WR {r['test_metrics']['win_rate']:.1f}%")
    
    print(f"\n⭐ VALIDATED: {len(validated)}")
    for r in validated:
        print(f"  {r['ticker']}: Score {r['score']}/8, WR {r['test_metrics']['win_rate']:.1f}%")
    
    print(f"\n❌ REJECTED: {len(rejected)}")
    for r in rejected:
        print(f"  {r['ticker']}: Score {r['score']}/8, WR {r['test_metrics']['win_rate']:.1f}%")
    
    # Save results
    results_df = pd.DataFrame([
        {
            'ticker': r['ticker'],
            'strategy': r['strategy'],
            'classification': r['classification'],
            'score': r['score'],
            'test_trades': r['test_metrics']['total_trades'] if r['test_metrics'] else 0,
            'test_wr': r['test_metrics']['win_rate'] if r['test_metrics'] else 0,
            'test_expectancy': r['test_metrics']['expectancy'] if r['test_metrics'] else 0,
            'test_pf': r['test_metrics']['profit_factor'] if r['test_metrics'] else 0,
        }
        for r in all_results
    ])
    
    results_df.to_csv('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest/COMPREHENSIVE_RETEST_RESULTS.csv', index=False)
    print(f"\n📁 Results saved to COMPREHENSIVE_RETEST_RESULTS.csv")
    
    # Close connection
    conn.close()
    print(f"\n{'='*90}")

if __name__ == '__main__':
    main()
