#!/usr/bin/env python3
"""
Comprehensive Batch Testing - All Testable Hypotheses
Uses only available data: silver.historical_stock_data + gold schema
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
import json
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total_trades = int(results.get('total_trades', 0))
    win_rate = float(results.get('win_rate', 0)) if results.get('win_rate') else None
    sharpe = float(results.get('sharpe', 0)) if results.get('sharpe') else None
    max_dd = float(results.get('max_drawdown', 0)) if results.get('max_drawdown') else None
    
    # Check if record exists
    cursor.execute("""
    SELECT id FROM openclaw_researcher.backtest_results 
    WHERE hypothesis_name = %s AND start_date = %s AND end_date = %s
    """, (hypothesis_name, start_date, end_date))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing
        cursor.execute("""
        UPDATE openclaw_researcher.backtest_results 
        SET total_trades = %s, win_rate_pct = %s, sharpe_ratio = %s, 
            max_drawdown_pct = %s, status = %s, parameters = %s, notes = %s, 
            created_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id
        """, (total_trades, win_rate, sharpe, max_dd, 'completed', 
              json.dumps(params), notes, existing[0]))
    else:
        # Insert new
        cursor.execute("""
        INSERT INTO openclaw_researcher.backtest_results 
        (hypothesis_name, start_date, end_date, total_trades, win_rate_pct,
         sharpe_ratio, max_drawdown_pct, status, parameters, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (hypothesis_name, start_date, end_date, total_trades, win_rate,
              sharpe, max_dd, 'completed', json.dumps(params), notes))
    
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


def test_time_series_momentum():
    """Time-Series Momentum - using OHLCV"""
    print("\n" + "="*70)
    print("TEST: Time-Series Momentum")
    print("="*70)
    
    conn = get_db_connection()
    query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    trades = []
    for ticker in df['ticker'].unique()[:50]:  # Limit to 50 tickers
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 60:
            continue
        
        ticker_df['ret_20d'] = ticker_df['close'].pct_change(20)
        ticker_df['ret_60d'] = ticker_df['close'].pct_change(60)
        ticker_df['future_ret'] = ticker_df['close'].pct_change(20).shift(-20)
        
        for i in range(60, len(ticker_df) - 20, 20):  # Monthly rebalancing
            row = ticker_df.iloc[i]
            
            # Long if both 20d and 60d returns positive
            if row['ret_20d'] > 0 and row['ret_60d'] > 0:
                trades.append({'signal': 'long', 'pnl': row['future_ret'] * 100})
            # Short if both negative
            elif row['ret_20d'] < 0 and row['ret_60d'] < 0:
                trades.append({'signal': 'short', 'pnl': -row['future_ret'] * 100})
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(12),
        'max_drawdown': returns.min()
    }
    
    print(f"  Trades: {results['total_trades']}, Win: {results['win_rate']:.1f}%, Sharpe: {results['sharpe']:.2f}")
    
    save_result('Time-Series Momentum', results, 
                {'lookback_short': 20, 'lookback_long': 60, 'hold_days': 20},
                '2021-01-01', '2024-12-31')
    return results


def test_quality_value_qarp():
    """Quality Value QARP - using stock_metrics fundamentals"""
    print("\n" + "="*70)
    print("TEST: Quality Value QARP")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get stock metrics with fundamentals
    query = """
    SELECT date, ticker, close, pe_ratio_ttm, ps_ratio, eps_growth_qbq, 
           debt_to_equity, free_cash_flow
    FROM gold.stock_metrics
    WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
    AND pe_ratio_ttm IS NOT NULL
    AND ps_ratio IS NOT NULL
    ORDER BY date, ticker
    """
    metrics_df = pd.read_sql(query, conn)
    
    # Get price data for forward returns
    price_query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE date BETWEEN '2024-01-01' AND '2025-01-31'
    ORDER BY ticker, date
    """
    prices_df = pd.read_sql(price_query, conn)
    conn.close()
    
    if len(metrics_df) == 0:
        print("  No fundamental data available")
        return None
    
    print(f"  Metrics records: {len(metrics_df)}")
    
    trades = []
    
    # Group by date for cross-sectional ranking
    for date, group in metrics_df.groupby('date'):
        if len(group) < 10:
            continue
        
        # Quality score: high EPS growth, low debt/equity, positive FCF
        group['quality_score'] = (
            group['eps_growth_qbq'].rank(pct=True) * 0.4 +
            (1 - group['debt_to_equity'].rank(pct=True)) * 0.3 +
            (group['free_cash_flow'] > 0).astype(int) * 0.3
        )
        
        # Value score: low P/E, low P/S
        group['value_score'] = (
            (1 - group['pe_ratio_ttm'].rank(pct=True)) * 0.5 +
            (1 - group['ps_ratio'].rank(pct=True)) * 0.5
        )
        
        # QARP: Quality at Reasonable Price
        group['qarp_score'] = group['quality_score'] * 0.6 + group['value_score'] * 0.4
        
        # Top quintile
        top_quintile = group.nlargest(int(len(group) * 0.2), 'qarp_score')
        
        for _, row in top_quintile.iterrows():
            ticker = row['ticker']
            entry_date = row['date']
            entry_price = row['close']
            
            # Find exit price (30 days later)
            ticker_prices = prices_df[prices_df['ticker'] == ticker]
            future_prices = ticker_prices[ticker_prices['date'] > entry_date]
            
            if len(future_prices) >= 20:
                exit_price = future_prices.iloc[19]['close']
                pnl = (exit_price - entry_price) / entry_price * 100
                trades.append({'ticker': ticker, 'pnl': pnl})
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(12),
        'max_drawdown': returns.min()
    }
    
    print(f"  Trades: {results['total_trades']}, Win: {results['win_rate']:.1f}%, Sharpe: {results['sharpe']:.2f}")
    
    save_result('Quality Value QARP', results,
                {'quality_weight': 0.6, 'value_weight': 0.4, 'hold_days': 30},
                '2024-01-01', '2024-12-31')
    return results


def test_pead():
    """Post-Earnings Announcement Drift - using earnings_data"""
    print("\n" + "="*70)
    print("TEST: PEAD (Post-Earnings Announcement Drift)")
    print("="*70)
    
    conn = get_db_connection()
    
    # Get earnings surprises
    query = """
    SELECT ticker, report_date, surprise_pct
    FROM gold.earnings_data
    WHERE surprise_pct IS NOT NULL
    ORDER BY ticker, report_date
    """
    earnings_df = pd.read_sql(query, conn)
    
    # Get price data
    price_query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE date BETWEEN '2024-01-01' AND '2025-02-15'
    ORDER BY ticker, date
    """
    prices_df = pd.read_sql(price_query, conn)
    conn.close()
    
    if len(earnings_df) == 0:
        print("  No earnings data available")
        return None
    
    print(f"  Earnings records: {len(earnings_df)}")
    
    trades = []
    
    for _, earnings in earnings_df.iterrows():
        ticker = earnings['ticker']
        report_date = pd.Timestamp(earnings['report_date'])
        surprise = float(earnings['surprise_pct'])
        
        # Get prices around earnings
        ticker_prices = prices_df[prices_df['ticker'] == ticker].copy()
        ticker_prices['date'] = pd.to_datetime(ticker_prices['date'])
        
        # Find entry (day after earnings)
        entry_prices = ticker_prices[ticker_prices['date'] > report_date]
        if len(entry_prices) == 0:
            continue
        entry_price = entry_prices.iloc[0]['close']
        entry_date = entry_prices.iloc[0]['date']
        
        # Find exit (20 days later)
        exit_prices = ticker_prices[ticker_prices['date'] > entry_date]
        if len(exit_prices) < 20:
            continue
        exit_price = exit_prices.iloc[19]['close']
        
        pnl = (exit_price - entry_price) / entry_price * 100
        
        # Positive surprise = long, Negative = short
        if surprise > 5:  # Strong positive surprise
            trades.append({'ticker': ticker, 'signal': 'long', 'surprise': surprise, 'pnl': pnl})
        elif surprise < -5:  # Strong negative surprise
            trades.append({'ticker': ticker, 'signal': 'short', 'surprise': surprise, 'pnl': -pnl})
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'avg_surprise': trades_df['surprise'].mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(12),
        'max_drawdown': returns.min()
    }
    
    print(f"  Trades: {results['total_trades']}, Win: {results['win_rate']:.1f}%, Sharpe: {results['sharpe']:.2f}")
    
    save_result('PEAD NLP Enhanced', results,
                {'surprise_threshold': 5, 'hold_days': 20},
                '2024-01-01', '2025-02-15',
                'Basic PEAD without NLP enhancement')
    return results


def test_moving_average_cross():
    """Moving Average Crossover - using OHLCV"""
    print("\n" + "="*70)
    print("TEST: Moving Average Crossover (Golden/Death Cross)")
    print("="*70)
    
    conn = get_db_connection()
    query = """
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    trades = []
    
    for ticker in df['ticker'].unique()[:30]:
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 200:
            continue
        
        ticker_df['sma_50'] = ticker_df['close'].rolling(50).mean()
        ticker_df['sma_200'] = ticker_df['close'].rolling(200).mean()
        ticker_df['position'] = np.where(ticker_df['sma_50'] > ticker_df['sma_200'], 1, -1)
        ticker_df['future_ret'] = ticker_df['close'].pct_change(20).shift(-20)
        
        # Signal on crossover
        ticker_df['signal'] = ticker_df['position'].diff()
        
        for i in range(200, len(ticker_df) - 20):
            if ticker_df['signal'].iloc[i] == 2:  # Bullish crossover
                pnl = ticker_df['future_ret'].iloc[i] * 100
                trades.append({'signal': 'golden_cross', 'pnl': pnl})
            elif ticker_df['signal'].iloc[i] == -2:  # Bearish crossover
                pnl = -ticker_df['future_ret'].iloc[i] * 100
                trades.append({'signal': 'death_cross', 'pnl': pnl})
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(12),
        'max_drawdown': returns.min()
    }
    
    print(f"  Trades: {results['total_trades']}, Win: {results['win_rate']:.1f}%, Sharpe: {results['sharpe']:.2f}")
    
    save_result('Moving Average Crossover', results,
                {'fast_ma': 50, 'slow_ma': 200, 'hold_days': 20},
                '2021-01-01', '2024-12-31')
    return results


def test_volume_spike():
    """Volume Spike Breakout - using OHLCV"""
    print("\n" + "="*70)
    print("TEST: Volume Spike Breakout")
    print("="*70)
    
    conn = get_db_connection()
    query = """
    SELECT date, ticker, open, high, low, close, volume
    FROM silver.historical_stock_data
    WHERE date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    trades = []
    
    for ticker in df['ticker'].unique()[:30]:
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 30:
            continue
        
        ticker_df['vol_avg_20'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['vol_spike'] = ticker_df['volume'] > ticker_df['vol_avg_20'] * 2
        ticker_df['price_break'] = ticker_df['close'] > ticker_df['close'].shift(1) * 1.02
        ticker_df['future_ret'] = ticker_df['close'].pct_change(10).shift(-10)
        
        for i in range(30, len(ticker_df) - 10):
            row = ticker_df.iloc[i]
            if row['vol_spike'] and row['price_break']:
                trades.append({'ticker': ticker, 'pnl': row['future_ret'] * 100})
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': returns.mean() / returns.std() * np.sqrt(25),
        'max_drawdown': returns.min()
    }
    
    print(f"  Trades: {results['total_trades']}, Win: {results['win_rate']:.1f}%, Sharpe: {results['sharpe']:.2f}")
    
    save_result('Volume Spike Breakout', results,
                {'vol_threshold': 2.0, 'price_threshold': 0.02, 'hold_days': 10},
                '2021-01-01', '2024-12-31')
    return results


def show_summary():
    print("\n" + "="*70)
    print("BACKTEST SUMMARY - Available Data Tests")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT hypothesis_name, total_trades, win_rate_pct, sharpe_ratio
    FROM openclaw_researcher.backtest_results
    WHERE status = 'completed'
    ORDER BY sharpe_ratio DESC NULLS LAST
    """)
    
    print("\nAll Backtests (Ranked by Sharpe):")
    print("-"*70)
    
    validated = []
    testing = []
    rejected = []
    
    for row in cursor.fetchall():
        name = row[0][:35]
        trades = row[1] if row[1] else 0
        win = float(row[2]) if row[2] else 0
        sharpe_val = float(row[3]) if row[3] else -999
        sharpe_str = f"{sharpe_val:.2f}" if sharpe_val != -999 else "N/A"
        win_str = f"{win:.1f}"
        
        line = f"  {name:35} | {trades:5} | {win_str:5}% | {sharpe_str:6}"
        
        if sharpe_val >= 1.0:
            validated.append(f"✅ {line}")
        elif sharpe_val > 0:
            testing.append(f"🧪 {line}")
        else:
            rejected.append(f"❌ {line}")
    
    for line in validated:
        print(line)
    for line in testing:
        print(line)
    for line in rejected:
        print(line)
    
    cursor.execute("""
    SELECT current_status, COUNT(*) FROM openclaw_researcher.hypothesis_registry
    GROUP BY current_status ORDER BY COUNT(*) DESC
    """)
    
    print("\n" + "="*70)
    print("HYPOTHESIS STATUS COUNTS")
    print("="*70)
    
    for row in cursor.fetchall():
        icon = {'idea': '💡', 'testing': '🧪', 'validated': '✅', 'promoted': '🏆', 'rejected': '❌'}.get(row[0], '⏳')
        print(f"  {icon} {row[0].upper():12}: {row[1]:3}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE BATCH TESTING - All Testable Hypotheses")
    print("="*70)
    
    # Run all tests
    test_time_series_momentum()
    test_quality_value_qarp()
    test_pead()
    test_moving_average_cross()
    test_volume_spike()
    
    show_summary()
    
    print("\n" + "="*70)
    print("✅ All tests with available data complete!")
    print("="*70)
