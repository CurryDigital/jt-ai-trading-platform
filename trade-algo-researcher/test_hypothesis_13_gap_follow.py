#!/usr/bin/env python3
"""
HYPOTHESIS 13: Gap Follow Strategy (Inverse of Gap Fade)
Follow the gap direction instead of fading it
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


def get_tickers_by_sector():
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
    return tickers_by_sector


def get_price_data(tickers, start='2022-01-01', end='2024-12-31'):
    conn = get_db_connection()
    ticker_list = "','".join(tickers[:30])
    query = f"""
    SELECT date, ticker, open, close
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def test_gap_follow(sector, tickers):
    """Test gap follow strategy (follow gap direction)"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 13: Gap Follow on {sector}")
    print(f"{'='*70}")
    print(f"Signal: Gap up > 2% → go LONG (follow momentum)")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None, None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        # Calculate overnight gap
        ticker_df['prev_close'] = ticker_df['close'].shift(1)
        ticker_df['gap_pct'] = (ticker_df['open'] - ticker_df['prev_close']) / ticker_df['prev_close']
        
        # Entry: Gap up > 2%
        for i in range(1, len(ticker_df) - 5):
            gap = ticker_df['gap_pct'].iloc[i]
            
            if gap > 0.02:  # Gap up > 2%
                entry_price = ticker_df['open'].iloc[i]
                exit_price = ticker_df['close'].iloc[i + 5]  # Hold 5 days
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append(net_return)
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(50) if returns.std() > 0 else -999
    
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
        print(f"  ✅ VALIDATED - Following gaps works")
        status = "VALIDATED"
    elif sharpe > 0.3 and win_rate >= 50:
        print(f"  🧪 TESTING - Moderate edge")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Gap following not predictive")
        status = "REJECTED"
        print(f"\n📋 Compared to Gap Fade:")
        print(f"  - Gap Fade (Tech): 50.5% win, Sharpe -0.07")
        print(f"  - Gap Follow (Tech): {win_rate:.1f}% win, Sharpe {sharpe:.2f}")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 13: Gap Follow Strategy")
    print("Inverse of Gap Fade - follow momentum instead of fading")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            results, status = test_gap_follow(sector_name, sectors[sector_name])
            
            if results:
                print(f"\n{'='*70}")
                print(f"SUMMARY for {sector_name}:")
                print(f"  Sharpe: {results['sharpe']:.2f}")
                print(f"  Win Rate: {results['win_rate']:.1f}%")
                print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 13 TEST COMPLETE")
    print("="*70)
