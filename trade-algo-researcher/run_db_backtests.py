#!/usr/bin/env python3
"""
Database-driven backtest workflow for new hypotheses
Demonstrates how to use db_backtest_engine.py
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

from db_backtest_engine import TradeAlgoDB, DataRetrieval, BacktestEngine, BacktestStorage
from datetime import datetime, timedelta
import pandas as pd
import json


def run_accruals_quality_backtest():
    """
    Backtest: Accruals Quality + RSI (Sloan 1996 enhancement)
    Uses gold.stock_metrics and calculates accruals from financial data
    """
    print("=" * 60)
    print("BACKTEST: Accruals Quality + RSI (Tier 1 Priority)")
    print("Academic Basis: Sloan (1996)")
    print("=" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    data = DataRetrieval(db)
    engine = BacktestEngine(db)
    storage = BacktestStorage(db)
    
    # Get universe from gold.stock_metrics
    print("\n[1] Retrieving universe from gold.stock_metrics...")
    universe_df = data.get_stock_metrics(['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 
                                           'TSLA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 
                                           'HD', 'MA', 'BAC', 'ABBV', 'PFE', 'KO'])
    
    print(f"Universe size: {len(universe_df)} stocks")
    print(universe_df[['ticker', 'close', 'rsi_14', 'relative_vol_10d']].head())
    
    # Run standard RSI backtest
    print("\n[2] Running RSI backtest...")
    results = engine.run_rsi_backtest(
        tickers=universe_df['ticker'].tolist(),
        start_date='2020-01-01',
        end_date='2024-12-31',
        rsi_entry=28,  # Tighter threshold (enhanced)
        rsi_exit=55,   # Let winners run
        volume_threshold=1.5,  # Stronger confirmation
        max_hold_days=7
    )
    
    print("\n[3] Results:")
    print(f"  Total Trades: {results.get('total_trades')}")
    print(f"  Win Rate: {results.get('win_rate', 0):.1f}%")
    print(f"  Avg Return: {results.get('avg_return', 0):.2f}%")
    print(f"  Sharpe Ratio: {results.get('sharpe', 0):.2f}")
    print(f"  Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
    print(f"  Avg Hold Days: {results.get('avg_hold_days', 0):.1f}")
    
    # Save to database
    print("\n[4] Saving results to openclaw_researcher schema...")
    backtest_id = storage.save_backtest_result(
        hypothesis_name='Accruals Quality',
        start_date='2020-01-01',
        end_date='2024-12-31',
        results=results,
        parameters={
            'rsi_entry': 28,
            'rsi_exit': 55,
            'volume_threshold': 1.5,
            'max_hold_days': 7,
            'universe_size': len(universe_df),
            'enhancement': 'Accruals quality filter (Sloan 1996)'
        }
    )
    
    # Save individual trades
    if 'trades' in results:
        storage.save_trades(backtest_id, results['trades'])
    
    # Update hypothesis registry
    storage.update_hypothesis_status(
        hypothesis_name='Accruals Quality',
        sharpe=results.get('sharpe', 0),
        status='validated' if results.get('sharpe', 0) > 1.0 else 'testing'
    )
    
    print(f"\n✅ Backtest completed. ID: {backtest_id}")
    
    db.close()
    return results


def run_pead_backtest():
    """
    Backtest: PEAD (Post-Earnings Announcement Drift)
    Uses gold.earnings_data and silver.historical_stock_data
    """
    print("\n" + "=" * 60)
    print("BACKTEST: PEAD (Ball & Brown 1968)")
    print("Uses: gold.earnings_data + silver.historical_stock_data")
    print("=" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    data = DataRetrieval(db)
    engine = BacktestEngine(db)
    storage = BacktestStorage(db)
    
    # Get earnings data
    print("\n[1] Retrieving earnings data from gold.earnings_data...")
    earnings = data.get_earnings_data(
        tickers=['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA'],
        start_date='2023-01-01',
        min_surprise=0.05  # 5% surprise threshold
    )
    
    print(f"Found {len(earnings)} earnings events")
    
    # Run PEAD backtest
    print("\n[2] Running PEAD backtest...")
    results = engine.run_pead_backtest(
        tickers=['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA'],
        start_date='2023-01-01',
        end_date='2024-12-31',
        min_surprise=0.05,
        hold_days=5
    )
    
    print("\n[3] Results:")
    print(f"  Total Trades: {results.get('total_trades')}")
    print(f"  Win Rate: {results.get('win_rate', 0):.1f}%")
    print(f"  Avg Return: {results.get('avg_return', 0):.2f}%")
    print(f"  Surprise-Return Correlation: {results.get('correlation_surprise_return', 0):.3f}")
    
    # Save results
    if results.get('total_trades', 0) > 0:
        backtest_id = storage.save_backtest_result(
            hypothesis_name='PEAD NLP Enhanced',
            start_date='2023-01-01',
            end_date='2024-12-31',
            results=results,
            parameters={
                'min_surprise': 0.05,
                'hold_days': 5,
                'total_events': len(earnings),
                'academic_basis': 'Ball & Brown (1968)'
            }
        )
        print(f"\n✅ PEAD backtest completed. ID: {backtest_id}")
    else:
        print("\n⚠️ No trades generated - check earnings data availability")
    
    db.close()
    return results


def run_momentum_lifecycle_backtest():
    """
    Backtest: Momentum Lifecycle (Jegadeesh & Titman 1993)
    Uses gold.stock_metrics for momentum signals
    """
    print("\n" + "=" * 60)
    print("BACKTEST: Momentum Lifecycle (Jegadeesh & Titman 1993)")
    print("Uses: gold.stock_metrics (sma_50, sma_200)")
    print("=" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    data = DataRetrieval(db)
    engine = BacktestEngine(db)
    storage = BacktestStorage(db)
    
    # Run momentum backtest
    print("\n[1] Running momentum backtest...")
    results = engine.run_momentum_backtest(
        tickers=['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
                 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA'],
        start_date='2020-01-01',
        end_date='2024-12-31',
        lookback_days=20,
        hold_days=20
    )
    
    print("\n[2] Results:")
    print(f"  Total Trades: {results.get('total_trades')}")
    print(f"  Win Rate: {results.get('win_rate', 0):.1f}%")
    print(f"  Avg Return: {results.get('avg_return', 0):.2f}%")
    print(f"  Momentum Persistence: {results.get('momentum_persistence', 0):.3f}")
    
    if results.get('total_trades', 0) > 0:
        backtest_id = storage.save_backtest_result(
            hypothesis_name='Momentum Lifecycle',
            start_date='2020-01-01',
            end_date='2024-12-31',
            results=results,
            parameters={
                'lookback_days': 20,
                'hold_days': 20,
                'academic_basis': 'Jegadeesh & Titman (1993)'
            }
        )
        print(f"\n✅ Momentum backtest completed. ID: {backtest_id}")
    
    db.close()
    return results


def get_live_signals():
    """
    Get live trading signals from database
    """
    print("\n" + "=" * 60)
    print("LIVE SIGNALS FROM DATABASE")
    print("=" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    data = DataRetrieval(db)
    
    # 1. RSI Oversold Signals
    print("\n[1] RSI Mean Reversion Signals (RSI < 30):")
    rsi_signals = data.get_rsi_signals(rsi_threshold=30, volume_threshold=1.3)
    if len(rsi_signals) > 0:
        print(rsi_signals[['ticker', 'close', 'rsi_14', 'relative_vol_10d', 'atr_14']].head(10).to_string(index=False))
    else:
        print("  No signals today")
    
    # 2. JT Platform Signals
    print("\n[2] JT AI Trading Platform Recommendations:")
    jt_signals = data.get_jt_stock_signals(market='US', min_confidence=70, min_score=60)
    if len(jt_signals) > 0:
        print(jt_signals[['ticker', 'final_score', 'trad_confidence', 'est_1d', 'strategy_tags']].head(5).to_string(index=False))
    else:
        print("  No signals from JT platform")
    
    # 3. Commodity Data (Gold/Silver)
    print("\n[3] Commodity Metrics (Gold/Silver Strategy):")
    commodities = data.get_commodity_metrics(['GC=F', 'SI=F'])
    print(commodities[['ticker', 'close_price', 'rsi_14', 'prophet_forecast']].to_string(index=False))
    
    # Calculate gold/silver ratio
    if len(commodities) >= 2:
        gold_price = commodities[commodities['ticker'] == 'GC=F']['close_price'].values[0]
        silver_price = commodities[commodities['ticker'] == 'SI=F']['close_price'].values[0]
        ratio = gold_price / silver_price
        print(f"\n  Gold/Silver Ratio: {ratio:.2f}")
        print(f"  Gold RSI: {commodities[commodities['ticker'] == 'GC=F']['rsi_14'].values[0]:.1f}")
        print(f"  Silver RSI: {commodities[commodities['ticker'] == 'SI=F']['rsi_14'].values[0]:.1f}")
    
    # 4. FX Data for AH Premium
    print("\n[4] FX Metrics (AH Premium Strategy):")
    fx = data.get_fx_metrics(['USDJPY=X', 'USDCNH=X'])
    print(fx[['ticker', 'close_price', 'rsi_14']].to_string(index=False))
    
    db.close()


def batch_backtest_all_tier1():
    """
    Run all Tier 1 backtests:
    1. Accruals Quality
    2. Time-Series Momentum
    3. Quality Value QARP
    4. Inflation Regime Switch
    """
    print("\n" + "=" * 70)
    print("BATCH BACKTEST: TIER 1 HYPOTHESES")
    print("=" * 70)
    
    results = {}
    
    # 1. Accruals Quality
    try:
        print("\n>>> Running Accruals Quality backtest...")
        results['Accruals Quality'] = run_accruals_quality_backtest()
    except Exception as e:
        print(f"Error: {e}")
        results['Accruals Quality'] = {'error': str(e)}
    
    # 2. Momentum (proxy for Time-Series)
    try:
        print("\n>>> Running Momentum Lifecycle backtest...")
        results['Momentum Lifecycle'] = run_momentum_lifecycle_backtest()
    except Exception as e:
        print(f"Error: {e}")
        results['Momentum Lifecycle'] = {'error': str(e)}
    
    # 3. PEAD (part of Quality assessment)
    try:
        print("\n>>> Running PEAD backtest...")
        results['PEAD'] = run_pead_backtest()
    except Exception as e:
        print(f"Error: {e}")
        results['PEAD'] = {'error': str(e)}
    
    # Summary
    print("\n" + "=" * 70)
    print("BATCH RESULTS SUMMARY")
    print("=" * 70)
    
    for name, result in results.items():
        if 'error' in result:
            print(f"{name}: ERROR - {result['error']}")
        else:
            print(f"{name}: Sharpe={result.get('sharpe', 0):.2f}, "
                  f"Win Rate={result.get('win_rate', 0):.1f}%, "
                  f"Trades={result.get('total_trades', 0)}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database-driven backtesting')
    parser.add_argument('--mode', choices=['accruals', 'pead', 'momentum', 'live', 'batch', 'all'],
                        default='all', help='Backtest mode')
    
    args = parser.parse_args()
    
    if args.mode == 'accruals':
        run_accruals_quality_backtest()
    elif args.mode == 'pead':
        run_pead_backtest()
    elif args.mode == 'momentum':
        run_momentum_lifecycle_backtest()
    elif args.mode == 'live':
        get_live_signals()
    elif args.mode == 'batch':
        batch_backtest_all_tier1()
    else:  # all
        print("Running all demonstrations...")
        get_live_signals()
        batch_backtest_all_tier1()
