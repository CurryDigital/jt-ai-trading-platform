#!/usr/bin/env python3
"""
ENHANCEMENT 2: Volume Breakout - Tighter Entry Criteria
Target: Push from 67.7% to 70%+ win rate
Method: Volume > 2.5x, Price move > 3%
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
    SELECT date, ticker, close, volume, high, low
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def test_volume_breakout_tighter(sector, tickers, vol_mult, price_threshold):
    """Test with tighter entry criteria"""
    print(f"\n{'='*70}")
    print(f"Volume Breakout: {sector}")
    print(f"Params: Volume > {vol_mult}x, Price up > {price_threshold}%")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    vol_lookback = 20
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        ticker_df['vol_avg'] = ticker_df['volume'].rolling(vol_lookback).mean()
        ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
        ticker_df['price_change'] = ticker_df['close'].pct_change()
        
        for i in range(vol_lookback, len(ticker_df) - 20):
            row = ticker_df.iloc[i]
            
            # Entry: Tighter criteria
            if (row['vol_ratio'] > vol_mult and 
                row['price_change'] > price_threshold):
                
                entry_price = row['close']
                target_price = entry_price * 1.05  # 5% profit target
                
                # Look for profit target or max 10 days
                exit_price = None
                for j in range(i+1, min(i+11, len(ticker_df))):
                    if ticker_df.iloc[j]['high'] >= target_price:
                        exit_price = target_price
                        break
                
                if exit_price is None:
                    exit_price = ticker_df.iloc[min(i+10, len(ticker_df)-1)]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append(net_return)
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    periods_per_year = 252 / 5
    sharpe = avg_return / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    winners = returns[returns > 0]
    losers = returns[returns <= 0]
    
    results = {
        'params': f"Vol>{vol_mult}x, Price>{price_threshold}%",
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_dd': max_dd
    }
    
    print(f"\n📊 RESULTS:")
    print(f"  Trades:     {results['trades']}")
    print(f"  Win Rate:   {results['win_rate']:.1f}%")
    print(f"  Avg Return: {results['avg_return']:.2f}%")
    print(f"  Sharpe:     {results['sharpe']:.2f}")
    print(f"  Max DD:     {results['max_dd']:.2f}%")
    
    if win_rate >= 70:
        print(f"\n✅ TARGET ACHIEVED: {win_rate:.1f}% >= 70%")
    elif win_rate >= 65:
        print(f"\n🧪 CLOSE: {win_rate:.1f}% (need 70%)")
    else:
        print(f"\n❌ NEEDS WORK: {win_rate:.1f}%")
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("ENHANCEMENT 2: Volume Breakout - Tighter Entry")
    print("Goal: Push from 67.7% to 70%+ win rate")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    all_results = []
    
    # Test different combinations on Tech sector
    if 'Tech' in sectors:
        print(f"\n{'='*70}")
        print("Testing parameter combinations")
        print(f"{'='*70}")
        
        param_combos = [
            (2.0, 0.02),  # Baseline (from enhancement 1)
            (2.5, 0.02),  # Higher volume, same price
            (2.0, 0.03),  # Same volume, higher price
            (2.5, 0.03),  # Both tighter
            (3.0, 0.02),  # Much higher volume
            (2.0, 0.04),  # Much higher price
        ]
        
        for vol_mult, price_thresh in param_combos:
            result = test_volume_breakout_tighter('Tech', sectors['Tech'], vol_mult, price_thresh)
            if result:
                all_results.append((vol_mult, price_thresh, result))
        
        # Comparison table
        if all_results:
            print(f"\n{'='*70}")
            print("COMPARISON: Parameter Combinations")
            print(f"{'='*70}")
            print(f"{'Volume':<10} {'Price%':<10} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
            print(f"{'-'*60}")
            
            for vol, price, r in all_results:
                status = "✅" if r['win_rate'] >= 70 else "🧪" if r['win_rate'] >= 65 else "❌"
                print(f"{status} {vol:<8.1f} {price*100:<8.1f} {r['trades']:<10} {r['win_rate']:<10.1f} {r['sharpe']:<10.2f}")
            
            # Best by win rate
            best_wr = max(all_results, key=lambda x: x[2]['win_rate'])
            print(f"\n🏆 BEST WIN RATE: Vol>{best_wr[0]}x, Price>{best_wr[1]*100:.0f}% → {best_wr[2]['win_rate']:.1f}%")
            
            # Best by Sharpe
            best_sharpe = max(all_results, key=lambda x: x[2]['sharpe'])
            print(f"🏆 BEST SHARPE: Vol>{best_sharpe[0]}x, Price>{best_sharpe[1]*100:.0f}% → {best_sharpe[2]['sharpe']:.2f}")
    
    print("\n" + "="*70)
    print("ENHANCEMENT 2 COMPLETE")
    print("="*70)
