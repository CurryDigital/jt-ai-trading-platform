#!/usr/bin/env python3
"""
HYPOTHESIS 4: Volume Breakout Strategy by Industry
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


def test_volume_breakout_detailed(sector, tickers, params):
    """Test volume breakout with full analysis"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 4: Volume Breakout on {sector}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None, None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    vol_lookback = params['vol_lookback']
    vol_mult = params['vol_mult']
    price_change = params['price_change']
    hold_days = params['hold_days']
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < vol_lookback + 20:
            continue
        
        ticker_df['vol_avg'] = ticker_df['volume'].rolling(vol_lookback).mean()
        ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
        ticker_df['price_change'] = ticker_df['close'].pct_change()
        
        for i in range(vol_lookback, len(ticker_df) - hold_days):
            row = ticker_df.iloc[i]
            
            # Volume spike + price breakout
            if row['vol_ratio'] > vol_mult and row['price_change'] > price_change:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + hold_days]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append({
                    'ticker': ticker,
                    'vol_ratio': row['vol_ratio'],
                    'price_change': row['price_change'] * 100,
                    'return': net_return
                })
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['return']
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    periods_per_year = 252 / hold_days
    sharpe = avg_return / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    winners = returns[returns > 0]
    losers = returns[returns <= 0]
    
    results = {
        'sector': sector,
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'avg_winner': winners.mean() if len(winners) > 0 else 0,
        'avg_loser': losers.mean() if len(losers) > 0 else 0,
        'best_trade': returns.max(),
        'worst_trade': returns.min(),
        'profit_factor': abs(winners.sum() / losers.sum()) if losers.sum() != 0 else 999,
        'avg_vol_ratio': trades_df['vol_ratio'].mean(),
        'avg_price_change': trades_df['price_change'].mean()
    }
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Total Trades:     {results['total_trades']}")
    print(f"  Win Rate:         {results['win_rate']:.1f}%")
    print(f"  Avg Return:       {results['avg_return']:.2f}%")
    print(f"  Sharpe Ratio:     {results['sharpe']:.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:.2f}%")
    print(f"  Avg Winner:       {results['avg_winner']:.2f}%")
    print(f"  Avg Loser:        {results['avg_loser']:.2f}%")
    print(f"  Profit Factor:    {results['profit_factor']:.2f}")
    print(f"  Avg Vol Ratio:    {results['avg_vol_ratio']:.2f}x")
    print(f"  Avg Price Move:   {results['avg_price_change']:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 50:
        print(f"  ✅ VALIDATED - Strong volume signal")
        status = "VALIDATED"
    elif sharpe > 0.5 and win_rate >= 45:
        print(f"  🧪 TESTING - Moderate signal")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Volume does not predict continuation")
        status = "REJECTED"
    
    print(f"\n💡 ENHANCEMENT SUGGESTIONS:")
    if win_rate < 50:
        print(f"  - Volume spikes may be distribution (selling), not accumulation")
    if results['avg_price_change'] > 5:
        print(f"  - Entry too late after move, try 1% threshold instead of 2%")
    if max_dd < -50:
        print(f"  - Add stop loss at -3% to catch false breakouts")
    if sharpe > 0.8:
        print(f"  - Strong results, try holding longer (5 days vs 3)")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 4: Volume Breakout by Industry")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    all_results = []
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            results, status = test_volume_breakout_detailed(
                sector_name,
                sectors[sector_name],
                {'vol_lookback': 20, 'vol_mult': 2.0, 'price_change': 0.02, 'hold_days': 3}
            )
            if results:
                all_results.append((sector_name, results, status))
    
    print("\n" + "="*70)
    print("SUMMARY: Volume Breakout by Industry")
    print("="*70)
    
    for sector, results, status in all_results:
        icon = "✅" if status == "VALIDATED" else "🧪" if status == "TESTING" else "❌"
        print(f"\n{icon} {sector}:")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Status: {status}")
