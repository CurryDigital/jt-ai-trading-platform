#!/usr/bin/env python3
"""
HYPOTHESIS 12: Volume Spike + RSI Oversold Combo
Combine two signals for higher conviction
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np


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


def get_data_with_metrics(tickers, start='2022-01-01', end='2024-12-31'):
    """Get price data with RSI metrics"""
    conn = get_db_connection()
    
    # Get historical prices
    ticker_list = "','".join(tickers[:30])
    price_query = f"""
    SELECT date, ticker, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    prices = pd.read_sql(price_query, conn)
    
    # Get RSI from gold schema
    rsi_query = f"""
    SELECT date, ticker, rsi_14
    FROM gold.stock_metrics
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    rsi = pd.read_sql(rsi_query, conn)
    
    conn.close()
    
    # Merge
    df = prices.merge(rsi, on=['date', 'ticker'], how='inner')
    return df


def test_volume_rsi_combo(sector, tickers):
    """Test volume spike + RSI oversold combo"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 12: Volume + RSI Combo on {sector}")
    print(f"{'='*70}")
    print(f"Signal: Volume > 2.0x AND RSI < 30 (high conviction mean reversion)")
    
    df = get_data_with_metrics(tickers)
    if len(df) == 0:
        return None, None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        # Calculate volume average
        ticker_df['vol_avg'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
        
        # Signal: Volume spike + RSI oversold
        ticker_df['signal'] = (
            (ticker_df['vol_ratio'] > 2.0) & 
            (ticker_df['rsi_14'] < 30)
        )
        
        for i in range(25, len(ticker_df) - 10):
            if ticker_df['signal'].iloc[i]:
                entry_price = ticker_df['close'].iloc[i]
                exit_price = ticker_df['close'].iloc[i + 10]
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append(net_return)
    
    if len(trades) < 10:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        print(f"   (Volume + RSI < 30 combo too rare)")
        return None, None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    results = {
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_dd': max_dd
    }
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Trades:       {results['trades']}")
    print(f"  Win Rate:     {results['win_rate']:.1f}%")
    print(f"  Avg Return:   {results['avg_return']:.2f}%")
    print(f"  Sharpe:       {results['sharpe']:.2f}")
    print(f"  Max DD:       {results['max_dd']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"  ✅ VALIDATED - Combo signal works")
        status = "VALIDATED"
    elif sharpe > 0.3 and win_rate >= 50:
        print(f"  🧪 TESTING - Weak edge")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Combo not predictive")
        status = "REJECTED"
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 12: Volume + RSI Combo")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT ticker, sector FROM gold.stock_metrics 
    WHERE sector IS NOT NULL AND date > '2023-01-01'
    """)
    tickers_by_sector = {}
    for row in cursor.fetchall():
        ticker, sector = row
        if sector not in tickers_by_sector:
            tickers_by_sector[sector] = []
        tickers_by_sector[sector].append(ticker)
    cursor.close()
    conn.close()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in tickers_by_sector:
            results, status = test_volume_rsi_combo(sector_name, tickers_by_sector[sector_name])
            
            if results:
                print(f"\n{'='*70}")
                print(f"SUMMARY for {sector_name}:")
                print(f"  Sharpe: {results['sharpe']:.2f}")
                print(f"  Win Rate: {results['win_rate']:.1f}%")
                print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 12 TEST COMPLETE")
    print("="*70)
