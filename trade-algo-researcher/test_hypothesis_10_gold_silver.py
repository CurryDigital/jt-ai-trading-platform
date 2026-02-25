#!/usr/bin/env python3
"""
HYPOTHESIS 10: Gold/Silver Ratio Mean Reversion
Trade the ratio between gold and silver prices
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


def test_gold_silver_ratio():
    """Test gold/silver ratio mean reversion"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 10: Gold/Silver Ratio Mean Reversion")
    print(f"{'='*70}")
    print(f"Signal: When ratio > 2 std dev from mean, expect mean reversion")
    
    conn = get_db_connection()
    
    # Get gold and silver data
    query = """
    SELECT date, ticker, close_price
    FROM gold.commodity_metrics
    WHERE ticker IN ('GC=F', 'SI=F')
    AND date BETWEEN '2020-01-01' AND '2024-12-31'
    ORDER BY date, ticker
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ NO COMMODITY DATA")
        return None, None
    
    print(f"Data: {len(df):,} records")
    
    # Pivot to get gold and silver side by side
    pivoted = df.pivot(index='date', columns='ticker', values='close_price')
    pivoted = pivoted.dropna()
    
    print(f"Gold/Silver records: {len(pivoted)}")
    
    # Calculate ratio
    pivoted['ratio'] = pivoted['GC=F'] / pivoted['SI=F']
    
    # Calculate z-score of ratio
    pivoted['ratio_mean'] = pivoted['ratio'].rolling(60).mean()
    pivoted['ratio_std'] = pivoted['ratio'].rolling(60).std()
    pivoted['z_score'] = (pivoted['ratio'] - pivoted['ratio_mean']) / pivoted['ratio_std']
    
    trades = []
    
    for i in range(60, len(pivoted) - 20):
        z = pivoted['z_score'].iloc[i]
        
        # If ratio is high (z > 2), expect mean reversion
        # Trade: Short gold, long silver (ratio will fall)
        if z > 2:
            gold_entry = pivoted['GC=F'].iloc[i]
            silver_entry = pivoted['SI=F'].iloc[i]
            
            gold_exit = pivoted['GC=F'].iloc[i + 20]
            silver_exit = pivoted['SI=F'].iloc[i + 20]
            
            # Short gold, long silver
            gold_return = (gold_entry - gold_exit) / gold_entry * 100
            silver_return = (silver_exit - silver_entry) / silver_entry * 100
            
            total_return = (gold_return + silver_return) / 2 - 0.1
            trades.append({'type': 'high_ratio', 'return': total_return})
        
        # If ratio is low (z < -2), expect mean reversion up
        # Trade: Long gold, short silver (ratio will rise)
        elif z < -2:
            gold_entry = pivoted['GC=F'].iloc[i]
            silver_entry = pivoted['SI=F'].iloc[i]
            
            gold_exit = pivoted['GC=F'].iloc[i + 20]
            silver_exit = pivoted['SI=F'].iloc[i + 20]
            
            # Long gold, short silver
            gold_return = (gold_exit - gold_entry) / gold_entry * 100
            silver_return = (silver_entry - silver_exit) / silver_entry * 100
            
            total_return = (gold_return + silver_return) / 2 - 0.1
            trades.append({'type': 'low_ratio', 'return': total_return})
    
    if len(trades) < 10:
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
        'max_dd': max_dd,
        'high_ratio_trades': len(trades_df[trades_df['type'] == 'high_ratio']),
        'low_ratio_trades': len(trades_df[trades_df['type'] == 'low_ratio'])
    }
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Trades:       {results['trades']}")
    print(f"  High Ratio:   {results['high_ratio_trades']}")
    print(f"  Low Ratio:    {results['low_ratio_trades']}")
    print(f"  Win Rate:     {results['win_rate']:.1f}%")
    print(f"  Avg Return:   {results['avg_return']:.2f}%")
    print(f"  Sharpe:       {results['sharpe']:.2f}")
    print(f"  Max DD:       {results['max_dd']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 55:
        print(f"  ✅ VALIDATED - Ratio mean reversion works")
        status = "VALIDATED"
    elif sharpe > 0.3:
        print(f"  🧪 TESTING - Weak edge")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Ratio not mean reverting")
        status = "REJECTED"
        print(f"\n📋 REJECTION REASON:")
        print(f"  - Gold/Silver ratio trends, doesn't mean revert")
        print(f"  - Extreme ratios can become more extreme")
        print(f"  - Need different timeframes or thresholds")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 10: Gold/Silver Ratio Mean Reversion")
    print("="*70)
    
    results, status = test_gold_silver_ratio()
    
    if results:
        print(f"\n{'='*70}")
        print(f"FINAL RESULTS:")
        print(f"  Sharpe: {results['sharpe']:.2f}")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Trades: {results['trades']}")
        print(f"  Status: {status}")
    
    print("\n" + "="*70)
    print("HYPOTHESIS 10 TEST COMPLETE")
    print("="*70)
