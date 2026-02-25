#!/usr/bin/env python3
"""
Backtest: Singapore Banking Yield Spread Strategy
Tests DBS, OCBC, UOB performance during rate hike cycles
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_db_connection():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    token = rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432, DBUsername='openclaw_user', Region='ap-southeast-1'
    )
    return psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432, database='aitrading', user='openclaw_user',
        password=token, sslmode='require'
    )


def save_backtest_result(hypothesis_name, results, params, start_date, end_date, trades_df=None):
    import json as json_lib
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total_trades = int(results.get('total_trades', 0))
    win_rate = float(results.get('win_rate', 0)) if results.get('win_rate') else None
    sharpe = float(results.get('sharpe', 0)) if results.get('sharpe') else None
    max_dd = float(results.get('max_drawdown', 0)) if results.get('max_drawdown') else None
    
    params_json = json_lib.dumps(params)
    
    cursor.execute("""
    SELECT id FROM openclaw_researcher.backtest_results 
    WHERE hypothesis_name = %s AND start_date = %s AND end_date = %s
    """, (hypothesis_name, start_date, end_date))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
        UPDATE openclaw_researcher.backtest_results 
        SET total_trades = %s, win_rate_pct = %s, sharpe_ratio = %s, 
            max_drawdown_pct = %s, status = %s, parameters = %s, notes = %s, 
            created_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id
        """, (total_trades, win_rate, sharpe, max_dd, 'completed', 
              params_json, 'SG Banking backtest', existing[0]))
    else:
        cursor.execute("""
        INSERT INTO openclaw_researcher.backtest_results 
        (hypothesis_name, start_date, end_date, total_trades, win_rate_pct,
         sharpe_ratio, max_drawdown_pct, status, parameters, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (hypothesis_name, start_date, end_date, total_trades, win_rate,
              sharpe, max_dd, 'completed', params_json, 'SG Banking backtest'))
    
    backtest_id = cursor.fetchone()[0]
    
    if sharpe and sharpe >= 1.0:
        status = 'validated'
    elif sharpe and sharpe > 0:
        status = 'testing'
    else:
        status = 'rejected'
    
    cursor.execute("""
    UPDATE openclaw_researcher.hypothesis_registry
    SET backtest_count = backtest_count + 1,
        best_sharpe = GREATEST(COALESCE(best_sharpe, -999), %s),
        last_backtest_date = CURRENT_DATE,
        current_status = %s
    WHERE hypothesis_name = %s
    """, (sharpe if sharpe else -999, status, hypothesis_name))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return backtest_id, status


def backtest_sg_banking():
    """Backtest Singapore Banking Yield Spread Strategy"""
    print("\n" + "="*70)
    print("BACKTEST: Singapore Banking Yield Spread Strategy")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get data for DBS, OCBC, UOB
    # Note: Using HK tickers as proxy if SG not available
    query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE ticker IN ('D05.SI', 'O39.SI', 'U11.SI', '0005.HK', '1299.HK')
    AND date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No data available for Singapore banks")
        return None
    
    print(f"Data loaded: {len(df)} records")
    print(f"Tickers: {df['ticker'].unique()}")
    
    # For this backtest, simulate the strategy using available data
    # Strategy: Long banks when rates rising (2022-2023 cycle)
    
    # Define rate hike periods (Fed funds rate changes)
    # Mar 2022 - Jul 2023: Rising rate cycle
    rate_hike_start = pd.Timestamp('2022-03-01')
    rate_hike_end = pd.Timestamp('2023-07-31')
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        # Calculate returns
        ticker_df['returns'] = ticker_df['close'].pct_change()
        
        # Entry: Start of rate hike cycle
        entry_data = ticker_df[ticker_df['date'] >= rate_hike_start]
        if len(entry_data) == 0:
            continue
        
        entry_date = entry_data.iloc[0]['date']
        entry_price = entry_data.iloc[0]['close']
        
        # Exit: End of rate hike cycle
        exit_data = ticker_df[ticker_df['date'] >= rate_hike_end]
        if len(exit_data) == 0:
            continue
        
        exit_date = exit_data.iloc[0]['date']
        exit_price = exit_data.iloc[0]['close']
        
        pnl = (exit_price - entry_price) / entry_price * 100
        
        trades.append({
            'ticker': ticker,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'holding_days': (exit_date - entry_date).days
        })
    
    if not trades:
        print("No trades generated")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0:
        return None
    
    # Calculate metrics
    annual_factor = 365 / trades_df['holding_days'].mean() if trades_df['holding_days'].mean() > 0 else 1
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'avg_holding_days': trades_df['holding_days'].mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(annual_factor) if returns.std() > 0 else 0,
        'max_drawdown': returns.min()
    }
    
    print(f"\nBacktest Results:")
    print(f"  Period: Mar 2022 - Jul 2023 (Rate Hike Cycle)")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Avg Holding: {results['avg_holding_days']:.0f} days")
    print(f"  Sharpe: {results['sharpe']:.2f}")
    print(f"  Max DD: {results['max_drawdown']:.2f}%")
    
    print("\n  Trade Details:")
    for _, trade in trades_df.iterrows():
        print(f"    {trade['ticker']:12} | Entry: {trade['entry_date']} | PnL: {trade['pnl']:+.2f}%")
    
    backtest_id, status = save_backtest_result(
        'Singapore Banking Yield Spread',
        results,
        {'entry': 'rate_hike_start', 'exit': 'rate_hike_end', 'tickers': list(df['ticker'].unique())},
        '2022-03-01',
        '2023-07-31'
    )
    
    print(f"\n  Status: {status.upper()}")
    
    return results


def backtest_china_ai_chip():
    """Backtest China AI Chip Infrastructure Strategy"""
    print("\n" + "="*70)
    print("BACKTEST: China AI Chip Infrastructure Strategy")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get data for China tech tickers
    query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE ticker IN ('0700.HK', '9988.HK', '3690.HK', '1024.HK', '9866.HK')
    AND date BETWEEN '2022-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No data available for China AI tickers")
        return None
    
    print(f"Data loaded: {len(df)} records")
    print(f"Tickers: {df['ticker'].unique()}")
    
    # Key dates for China AI theme
    # Oct 2022: First US chip ban announcement
    # Oct 2023: Expanded ban
    # Mar 2024: "Big Fund" Phase 3 announced ($47B)
    
    policy_dates = [
        ('2022-10-07', 'US Chip Ban Round 1'),
        ('2023-10-17', 'US Chip Ban Round 2'),
        ('2024-03-01', 'Big Fund Phase 3'),
    ]
    
    trades = []
    
    for policy_date, policy_name in policy_dates:
        entry_date = pd.Timestamp(policy_date)
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker].sort_values('date')
            
            # Find entry price (day after policy)
            entry_data = ticker_df[ticker_df['date'] >= entry_date]
            if len(entry_data) < 30:  # Need at least 30 days for exit
                continue
            
            entry_price = entry_data.iloc[0]['close']
            
            # Exit after 60 days (typical policy drift window)
            if len(entry_data) >= 60:
                exit_price = entry_data.iloc[59]['close']
                exit_date = entry_data.iloc[59]['date']
            else:
                exit_price = entry_data.iloc[-1]['close']
                exit_date = entry_data.iloc[-1]['date']
            
            pnl = (exit_price - entry_price) / entry_price * 100
            
            trades.append({
                'ticker': ticker,
                'policy': policy_name,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'pnl': pnl
            })
    
    if not trades:
        print("No trades generated")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(6) if returns.std() > 0 else 0,
        'max_drawdown': returns.min()
    }
    
    print(f"\nBacktest Results:")
    print(f"  Period: Oct 2022 - Mar 2024")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Sharpe: {results['sharpe']:.2f}")
    print(f"  Max DD: {results['max_drawdown']:.2f}%")
    
    print("\n  Trade Details:")
    for _, trade in trades_df.iterrows():
        print(f"    {trade['ticker']:10} | {trade['policy'][:20]:20} | PnL: {trade['pnl']:+.2f}%")
    
    backtest_id, status = save_backtest_result(
        'China AI Chip Infrastructure',
        results,
        {'signals': policy_dates, 'hold_days': 60},
        '2022-10-01',
        '2024-03-31'
    )
    
    print(f"\n  Status: {status.upper()}")
    
    return results


def show_summary():
    print("\n" + "="*70)
    print("BACKTEST SUMMARY - Asian Hypotheses")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT hypothesis_name, total_trades, win_rate_pct, sharpe_ratio
    FROM openclaw_researcher.backtest_results
    WHERE hypothesis_name IN ('Singapore Banking Yield Spread', 'China AI Chip Infrastructure', 'HK IPO Post Listing Momentum')
    AND status = 'completed'
    ORDER BY sharpe_ratio DESC NULLS LAST
    """)
    
    print("\nToday's Backtests:")
    print("-"*70)
    
    for row in cursor.fetchall():
        sharpe_val = float(row[3]) if row[3] else -999
        sharpe_str = f"{sharpe_val:.2f}" if sharpe_val != -999 else "N/A"
        win_str = f"{float(row[2]) if row[2] else 0:.1f}"
        
        if sharpe_val >= 1.0:
            icon = "✅"
            status = "VALIDATED"
        elif sharpe_val > 0:
            icon = "🧪"
            status = "TESTING"
        else:
            icon = "❌"
            status = "REJECTED"
        
        print(f"{icon} {row[0][:40]:40} | Trades: {row[1]:3} | Win: {win_str:5}% | Sharpe: {sharpe_str:6} | {status}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("="*70)
    print("ASIAN HYPOTHESES BACKTESTING")
    print("="*70)
    
    # Run backtests
    backtest_sg_banking()
    backtest_china_ai_chip()
    
    show_summary()
    
    print("\n" + "="*70)
    print("✅ Backtesting complete!")
    print("="*70)
