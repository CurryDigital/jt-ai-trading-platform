#!/usr/bin/env python3
"""
ENHANCEMENT 3: RSI Mean Reversion - Push to 70% Win Rate
Target: Improve from 56-58% to 70%+
Methods: Add filters, profit targets, volume confirmation
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


def get_data_with_metrics(tickers, start='2022-01-01', end='2024-12-31'):
    conn = get_db_connection()
    ticker_list = "','".join(tickers[:30])
    
    price_query = f"""
    SELECT date, ticker, close, volume, high, low
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    prices = pd.read_sql(price_query, conn)
    
    rsi_query = f"""
    SELECT date, ticker, rsi_14
    FROM gold.stock_metrics
    WHERE ticker IN ('{ticker_list}') AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    rsi = pd.read_sql(rsi_query, conn)
    conn.close()
    
    df = prices.merge(rsi, on=['date', 'ticker'], how='inner')
    return df


def test_rsi_enhancement(sector, tickers, rsi_threshold, exit_type='time', vol_filter=False):
    """Test RSI with various enhancements"""
    print(f"\n{'='*70}")
    print(f"RSI Enhancement: {sector}")
    print(f"Params: RSI < {rsi_threshold}, Exit: {exit_type}, Vol Filter: {vol_filter}")
    print(f"{'='*70}")
    
    df = get_data_with_metrics(tickers)
    if len(df) == 0:
        return None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 50:
            continue
        
        # Calculate volume average if needed
        if vol_filter:
            ticker_df['vol_avg'] = ticker_df['volume'].rolling(20).mean()
            ticker_df['vol_ratio'] = ticker_df['volume'] / ticker_df['vol_avg']
        
        for i in range(25, len(ticker_df) - 15):
            rsi = ticker_df['rsi_14'].iloc[i]
            
            # Base signal: RSI oversold
            if pd.isna(rsi) or rsi >= rsi_threshold:
                continue
            
            # Optional volume filter
            if vol_filter:
                vol_ratio = ticker_df['vol_ratio'].iloc[i]
                if pd.isna(vol_ratio) or vol_ratio < 1.5:
                    continue
            
            entry_price = ticker_df['close'].iloc[i]
            
            # Different exit strategies
            if exit_type == 'time':
                exit_price = ticker_df['close'].iloc[i + 10]
                
            elif exit_type == 'profit_target':
                target = entry_price * 1.04  # 4% profit
                exit_price = None
                for j in range(i+1, min(i+15, len(ticker_df))):
                    if ticker_df['high'].iloc[j] >= target:
                        exit_price = target
                        break
                if exit_price is None:
                    exit_price = ticker_df['close'].iloc[min(i+10, len(ticker_df)-1)]
                    
            elif exit_type == 'rsi_recovery':
                # Exit when RSI recovers to 40
                exit_price = None
                for j in range(i+1, min(i+20, len(ticker_df))):
                    if ticker_df['rsi_14'].iloc[j] >= 40:
                        exit_price = ticker_df['close'].iloc[j]
                        break
                if exit_price is None:
                    exit_price = ticker_df['close'].iloc[min(i+10, len(ticker_df)-1)]
            
            gross_return = (exit_price - entry_price) / entry_price * 100
            net_return = gross_return - 0.1
            trades.append(net_return)
    
    if len(trades) < 50:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None
    
    returns = pd.Series(trades)
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(25) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    max_dd = ((cumulative - running_max) / running_max).min() * 100
    
    results = {
        'rsi_threshold': rsi_threshold,
        'exit_type': exit_type,
        'vol_filter': vol_filter,
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
    print("ENHANCEMENT 3: RSI Mean Reversion - Push to 70%")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT ticker, sector FROM gold.stock_metrics 
    WHERE sector IS NOT NULL AND date > '2023-01-01'
    """)
    sectors = {}
    for row in cursor.fetchall():
        ticker, sector = row
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(ticker)
    cursor.close()
    conn.close()
    
    all_results = []
    
    # Test different combinations on Tech sector
    if 'Tech' in sectors:
        print(f"\n{'='*70}")
        print("Testing RSI Enhancements")
        print(f"{'='*70}")
        
        test_configs = [
            # (rsi_threshold, exit_type, vol_filter)
            (25, 'time', False),           # Baseline
            (25, 'profit_target', False),  # Profit target
            (25, 'rsi_recovery', False),   # RSI recovery exit
            (20, 'time', False),           # Tighter RSI
            (20, 'profit_target', False),  # Tighter + profit
            (20, 'profit_target', True),   # Tighter + profit + volume
            (15, 'profit_target', False),  # Extreme RSI
        ]
        
        for rsi_thresh, exit, vol in test_configs:
            result = test_rsi_enhancement('Tech', sectors['Tech'], rsi_thresh, exit, vol)
            if result:
                all_results.append((rsi_thresh, exit, vol, result))
        
        # Comparison table
        if all_results:
            print(f"\n{'='*70}")
            print("COMPARISON: RSI Enhancements")
            print(f"{'='*70}")
            print(f"{'RSI':<8} {'Exit':<18} {'Vol':<6} {'Trades':<10} {'Win%':<10} {'Sharpe'}")
            print(f"{'-'*60}")
            
            for rsi, exit, vol, r in all_results:
                vol_str = "Yes" if vol else "No"
                status = "✅" if r['win_rate'] >= 70 else "🧪" if r['win_rate'] >= 60 else "❌"
                print(f"{status} {rsi:<6} {exit:<16} {vol_str:<4} {r['trades']:<10} {r['win_rate']:<10.1f} {r['sharpe']:.2f}")
            
            # Best by win rate
            best_wr = max(all_results, key=lambda x: x[3]['win_rate'])
            print(f"\n🏆 BEST WIN RATE: RSI <{best_wr[0]}, {best_wr[1]}, Vol={best_wr[2]} → {best_wr[3]['win_rate']:.1f}%")
    
    print("\n" + "="*70)
    print("ENHANCEMENT 3 COMPLETE")
    print("="*70)
