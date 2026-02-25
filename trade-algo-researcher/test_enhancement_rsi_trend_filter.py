#!/usr/bin/env python3
"""
ENHANCEMENT TEST: RSI Mean Reversion + Trend Filter
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


def test_enhancement_trend_filter(sector, tickers):
    """Test RSI + 50-day SMA trend filter"""
    print(f"\n{'='*70}")
    print(f"ENHANCEMENT TEST: RSI + Trend Filter on {sector}")
    print(f"{'='*70}")
    print(f"Enhancement: Only trade in direction of 50-day SMA trend")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades_with_filter = []
    trades_without_filter = []  # Baseline for comparison
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        # Calculate indicators
        ticker_df['rsi'] = calculate_rsi(ticker_df['close'], 14)
        ticker_df['sma_50'] = ticker_df['close'].rolling(50).mean()
        ticker_df['volume_avg'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg']
        ticker_df['trend_up'] = ticker_df['close'] > ticker_df['sma_50']
        
        for i in range(50, len(ticker_df) - 10):
            row = ticker_df.iloc[i]
            
            # Base signal: RSI < 30 and volume spike
            if row['rsi'] < 30 and row['volume_ratio'] > 1.3:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + 10]['close']  # 10-day hold
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                # WITHOUT filter (baseline)
                trades_without_filter.append(net_return)
                
                # WITH trend filter: Only long in uptrend
                if row['trend_up']:  # Price > 50-day SMA
                    trades_with_filter.append(net_return)
    
    if len(trades_without_filter) < 30:
        print(f"❌ INSUFFICIENT TRADES")
        return None
    
    # Compare results
    returns_no_filter = pd.Series(trades_without_filter)
    returns_with_filter = pd.Series(trades_with_filter)
    
    # Calculate metrics
    def calc_metrics(returns, label):
        if len(returns) == 0 or returns.std() == 0:
            return None
        
        periods_per_year = 25  # 10-day hold
        return {
            'label': label,
            'trades': len(returns),
            'win_rate': (returns > 0).mean() * 100,
            'avg_return': returns.mean(),
            'sharpe': returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999,
            'max_dd': ((1 + returns/100).cumprod() / (1 + returns/100).cumprod().expanding().max() - 1).min() * 100
        }
    
    baseline = calc_metrics(returns_no_filter, "Without Filter (Baseline)")
    enhanced = calc_metrics(returns_with_filter, "With Trend Filter")
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"\n  {'Metric':<20} {'Baseline':<15} {'Enhanced':<15} {'Change'}")
    print(f"  {'-'*60}")
    
    if baseline and enhanced:
        for key in ['trades', 'win_rate', 'avg_return', 'sharpe', 'max_dd']:
            b_val = baseline[key]
            e_val = enhanced[key]
            if key == 'trades':
                change = f"{e_val - b_val:+.0f}"
                print(f"  {key:<20} {b_val:<15.0f} {e_val:<15.0f} {change}")
            else:
                change = f"{e_val - b_val:+.2f}"
                print(f"  {key:<20} {b_val:<15.2f} {e_val:<15.2f} {change}")
        
        print(f"\n🎯 CONCLUSION:")
        
        sharpe_improvement = enhanced['sharpe'] - baseline['sharpe']
        win_rate_improvement = enhanced['win_rate'] - baseline['win_rate']
        
        if enhanced['sharpe'] >= 1.0 and enhanced['win_rate'] >= 55:
            print(f"  ✅ VALIDATED - Enhancement works!")
            print(f"  Sharpe improved: {baseline['sharpe']:.2f} → {enhanced['sharpe']:.2f} (+{sharpe_improvement:.2f})")
            print(f"  Win rate improved: {baseline['win_rate']:.1f}% → {enhanced['win_rate']:.1f}% (+{win_rate_improvement:.1f}%)")
            status = "VALIDATED"
        elif sharpe_improvement > 0.1 or win_rate_improvement > 2:
            print(f"  🧪 IMPROVED - Trend filter helps")
            print(f"  Sharpe improved: {baseline['sharpe']:.2f} → {enhanced['sharpe']:.2f}")
            status = "IMPROVED"
        else:
            print(f"  ❌ NO IMPROVEMENT - Trend filter doesn't help")
            print(f"  Sharpe: {baseline['sharpe']:.2f} → {enhanced['sharpe']:.2f}")
            status = "NO_EFFECT"
        
        return {
            'baseline': baseline,
            'enhanced': enhanced,
            'sharpe_delta': sharpe_improvement,
            'win_rate_delta': win_rate_improvement,
            'status': status
        }
    
    return None


if __name__ == "__main__":
    print("="*70)
    print("ENHANCEMENT TEST: RSI + Trend Filter")
    print("From: memory/strategies/rsi_mean_reversion.md")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            result = test_enhancement_trend_filter(sector_name, sectors[sector_name])
            
            if result:
                print(f"\n{'='*70}")
                print(f"SUMMARY for {sector_name}:")
                print(f"  Baseline Sharpe: {result['baseline']['sharpe']:.2f}")
                print(f"  Enhanced Sharpe: {result['enhanced']['sharpe']:.2f}")
                print(f"  Improvement: {result['sharpe_delta']:+.2f}")
                print(f"  Status: {result['status']}")
    
    print("\n" + "="*70)
    print("ENHANCEMENT TEST COMPLETE")
    print("Update memory/strategies/rsi_mean_reversion.md with results")
    print("="*70)
