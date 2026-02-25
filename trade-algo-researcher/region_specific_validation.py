#!/usr/bin/env python3
"""
REGION-SPECIFIC RIGOROUS VALIDATION
Testing strategies in their SPECIFIC regions with EXACT tickers listed
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
    
    # Check if exists
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


def test_gap_fade_hk():
    """Test Gap Fade on HK-specific tickers"""
    print("\n" + "="*70)
    print("REGION-SPECIFIC TEST: Gap Fade (HK)")
    print("="*70)
    
    # Exact tickers from strategy_region_definitions.json
    hk_tickers = ['1044.HK', '0006.HK', '0002.HK', '0023.HK', '0960.HK', 
                  '1038.HK', '0101.HK', '0016.HK', '0066.HK', '1113.HK']
    
    conn = get_db_connection()
    
    # Check which tickers have data
    ticker_list = "','".join(hk_tickers)
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT DISTINCT ticker FROM silver.historical_stock_data 
    WHERE ticker IN ('{ticker_list}') AND date > '2021-01-01'
    """)
    
    available_tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    print(f"Requested: {len(hk_tickers)} tickers")
    print(f"Available: {len(available_tickers)} tickers: {available_tickers}")
    
    if len(available_tickers) < 3:
        print("❌ INSUFFICIENT DATA")
        conn.close()
        return None
    
    # Get data
    ticker_list = "','".join(available_tickers)
    query = f"""
    SELECT date, ticker, close, open
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Data: {len(df):,} records")
    
    # Gap fade strategy
    trades = []
    commission = 0.005
    slippage = 0.0005
    
    for ticker in available_tickers:
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        # Calculate overnight gap
        ticker_df['prev_close'] = ticker_df['close'].shift(1)
        ticker_df['gap'] = (ticker_df['open'] - ticker_df['prev_close']) / ticker_df['prev_close']
        
        for i in range(1, len(ticker_df)):
            gap = ticker_df['gap'].iloc[i]
            
            # Gap > 0.5% fade
            if abs(gap) > 0.005:
                entry_price = ticker_df['open'].iloc[i]
                
                # Exit at close (intraday fade)
                exit_price = ticker_df['close'].iloc[i]
                
                # Fade the gap (if gap up, short; if gap down, long)
                if gap > 0:
                    # Gap up - fade down
                    gross_return = (entry_price - exit_price) / entry_price
                else:
                    # Gap down - fade up
                    gross_return = (exit_price - entry_price) / entry_price
                
                # Costs
                total_cost = slippage * 2 + (commission / entry_price) * 2
                net_return = gross_return - total_cost
                
                trades.append({
                    'ticker': ticker,
                    'date': ticker_df['date'].iloc[i],
                    'gap': gap * 100,
                    'net_return': net_return * 100
                })
    
    if not trades:
        print("❌ NO TRADES")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['net_return'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        print("❌ NO VALID RETURNS")
        return None
    
    periods_per_year = 252  # Daily
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min()
    }
    
    print(f"\n📊 RESULTS (HK tickers only):")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Sharpe: {results['sharpe']:.2f}")
    print(f"  Max DD: {results['max_drawdown']:.2f}%")
    
    status_str = "✅ VALIDATED" if sharpe >= 1.0 and results['win_rate'] >= 50 else "❌ FAILED"
    print(f"\n  Status: {status_str}")
    
    save_result(
        'Gap Fade (HK)',
        results,
        {'tickers': available_tickers, 'gap_threshold': 0.005, 'region': 'HK'},
        '2021-01-01',
        '2024-12-31',
        f'Region-specific test on {len(available_tickers)} HK tickers'
    )
    
    return results


def test_3day_reversal_hk():
    """Test 3-Day Reversal on HK-specific tickers"""
    print("\n" + "="*70)
    print("REGION-SPECIFIC TEST: 3-Day Reversal (HK)")
    print("="*70)
    
    # Exact tickers from strategy_region_definitions.json
    hk_tickers = ['0005.HK', '1044.HK', '1299.HK', '2888.HK', '0011.HK',
                  '1113.HK', '1997.HK', '1038.HK', '0388.HK', '0960.HK',
                  '1177.HK', '1398.HK', '1810.HK']
    
    conn = get_db_connection()
    
    # Check available tickers
    ticker_list = "','".join(hk_tickers)
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT DISTINCT ticker FROM silver.historical_stock_data 
    WHERE ticker IN ('{ticker_list}') AND date > '2021-01-01'
    """)
    
    available_tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    print(f"Requested: {len(hk_tickers)} tickers")
    print(f"Available: {len(available_tickers)} tickers: {available_tickers}")
    
    if len(available_tickers) < 5:
        print("❌ INSUFFICIENT DATA")
        conn.close()
        return None
    
    # Get data
    ticker_list = "','".join(available_tickers)
    query = f"""
    SELECT date, ticker, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '2021-01-01' AND '2024-12-31'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Data: {len(df):,} records")
    
    # 3-Day Reversal strategy
    trades = []
    commission = 0.005
    slippage = 0.0005
    
    for ticker in available_tickers:
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        ticker_df['ret_3d'] = ticker_df['close'].pct_change(3)
        ticker_df['volume_avg'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg']
        
        for i in range(60, len(ticker_df) - 5):
            row = ticker_df.iloc[i]
            
            # Signal: 3-day decline > 5%, volume > 1.3x
            if row['ret_3d'] < -0.05 and row['volume_ratio'] > 1.3:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + 3]['close']
                
                gross_return = (exit_price - entry_price) / entry_price
                total_cost = slippage * 2 + (commission / entry_price) * 2
                net_return = gross_return - total_cost
                
                trades.append({
                    'ticker': ticker,
                    'date': ticker_df.index[i],
                    'net_return': net_return * 100
                })
    
    if not trades:
        print("❌ NO TRADES")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['net_return'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        print("❌ NO VALID RETURNS")
        return None
    
    periods_per_year = 84  # 3-day holds
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min()
    }
    
    print(f"\n📊 RESULTS (HK tickers only):")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Sharpe: {results['sharpe']:.2f}")
    print(f"  Max DD: {results['max_drawdown']:.2f}%")
    
    status_str = "✅ VALIDATED" if sharpe >= 1.0 and results['win_rate'] >= 50 else "❌ FAILED"
    print(f"\n  Status: {status_str}")
    
    save_result(
        '3-Day Reversal (HK)',
        results,
        {'tickers': available_tickers, 'threshold': 0.05, 'region': 'HK'},
        '2021-01-01',
        '2024-12-31',
        f'Region-specific test on {len(available_tickers)} HK tickers'
    )
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("REGION-SPECIFIC RIGOROUS VALIDATION")
    print("="*70)
    print("\n✅ Testing strategies on their SPECIFIC regional tickers")
    print("✅ Using exact tickers from strategy_region_definitions.json")
    print("✅ Including transaction costs")
    print("="*70)
    
    test_gap_fade_hk()
    test_3day_reversal_hk()
    
    print("\n" + "="*70)
    print("✅ REGION-SPECIFIC TESTING COMPLETE")
    print("="*70)
