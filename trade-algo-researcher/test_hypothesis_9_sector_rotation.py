#!/usr/bin/env python3
"""
HYPOTHESIS 9: Sector Rotation Momentum
Buy strongest sector, sell weakest
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


def test_sector_rotation():
    """Test sector rotation momentum"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 9: Sector Rotation Momentum")
    print(f"{'='*70}")
    print(f"Signal: Buy strongest sector ETF, sell weakest")
    
    conn = get_db_connection()
    
    # Get ETF data
    query = """
    SELECT date, ticker, close_price
    FROM gold.etf_daily_data
    WHERE ticker IN ('XLK', 'XLU', 'XLF', 'XLE', 'XLI')
    AND date BETWEEN '2020-01-01' AND '2024-12-31'
    ORDER BY date, ticker
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ NO ETF DATA")
        return None, None
    
    print(f"ETFs: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    # Calculate momentum for each ETF
    pivoted = df.pivot(index='date', columns='ticker', values='close_price')
    pivoted = pivoted.dropna()
    
    # 20-day momentum
    momentum = pivoted.pct_change(20)
    
    trades = []
    
    for i in range(20, len(momentum) - 20):
        row = momentum.iloc[i]
        
        # Find strongest and weakest sectors
        strongest = row.idxmax()
        weakest = row.idxmin()
        
        strongest_mom = row[strongest]
        weakest_mom = row[weakest]
        
        # Only trade if spread is significant (> 5%)
        if strongest_mom - weakest_mom > 0.05:
            # Long strongest
            entry_price = pivoted[strongest].iloc[i]
            exit_price = pivoted[strongest].iloc[i + 20]
            long_return = (exit_price - entry_price) / entry_price * 100
            
            # Short weakest
            entry_price_short = pivoted[weakest].iloc[i]
            exit_price_short = pivoted[weakest].iloc[i + 20]
            short_return = (entry_price_short - exit_price_short) / entry_price_short * 100
            
            # Combined return
            total_return = (long_return + short_return) / 2 - 0.1
            
            trades.append({
                'long': strongest,
                'short': weakest,
                'return': total_return
            })
    
    if len(trades) < 20:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['return']
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(12) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    results = {
        'trades': len(trades_df),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_dd': max_dd
    }
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Trades:      {results['trades']}")
    print(f"  Win Rate:    {results['win_rate']:.1f}%")
    print(f"  Avg Return:  {results['avg_return']:.2f}%")
    print(f"  Sharpe:      {results['sharpe']:.2f}")
    print(f"  Max DD:      {results['max_dd']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"  ✅ VALIDATED - Sector rotation works")
        status = "VALIDATED"
    elif sharpe > 0.5:
        print(f"  🧪 TESTING - Moderate edge")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - No sector momentum edge")
        status = "REJECTED"
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 9: Sector Rotation Momentum")
    print("="*70)
    
    results, status = test_sector_rotation()
    
    if results:
        print(f"\n{'='*70}")
        print(f"FINAL RESULTS:")
        print(f"  Sharpe: {results['sharpe']:.2f}")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 9 TEST COMPLETE")
    print("="*70)
