#!/usr/bin/env python3
"""
ENHANCEMENT TEST 2: Tighter RSI Threshold (25 vs 30)
From memory/strategies/rsi_mean_reversion.md
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


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def test_enhancement_rsi_threshold(sector, tickers, rsi_threshold):
    """Test RSI mean reversion with specific threshold"""
    print(f"\n{'='*70}")
    print(f"ENHANCEMENT TEST: RSI Threshold = {rsi_threshold} on {sector}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        ticker_df['rsi'] = calculate_rsi(ticker_df['close'], 14)
        ticker_df['volume_avg'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg']
        
        for i in range(50, len(ticker_df) - 5):
            row = ticker_df.iloc[i]
            
            # Test with specified threshold
            if row['rsi'] < rsi_threshold and row['volume_ratio'] > 1.3:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + 5]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append(net_return)
    
    if len(trades) < 30:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None
    
    returns = pd.Series(trades)
    
    periods_per_year = 50  # 5-day hold
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
    results = {
        'trades': len(trades),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_dd': ((1 + returns/100).cumprod() / (1 + returns/100).cumprod().expanding().max() - 1).min() * 100
    }
    
    print(f"\n📊 RESULTS (RSI < {rsi_threshold}):")
    print(f"  Trades:      {results['trades']}")
    print(f"  Win Rate:    {results['win_rate']:.1f}%")
    print(f"  Avg Return:  {results['avg_return']:.2f}%")
    print(f"  Sharpe:      {results['sharpe']:.2f}")
    print(f"  Max DD:      {results['max_dd']:.2f}%")
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("ENHANCEMENT TEST 2: Tighter RSI Threshold")
    print("From: memory/strategies/rsi_mean_reversion.md")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name not in sectors:
            continue
        
        print(f"\n{'='*70}")
        print(f"Testing {sector_name} with different RSI thresholds")
        print(f"{'='*70}")
        
        # Test different thresholds
        thresholds = [20, 25, 30, 35]
        results_list = []
        
        for threshold in thresholds:
            result = test_enhancement_rsi_threshold(sector_name, sectors[sector_name], threshold)
            if result:
                results_list.append((threshold, result))
        
        # Compare
        if results_list:
            print(f"\n{'='*70}")
            print(f"COMPARISON for {sector_name}:")
            print(f"{'='*70}")
            print(f"{'RSI Threshold':<15} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
            print(f"{'-'*60}")
            
            best = None
            for threshold, result in results_list:
                status = "✅" if result['sharpe'] >= 1.0 else "🧪" if result['sharpe'] > 0.5 else "❌"
                print(f"{status} RSI < {threshold:<12} {result['trades']:<10} {result['win_rate']:<10.1f} {result['sharpe']:<10.2f}")
                
                if best is None or result['sharpe'] > best[1]['sharpe']:
                    best = (threshold, result)
            
            if best:
                print(f"\n🏆 BEST: RSI < {best[0]} with Sharpe {best[1]['sharpe']:.2f}")
    
    print("\n" + "="*70)
    print("ENHANCEMENT TEST 2 COMPLETE")
    print("Update memory/strategies/rsi_mean_reversion.md with results")
    print("="*70)
