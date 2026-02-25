#!/usr/bin/env python3
"""
HYPOTHESIS 7: Double Bottom Pattern Recognition
Classic reversal pattern - two lows at similar price level
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
    SELECT date, ticker, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def find_double_bottoms(prices, tolerance=0.02, min_days_between=5, max_days_between=30):
    """Find double bottom patterns in price series"""
    patterns = []
    
    # Find local minima manually (without scipy)
    minima_indices = []
    for i in range(5, len(prices) - 5):
        # Check if this is a local minimum (lower than 5 days before and after)
        if prices.iloc[i] < prices.iloc[i-5:i].min() and prices.iloc[i] < prices.iloc[i+1:i+5].min():
            minima_indices.append(i)
    
    for i in range(len(minima_indices)):
        for j in range(i+1, len(minima_indices)):
            idx1 = minima_indices[i]
            idx2 = minima_indices[j]
            
            # Check time between
            days_between = idx2 - idx1
            if days_between < min_days_between or days_between > max_days_between:
                continue
            
            # Check price similarity (within tolerance)
            price1 = prices.iloc[idx1]
            price2 = prices.iloc[idx2]
            price_diff = abs(price1 - price2) / price1
            
            if price_diff <= tolerance:
                # Check if there's a peak between (the "middle")
                middle_prices = prices.iloc[idx1:idx2]
                peak_between = middle_prices.max()
                
                # Valid double bottom: peak between is higher than both lows
                if peak_between > price1 * 1.02 and peak_between > price2 * 1.02:
                    patterns.append((idx1, idx2, price1, price2))
    
    return patterns


def test_double_bottom(sector, tickers):
    """Test double bottom pattern"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 7: Double Bottom Pattern on {sector}")
    print(f"{'='*70}")
    print(f"Pattern: Two lows at similar price, with peak in between")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date')
        if len(ticker_df) < 60:
            continue
        
        # Find double bottoms
        patterns = find_double_bottoms(ticker_df['close'])
        
        for idx1, idx2, price1, price2 in patterns:
            # Entry: Break above the peak between the two bottoms
            middle_prices = ticker_df['close'].iloc[idx1:idx2]
            peak_price = middle_prices.max()
            peak_idx = middle_prices.idxmax()
            
            # Look for breakout after second bottom
            for k in range(idx2 + 1, min(idx2 + 10, len(ticker_df))):
                if ticker_df['close'].iloc[k] > peak_price:
                    entry_price = ticker_df['close'].iloc[k]
                    entry_date = ticker_df['date'].iloc[k]
                    
                    # Exit after 10 days
                    if k + 10 < len(ticker_df):
                        exit_price = ticker_df['close'].iloc[k + 10]
                        
                        gross_return = (exit_price - entry_price) / entry_price * 100
                        net_return = gross_return - 0.1
                        
                        trades.append(net_return)
                    break
    
    if len(trades) < 20:
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
    print(f"  Patterns Found:  {results['trades']}")
    print(f"  Win Rate:        {results['win_rate']:.1f}%")
    print(f"  Avg Return:      {results['avg_return']:.2f}%")
    print(f"  Sharpe Ratio:    {results['sharpe']:.2f}")
    print(f"  Max Drawdown:    {results['max_dd']:.2f}%")
    print(f"  Avg Winner:      {results['avg_winner']:.2f}%")
    print(f"  Avg Loser:       {results['avg_loser']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"  ✅ VALIDATED - Pattern works!")
        status = "VALIDATED"
    elif sharpe > 0.3 and win_rate >= 50:
        print(f"  🧪 TESTING - Weak edge")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Pattern not predictive")
        status = "REJECTED"
    
    if status == "REJECTED":
        print(f"\n📋 REJECTION REASON:")
        if win_rate < 50:
            print(f"  - Win rate below 50% (coin flip)")
        if sharpe < 0:
            print(f"  - Negative Sharpe (losing strategy)")
        print(f"  - Double bottoms too rare or not reliable")
        print(f"  - Pattern recognition may be too subjective")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 7: Double Bottom Pattern")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            results, status = test_double_bottom(sector_name, sectors[sector_name])
            
            if results:
                print(f"\n{'='*70}")
                print(f"SUMMARY for {sector_name}:")
                print(f"  Sharpe: {results['sharpe']:.2f}")
                print(f"  Win Rate: {results['win_rate']:.1f}%")
                print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 7 TEST COMPLETE")
    print("="*70)
