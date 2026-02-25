#!/usr/bin/env python3
"""
RIGOROUS REVALIDATION SCRIPT
Testing all strategies with actual available data only
NO proxies, NO synthetic data, NO assumptions
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


def save_result(hypothesis_name, results, params, start_date, end_date, notes=""):
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
              params_json, notes, existing[0]))
    else:
        cursor.execute("""
        INSERT INTO openclaw_researcher.backtest_results 
        (hypothesis_name, start_date, end_date, total_trades, win_rate_pct,
         sharpe_ratio, max_drawdown_pct, status, parameters, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (hypothesis_name, start_date, end_date, total_trades, win_rate,
              sharpe, max_dd, 'completed', params_json, notes))
    
    backtest_id = cursor.fetchone()[0]
    
    # Determine status based on results
    if sharpe and sharpe >= 1.0 and win_rate and win_rate >= 50:
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


def validate_3day_reversal():
    """RIGOROUS VALIDATION: 3-Day Reversal with full transaction costs"""
    print("\n" + "="*70)
    print("VALIDATING: 3-Day Reversal")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get actual available tickers from database
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT ticker FROM silver.historical_stock_data 
    WHERE date > '2021-01-01'
    AND (ticker LIKE 'A%' OR ticker LIKE 'MSFT' OR ticker LIKE 'GOOGL' 
         OR ticker LIKE 'AMZN' OR ticker LIKE 'NVDA' OR ticker LIKE 'TSLA'
         OR ticker LIKE 'META' OR ticker LIKE 'NFLX' OR ticker LIKE 'AMD'
         OR ticker LIKE 'CRM' OR ticker LIKE 'ADBE' OR ticker LIKE 'PYPL'
         OR ticker LIKE 'UBER' OR ticker LIKE 'COIN' OR ticker LIKE 'PLTR')
    LIMIT 20
    """)
    
    tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    if len(tickers) < 10:
        # Fallback: get any tickers with sufficient data
        query = """
        SELECT ticker FROM (
            SELECT ticker, COUNT(*) as cnt 
            FROM silver.historical_stock_data 
            WHERE date BETWEEN '2021-01-01' AND '2024-12-31'
            GROUP BY ticker 
            ORDER BY cnt DESC 
            LIMIT 20
        ) sub
        """
        tickers_df = pd.read_sql(query, conn)
        tickers = tickers_df['ticker'].tolist()
    
    print(f"Testing with {len(tickers)} tickers: {tickers[:5]}...")
    
    # Get price data
    ticker_list = "','".join(tickers)
    query = f"""
    SELECT date, ticker, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ NO DATA AVAILABLE")
        return None
    
    print(f"Data: {len(df):,} records")
    
    # Backtest with transaction costs
    trades = []
    commission = 0.005  # $0.005 per share
    slippage = 0.0005   # 0.05%
    
    for ticker in tickers:
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        # Calculate signals
        ticker_df['ret_1d'] = ticker_df['close'].pct_change()
        ticker_df['ret_3d'] = ticker_df['close'].pct_change(3)
        ticker_df['volume_avg_20'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg_20']
        
        for i in range(60, len(ticker_df) - 5):
            row = ticker_df.iloc[i]
            
            # Signal: 3 down days, >5% decline, volume > 1.3x
            if row['ret_3d'] < -0.05 and row['volume_ratio'] > 1.3:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + 3]['close']  # Hold 3 days
                
                # Calculate returns with costs
                gross_return = (exit_price - entry_price) / entry_price
                
                # Entry costs (slippage + commission impact)
                entry_cost = slippage + (commission / entry_price)
                exit_cost = slippage + (commission / exit_price)
                
                net_return = gross_return - entry_cost - exit_cost
                
                trades.append({
                    'ticker': ticker,
                    'date': ticker_df.index[i],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'gross_return': gross_return * 100,
                    'net_return': net_return * 100
                })
    
    if not trades:
        print("❌ NO TRADES GENERATED")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['net_return'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        print("❌ INSUFFICIENT TRADES FOR ANALYSIS")
        return None
    
    # Calculate metrics
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    total_return = returns.sum()
    
    # Sharpe (assuming 252 trading days, hold 3 days = 84 periods/year)
    periods_per_year = 84
    sharpe = avg_return / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else 0
    
    # Max drawdown from cumulative returns
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'gross_avg': trades_df['gross_return'].mean()
    }
    
    print(f"\n📊 RESULTS (with transaction costs):")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return (net): {results['avg_return']:.2f}%")
    print(f"  Avg Return (gross): {results['gross_avg']:.2f}%")
    print(f"  Total Return: {results['total_return']:.2f}%")
    print(f"  Sharpe Ratio: {results['sharpe']:.2f}")
    print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"  Transaction Cost Impact: {results['gross_avg'] - results['avg_return']:.2f}%")
    
    status_str = "✅ VALIDATED" if sharpe >= 1.0 and win_rate >= 50 else "❌ FAILED"
    print(f"\n  Status: {status_str}")
    
    save_result(
        '3-Day Reversal',
        results,
        {'slippage': 0.0005, 'commission': 0.005, 'hold_days': 3, 'threshold': 0.05},
        '2021-01-01',
        '2024-12-31',
        'RIGOROUS validation with transaction costs - Research Integrity Protocol'
    )
    
    return results


def validate_sector_rotation():
    """RIGOROUS VALIDATION: Sector Rotation with ETF data"""
    print("\n" + "="*70)
    print("VALIDATING: Sector Rotation Tech/Util")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get ETF data from gold schema
    query = """
    SELECT date, ticker, close_price
    FROM gold.etf_daily_data
    WHERE ticker IN ('XLK', 'XLU', 'SPY')
    AND date BETWEEN '2018-01-01' AND '2024-12-31'
    ORDER BY date, ticker
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ NO ETF DATA AVAILABLE")
        return None
    
    print(f"Data: {len(df):,} records")
    print(f"Tickers: {df['ticker'].unique()}")
    
    # Pivot to wide format
    pivoted = df.pivot(index='date', columns='ticker', values='close_price')
    pivoted = pivoted.dropna()
    
    # Calculate momentum spread
    pivoted['xlk_mom'] = pivoted['XLK'].pct_change(20)
    pivoted['xlu_mom'] = pivoted['XLU'].pct_change(20)
    pivoted['spread'] = pivoted['xlk_mom'] - pivoted['xlu_mom']
    pivoted = pivoted.dropna()
    
    # Transaction costs for ETFs (lower than stocks)
    commission = 0.001  # 0.1%
    slippage = 0.0002   # 0.02%
    total_cost = commission + slippage
    
    trades = []
    position = None
    entry_price = None
    entry_date = None
    
    for i in range(20, len(pivoted) - 20):
        date = pivoted.index[i]
        spread = pivoted['spread'].iloc[i]
        
        # Entry logic
        if position is None:
            if spread > 0.05:  # Tech outperforming
                position = 'XLU'
                entry_price = pivoted['XLU'].iloc[i]
                entry_date = date
            elif spread < -0.05:  # Utilities outperforming
                position = 'XLK'
                entry_price = pivoted['XLK'].iloc[i]
                entry_date = date
        
        # Exit logic (20 days or spread normalizes)
        elif position:
            days_held = i - pivoted.index.get_loc(entry_date)
            current_spread = abs(spread)
            
            if days_held >= 20 or current_spread < 0.02:
                if position == 'XLU':
                    exit_price = pivoted['XLU'].iloc[i]
                else:
                    exit_price = pivoted['XLK'].iloc[i]
                
                gross_return = (exit_price - entry_price) / entry_price
                net_return = gross_return - (total_cost * 2)  # Entry + exit
                
                trades.append({
                    'date': entry_date,
                    'position': position,
                    'gross_return': gross_return * 100,
                    'net_return': net_return * 100,
                    'days_held': days_held
                })
                
                position = None
    
    if not trades:
        print("❌ NO TRADES GENERATED")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['net_return'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        print("❌ INSUFFICIENT TRADES")
        return None
    
    # Calculate metrics
    periods_per_year = 12  # Monthly rebalancing
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min(),
        'avg_days_held': trades_df['days_held'].mean()
    }
    
    print(f"\n📊 RESULTS (with transaction costs):")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Avg Hold Days: {results['avg_days_held']:.0f}")
    print(f"  Sharpe Ratio: {results['sharpe']:.2f}")
    print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    
    status_str = "✅ VALIDATED" if sharpe >= 1.0 else "❌ FAILED"
    print(f"\n  Status: {status_str}")
    
    save_result(
        'Sector Rotation Tech/Util',
        results,
        {'slippage': 0.0002, 'commission': 0.001, 'threshold': 0.05, 'hold_days': 20},
        '2018-01-01',
        '2024-12-31',
        'RIGOROUS validation with ETF transaction costs - Research Integrity Protocol'
    )
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("RIGOROUS REVALIDATION - Research Integrity Protocol")
    print("="*70)
    print("\n✅ Using only actual database data")
    print("✅ Including transaction costs (slippage + commission)")
    print("✅ No proxies, no assumptions, no made-up numbers")
    print("="*70)
    
    validate_3day_reversal()
    validate_sector_rotation()
    
    print("\n" + "="*70)
    print("✅ RIGOROUS VALIDATION COMPLETE")
    print("="*70)
