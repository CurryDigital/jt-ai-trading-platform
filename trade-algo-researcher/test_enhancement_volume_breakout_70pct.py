#!/usr/bin/env python3
"""
ENHANCEMENT: Volume Breakout - Push to 70%+ Win Rate
Target: Improve from 56% to 70%+ win rate
Methods: Add profit targets, trailing stops, entry timing
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


def test_volume_breakout_enhanced(sector, tickers, params):
    """Test volume breakout with enhanced exits"""
    print(f"\n{'='*70}")
    print(f"ENHANCEMENT: Volume Breakout on {sector}")
    print(f"Exit Strategy: {params['exit_type']}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    vol_lookback = 20
    vol_mult = 2.0
    price_change_threshold = 0.02
    
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
            
            # Entry signal
            if row['vol_ratio'] > vol_mult and row['price_change'] > price_change_threshold:
                entry_price = row['close']
                
                # Different exit strategies
                if params['exit_type'] == 'time':
                    # Original: hold 3 days
                    exit_price = ticker_df.iloc[i + 3]['close']
                    
                elif params['exit_type'] == 'profit_target':
                    # Exit at +5% profit
                    target_price = entry_price * 1.05
                    exit_price = None
                    for j in range(i+1, min(i+10, len(ticker_df))):
                        if ticker_df.iloc[j]['high'] >= target_price:
                            exit_price = target_price
                            break
                    if exit_price is None:
                        exit_price = ticker_df.iloc[min(i+10, len(ticker_df)-1)]['close']
                        
                elif params['exit_type'] == 'trailing_stop':
                    # Trailing stop at -3%
                    exit_price = None
                    highest_price = entry_price
                    for j in range(i+1, min(i+10, len(ticker_df))):
                        current_price = ticker_df.iloc[j]['close']
                        if current_price > highest_price:
                            highest_price = current_price
                        # Trailing stop: exit if down 3% from highest
                        if current_price < highest_price * 0.97:
                            exit_price = current_price
                            break
                    if exit_price is None:
                        exit_price = ticker_df.iloc[min(i+10, len(ticker_df)-1)]['close']
                
                elif params['exit_type'] == 'combined':
                    # Profit target + Trailing stop
                    target_price = entry_price * 1.05
                    stop_price = entry_price * 0.97
                    exit_price = None
                    
                    for j in range(i+1, min(i+10, len(ticker_df))):
                        current_price = ticker_df.iloc[j]['close']
                        # Take profit
                        if current_price >= target_price:
                            exit_price = target_price
                            break
                        # Stop loss
                        if current_price <= stop_price:
                            exit_price = stop_price
                            break
                    
                    if exit_price is None:
                        exit_price = ticker_df.iloc[min(i+10, len(ticker_df)-1)]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1  # 0.1% cost
                
                trades.append(net_return)
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    periods_per_year = 252 / 5  # ~5 day avg hold
    sharpe = avg_return / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    winners = returns[returns > 0]
    losers = returns[returns <= 0]
    
    results = {
        'exit_type': params['exit_type'],
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'avg_winner': winners.mean() if len(winners) > 0 else 0,
        'avg_loser': losers.mean() if len(losers) > 0 else 0,
        'profit_factor': abs(winners.sum() / losers.sum()) if losers.sum() != 0 else 999
    }
    
    print(f"\n📊 RESULTS ({params['exit_type']}):")
    print(f"  Trades:      {results['trades']}")
    print(f"  Win Rate:    {results['win_rate']:.1f}%")
    print(f"  Avg Return:  {results['avg_return']:.2f}%")
    print(f"  Sharpe:      {results['sharpe']:.2f}")
    print(f"  Max DD:      {results['max_dd']:.2f}%")
    print(f"  Avg Winner:  {results['avg_winner']:.2f}%")
    print(f"  Avg Loser:   {results['avg_loser']:.2f}%")
    print(f"  Profit Fac:  {results['profit_factor']:.2f}")
    
    # Target: 70% win rate
    if win_rate >= 70:
        print(f"\n✅ TARGET ACHIEVED: Win rate {win_rate:.1f}% >= 70%")
    elif win_rate >= 65:
        print(f"\n🧪 CLOSE: Win rate {win_rate:.1f}% (need 70%)")
    else:
        print(f"\n❌ NEEDS WORK: Win rate {win_rate:.1f}% (target 70%)")
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("ENHANCEMENT: Volume Breakout - Push to 70%+ Win Rate")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    all_results = []
    
    # Test different exit strategies on Tech sector
    if 'Tech' in sectors:
        print(f"\n{'='*70}")
        print("Testing different exit strategies on Tech sector")
        print(f"{'='*70}")
        
        exit_strategies = [
            {'exit_type': 'time'},           # Baseline
            {'exit_type': 'profit_target'},  # Exit at +5%
            {'exit_type': 'trailing_stop'},  # Trailing -3%
            {'exit_type': 'combined'}        # +5% target / -3% stop
        ]
        
        for params in exit_strategies:
            result = test_volume_breakout_enhanced('Tech', sectors['Tech'], params)
            if result:
                all_results.append((params['exit_type'], result))
        
        # Compare
        if all_results:
            print(f"\n{'='*70}")
            print("COMPARISON: Exit Strategies")
            print(f"{'='*70}")
            print(f"{'Exit Type':<20} {'Trades':<10} {'Win%':<10} {'Sharpe':<10} {'Status'}")
            print(f"{'-'*60}")
            
            for exit_type, result in all_results:
                status = "✅" if result['win_rate'] >= 70 else "🧪" if result['win_rate'] >= 60 else "❌"
                print(f"{status} {exit_type:<18} {result['trades']:<10} {result['win_rate']:<10.1f} {result['sharpe']:<10.2f}")
            
            # Best by win rate
            best_wr = max(all_results, key=lambda x: x[1]['win_rate'])
            print(f"\n🏆 BEST WIN RATE: {best_wr[0]} with {best_wr[1]['win_rate']:.1f}%")
            
            # Best by Sharpe
            best_sharpe = max(all_results, key=lambda x: x[1]['sharpe'])
            print(f"🏆 BEST SHARPE: {best_sharpe[0]} with {best_sharpe[1]['sharpe']:.2f}")
    
    print("\n" + "="*70)
    print("ENHANCEMENT TEST COMPLETE")
    print("Update memory/strategies/volume_breakout.md")
    print("="*70)
