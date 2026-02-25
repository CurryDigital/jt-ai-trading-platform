#!/usr/bin/env python3
"""
ARASO Backtest Runner
Executes 5-year backtest and validates against Sharpe target

Usage:
    python run_backtest.py --db-user USER --db-pass PASS
    
Output:
    - Console report
    - results/araso_backtest_YYYYMMDD.json
    - results/araso_equity_curve.csv
"""

import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / 'strategies'))

from araso_backtest import ARASOBacktester, BacktestConfig

def run_full_backtest(db_user, db_pass, db_host="openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com"):
    """Execute complete ARASO backtest."""
    
    print("=" * 70)
    print("ARASO STRATEGY BACKTEST")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database connection
    from araso_factor_model import DatabaseConnector
    
    print("🔌 Connecting to database...")
    db = DatabaseConnector(
        host=db_host,
        username=db_user,
        password=db_pass
    )
    db.connect()
    print("✅ Connected")
    print()
    
    # Universe selection
    # Focus on tech/SaaS for Information Arbitrage thesis
    universe = [
        # Core tech
        'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
        # SaaS vulnerable to AI disruption
        'ADBE', 'ADSK', 'INTU', 'CRM', 'NOW', 'TEAM', 'SNOW', 'ZM', 'DDOG',
        # GPU supply chain
        'VRT', 'FN', 'AMAT', 'LRCX', 'KLAC', 'SNPS', 'CDNS',
        # Hardware
        'AMD', 'INTC', 'QCOM', 'MU', 'STX', 'WDC',
    ]
    
    print(f"📊 Universe: {len(universe)} stocks")
    print(f"   Focus: Tech/SaaS for Information Arbitrage validation")
    print()
    
    # Configuration
    config = BacktestConfig(
        start_date=datetime(2019, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=1_000_000,
        rebalance_freq=5,  # Weekly
        transaction_cost=0.001,  # 10bps
        max_positions=20,
        entry_zscore=1.5,
        exit_zscore=0.3,
        hmm_threshold=0.7
    )
    
    print("⚙️  Configuration:")
    print(f"   Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"   Initial Capital: ${config.initial_capital:,.0f}")
    print(f"   Rebalance: Every {config.rebalance_freq} days")
    print(f"   Transaction Cost: {config.transaction_cost*100:.0f}bps")
    print()
    
    # Run backtest
    print("🚀 Running backtest...")
    print("   (This may take 5-10 minutes)")
    print()
    
    backtester = ARASOBacktester(db, config)
    results = backtester.run_backtest(universe)
    
    # Print report
    backtester.print_report(results)
    
    # Save results
    print("\n💾 Saving results...")
    
    # Create results directory
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # Save JSON report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = results_dir / f'araso_backtest_{timestamp}.json'
    backtester.save_results(results, filename=json_file.name)
    
    # Save equity curve CSV
    if backtester.portfolio_history:
        equity_df = pd.DataFrame([
            {
                'date': p.date,
                'total_value': p.total_value,
                'daily_return': p.daily_return,
                'cash': p.cash
            }
            for p in backtester.portfolio_history
        ])
        equity_file = results_dir / f'araso_equity_curve_{timestamp}.csv'
        equity_df.to_csv(equity_file, index=False)
        print(f"   Equity curve: {equity_file}")
    
    # Save trades CSV
    if backtester.trades:
        trades_df = pd.DataFrame([
            {
                'ticker': t.ticker,
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'direction': 'Long' if t.direction == 1 else 'Short',
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'pnl': t.pnl,
                'exit_reason': t.exit_reason
            }
            for t in backtester.trades if t.pnl is not None
        ])
        trades_file = results_dir / f'araso_trades_{timestamp}.csv'
        trades_df.to_csv(trades_file, index=False)
        print(f"   Trades: {trades_file}")
    
    print()
    print("=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)
    
    # Validation against targets
    print("\n🎯 TARGET VALIDATION:")
    
    target_sharpe = 2.1
    actual_sharpe = results.get('sharpe_ratio', 0)
    
    target_dd = 0.12
    actual_dd = abs(results.get('max_drawdown', 0))
    
    print(f"   Sharpe Ratio:")
    print(f"     Target: {target_sharpe:.1f}")
    print(f"     Actual: {actual_sharpe:.2f}")
    print(f"     Status: {'✅ PASS' if actual_sharpe >= target_sharpe else '❌ FAIL'}")
    
    print(f"   Max Drawdown:")
    print(f"     Target: <{target_dd*100:.0f}%")
    print(f"     Actual: {actual_dd*100:.1f}%")
    print(f"     Status: {'✅ PASS' if actual_dd <= target_dd else '❌ FAIL'}")
    
    # Decision
    print("\n📋 NEXT STEPS:")
    if actual_sharpe >= target_sharpe and actual_dd <= target_dd:
        print("   ✅ Strategy meets targets")
        print("   ➡️  Move to 'paper' status")
        print("   ➡️  Deploy on JT platform in SIMULATION mode")
        print("   ➡️  30-day paper trading validation")
    else:
        print("   ⚠️  Strategy needs refinement")
        print("   ➡️  Debug factor model parameters")
        print("   ➡️  Review HMM thresholds")
        print("   ➡️  Consider universe selection")
    
    print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Run ARASO Backtest')
    parser.add_argument('--db-user', type=str, required=True,
                       help='Database username')
    parser.add_argument('--db-pass', type=str, required=True,
                       help='Database password')
    parser.add_argument('--db-host', type=str, 
                       default='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
                       help='Database host')
    
    args = parser.parse_args()
    
    try:
        results = run_full_backtest(
            db_user=args.db_user,
            db_pass=args.db_pass,
            db_host=args.db_host
        )
        
        # Exit code based on validation
        sharpe = results.get('sharpe_ratio', 0)
        dd = abs(results.get('max_drawdown', 0))
        
        if sharpe >= 2.1 and dd <= 0.12:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Needs work
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
