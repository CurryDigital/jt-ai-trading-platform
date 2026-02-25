#!/usr/bin/env python3
"""
HYPOTHESIS 8: Higher Lows Trend Strategy
Simple trend following - buy when price makes higher lows
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
    SELECT date, ticker, close, low, high
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def test_higher_lows(sector, tickers):
    """Test higher lows trend strategy"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 8: Higher Lows Trend on {sector}")
    print(f"{'='*70}")
    print(f"Signal: 3 consecutive higher lows = uptrend, go long")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None, None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        # Calculate higher lows
        ticker_df['higher_low'] = (
            (ticker_df['low'] > ticker_df['low'].shift(1)) &
            (ticker_df['low'].shift(1) > ticker_df['low'].shift(2)) &
            (ticker_df['low'].shift(2) > ticker_df['low'].shift(3))
        )
        
        # Also require higher highs for confirmation
        ticker_df['higher_high'] = (
            (ticker_df['high'] > ticker_df['high'].shift(1)) &
            (ticker_df['high'].shift(1) > ticker_df['high'].shift(2))
        )
        
        # Entry: Higher lows + higher highs (strong uptrend)
        for i in range(10, len(ticker_df) - 10):
            if ticker_df['higher_low'].iloc[i] and ticker_df['higher_high'].iloc[i]:
                entry_price = ticker_df['close'].iloc[i]
                
                # Exit after 10 days or if trend breaks
                exit_price = None
                for j in range(i+1, min(i+11, len(ticker_df))):
                    # Exit if we get a lower low (trend broken)
                    if ticker_df['low'].iloc[j] < ticker_df['low'].iloc[j-1]:
                        exit_price = ticker_df['close'].iloc[j]
                        break
                
                if exit_price is None:
                    exit_price = ticker_df.iloc[min(i+10, len(ticker_df)-1)]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append(net_return)
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    winners = returns[returns > 0]
    losers = returns[returns <= 0]
    
    results = {
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'avg_winner': winners.mean() if len(winners) > 0 else 0,
        'avg_loser': losers.mean() if len(losers) > 0 else 0
    }
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Trades:       {results['trades']}")
    print(f"  Win Rate:     {results['win_rate']:.1f}%")
    print(f"  Avg Return:   {results['avg_return']:.2f}%")
    print(f"  Sharpe:       {results['sharpe']:.2f}")
    print(f"  Max DD:       {results['max_dd']:.2f}%")
    print(f"  Avg Winner:   {results['avg_winner']:.2f}%")
    print(f"  Avg Loser:    {results['avg_loser']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"  ✅ VALIDATED - Trend following works")
        status = "VALIDATED"
    elif sharpe > 0.3 and win_rate >= 50:
        print(f"  🧪 TESTING - Weak trend signal")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Higher lows not predictive")
        status = "REJECTED"
        print(f"\n📋 REJECTION REASON:")
        print(f"  - Simple price patterns not sufficient")
        print(f"  - Need volume/momentum confirmation")
        print(f"  - Entry too late in trend")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 8: Higher Lows Trend Strategy")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            results, status = test_higher_lows(sector_name, sectors[sector_name])
            
            if results:
                print(f"\n{'='*70}")
                print(f"SUMMARY for {sector_name}:")
                print(f"  Sharpe: {results['sharpe']:.2f}")
                print(f"  Win Rate: {results['win_rate']:.1f}%")
                print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 8 TEST COMPLETE")
    print("="*70)
