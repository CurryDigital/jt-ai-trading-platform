#!/usr/bin/env python3
"""
HYPOTHESIS 5: Moving Average Crossover by Industry
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


def test_ma_crossover_detailed(sector, tickers, params):
    """Test MA crossover with full analysis"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 5: MA Crossover on {sector}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    if len(df) == 0:
        return None, None
    
    print(f"Tickers: {df['ticker'].nunique()}, Records: {len(df):,}")
    
    fast_ma = params['fast_ma']
    slow_ma = params['slow_ma']
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < slow_ma + 20:
            continue
        
        ticker_df['fast'] = ticker_df['close'].rolling(fast_ma).mean()
        ticker_df['slow'] = ticker_df['close'].rolling(slow_ma).mean()
        ticker_df['position'] = np.where(ticker_df['fast'] > ticker_df['slow'], 1, 0)
        ticker_df['signal'] = ticker_df['position'].diff()
        
        for i in range(slow_ma, len(ticker_df) - 1):
            # Bullish crossover
            if ticker_df['signal'].iloc[i] == 1:
                entry_price = ticker_df['close'].iloc[i]
                
                # Exit on bearish crossover or after 20 days
                exit_price = None
                for j in range(i+1, min(i+21, len(ticker_df))):
                    if ticker_df['signal'].iloc[j] == -1:
                        exit_price = ticker_df['close'].iloc[j]
                        break
                
                if exit_price is None:
                    exit_price = ticker_df.iloc[min(i+20, len(ticker_df)-1)]['close']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append({'ticker': ticker, 'return': net_return})
    
    if len(trades) < 30:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['return']
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(12) if returns.std() > 0 else -999  # Monthly
    
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
        'profit_factor': abs(winners.sum() / losers.sum()) if losers.sum() != 0 else 999
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
    
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 50:
        print(f"  ✅ VALIDATED - Trend following works")
        status = "VALIDATED"
    elif sharpe > 0.3 and win_rate >= 45:
        print(f"  🧪 TESTING - Weak trend signal")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Lagging indicator, too slow")
        status = "REJECTED"
    
    print(f"\n💡 ENHANCEMENT SUGGESTIONS:")
    if sharpe < 0:
        print(f"  - MA crossovers are lagging, markets have changed")
        print(f"  - Consider using EMA instead of SMA for faster response")
    if win_rate < 50:
        print(f"  - Add volume filter (only trade on high volume)")
    if results['avg_winner'] < abs(results['avg_loser']):
        print(f"  - Let winners run (trailing stop), cut losers quickly")
    if sharpe > 0.5:
        print(f"  - Try faster MAs (10/30 instead of 20/50)")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 5: Moving Average Crossover by Industry")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    all_results = []
    
    for sector_name in ['Tech', 'Equity']:
        if sector_name in sectors:
            results, status = test_ma_crossover_detailed(
                sector_name,
                sectors[sector_name],
                {'fast_ma': 20, 'slow_ma': 50}
            )
            if results:
                all_results.append((sector_name, results, status))
    
    print("\n" + "="*70)
    print("SUMMARY: MA Crossover by Industry")
    print("="*70)
    
    for sector, results, status in all_results:
        icon = "✅" if status == "VALIDATED" else "🧪" if status == "TESTING" else "❌"
        print(f"\n{icon} {sector}:")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Status: {status}")
