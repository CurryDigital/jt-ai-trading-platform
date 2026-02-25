#!/usr/bin/env python3
"""
HYPOTHESIS 2: Bollinger Bands Mean Reversion by Industry
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
    SELECT DISTINCT ticker, sector 
    FROM gold.stock_metrics 
    WHERE sector IS NOT NULL
    AND date > '2023-01-01'
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
    SELECT date, ticker, close, volume, open
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '{start}' AND '{end}'
    ORDER BY ticker, date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df


def test_bollinger_detailed(sector, tickers, params):
    """Test Bollinger Bands with full analysis"""
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS 2: Bollinger Bands on {sector}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    
    if len(df) == 0:
        print(f"❌ NO DATA FOR {sector}")
        return None, None
    
    print(f"Tickers tested: {df['ticker'].nunique()}")
    print(f"Data records: {len(df):,}")
    
    period = params['period']
    std_dev = params['std_dev']
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < period + 20:
            continue
        
        # Calculate Bollinger Bands
        ticker_df['sma'] = ticker_df['close'].rolling(period).mean()
        ticker_df['std'] = ticker_df['close'].rolling(period).std()
        ticker_df['lower'] = ticker_df['sma'] - (std_dev * ticker_df['std'])
        ticker_df['upper'] = ticker_df['sma'] + (std_dev * ticker_df['std'])
        
        for i in range(period, len(ticker_df) - 1):
            row = ticker_df.iloc[i]
            
            # Long when price touches lower band
            if row['close'] < row['lower']:
                entry_price = row['close']
                entry_date = ticker_df['date'].iloc[i]
                
                # Exit when returns to SMA or 20 days max
                exit_price = None
                exit_date = None
                for j in range(i+1, min(i+21, len(ticker_df))):
                    if ticker_df.iloc[j]['close'] >= ticker_df.iloc[j]['sma']:
                        exit_price = ticker_df.iloc[j]['close']
                        exit_date = ticker_df.iloc[j]['date']
                        break
                
                if exit_price is None:
                    exit_price = ticker_df.iloc[min(i+20, len(ticker_df)-1)]['close']
                    exit_date = ticker_df.iloc[min(i+20, len(ticker_df)-1)]['date']
                
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1  # 0.1% cost
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': net_return
                })
    
    if len(trades) < 30:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None, None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['return']
    
    # Metrics
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = returns.mean() / returns.std() * np.sqrt(252/10) if returns.std() > 0 else -999
    
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min() * 100
    
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
    
    # Print results
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"  Total Trades:     {results['total_trades']}")
    print(f"  Win Rate:         {results['win_rate']:.1f}%")
    print(f"  Avg Return:       {results['avg_return']:.2f}%")
    print(f"  Sharpe Ratio:     {results['sharpe']:.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:.2f}%")
    print(f"  Avg Winner:       {results['avg_winner']:.2f}%")
    print(f"  Avg Loser:        {results['avg_loser']:.2f}%")
    print(f"  Profit Factor:    {results['profit_factor']:.2f}")
    print(f"  Best Trade:       {results['best_trade']:.2f}%")
    print(f"  Worst Trade:      {results['worst_trade']:.2f}%")
    
    # Conclusion
    print(f"\n🎯 CONCLUSION:")
    if sharpe >= 1.0 and win_rate >= 50:
        print(f"  ✅ VALIDATED - Strong performance in {sector}")
        status = "VALIDATED"
    elif sharpe > 0.5 and win_rate >= 45:
        print(f"  🧪 TESTING - Moderate edge, consider optimizations")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Does not work in {sector}")
        status = "REJECTED"
    
    # Enhancements
    print(f"\n💡 ENHANCEMENT SUGGESTIONS:")
    if win_rate >= 70 and sharpe > 2:
        print(f"  - Excellent results! Test with position sizing")
        print(f"  - Consider leverage (high win rate supports it)")
    elif win_rate < 55:
        print(f"  - Try wider bands (2.5σ or 3.0σ) for fewer, higher-quality signals")
    if max_dd < -30:
        print(f"  - Add stop loss at -5% to limit drawdowns")
    if results['avg_winner'] < abs(results['avg_loser']) * 1.3:
        print(f"  - Let winners run longer (trailing stop instead of SMA exit)")
    
    return results, status


if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 2: Bollinger Bands by Industry")
    print("="*70)
    
    sectors = get_tickers_by_sector()
    
    all_results = []
    
    # Test on Tech
    if 'Tech' in sectors:
        results, status = test_bollinger_detailed(
            'Tech',
            sectors['Tech'],
            {'period': 20, 'std_dev': 2.0}
        )
        if results:
            all_results.append(('Tech', results, status))
    
    # Test on Equity
    if 'Equity' in sectors:
        results, status = test_bollinger_detailed(
            'Equity',
            sectors['Equity'],
            {'period': 20, 'std_dev': 2.0}
        )
        if results:
            all_results.append(('Equity', results, status))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY: Bollinger Bands by Industry")
    print("="*70)
    
    for sector, results, status in all_results:
        icon = "✅" if status == "VALIDATED" else "🧪" if status == "TESTING" else "❌"
        print(f"\n{icon} {sector}:")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Status: {status}")
