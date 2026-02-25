#!/usr/bin/env python3
"""
INDUSTRY-SPECIFIC STRATEGY TESTING
Test one hypothesis at a time with detailed analysis
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
    """Get tickers grouped by sector from gold.stock_metrics"""
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
    """Get price data for tickers"""
    conn = get_db_connection()
    
    ticker_list = "','".join(tickers[:30])  # Limit to prevent timeout
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


def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def test_mean_reversion_detailed(sector, tickers, params):
    """Test mean reversion with full analysis"""
    print(f"\n{'='*70}")
    print(f"TESTING: RSI Mean Reversion on {sector}")
    print(f"{'='*70}")
    
    df = get_price_data(tickers)
    
    if len(df) == 0:
        print(f"❌ NO DATA FOR {sector}")
        return None
    
    print(f"Tickers tested: {df['ticker'].nunique()}")
    print(f"Data records: {len(df):,}")
    
    rsi_period = params['rsi_period']
    rsi_threshold = params['rsi_threshold']
    hold_days = params['hold_days']
    
    trades = []
    
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
        if len(ticker_df) < 100:
            continue
        
        ticker_df['rsi'] = calculate_rsi(ticker_df['close'], rsi_period)
        ticker_df['volume_avg'] = ticker_df['volume'].rolling(20).mean()
        ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg']
        
        for i in range(50, len(ticker_df) - hold_days):
            row = ticker_df.iloc[i]
            
            if row['rsi'] < rsi_threshold and row['volume_ratio'] > 1.3:
                entry_price = row['close']
                exit_price = ticker_df.iloc[i + hold_days]['close']
                
                # Include 0.1% transaction cost
                gross_return = (exit_price - entry_price) / entry_price * 100
                net_return = gross_return - 0.1
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': ticker_df['date'].iloc[i],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'rsi': row['rsi'],
                    'return': net_return
                })
    
    if len(trades) < 30:
        print(f"❌ INSUFFICIENT TRADES: {len(trades)}")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['return']
    
    # Calculate metrics
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    periods_per_year = 252 / hold_days
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
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
    
    # Print detailed analysis
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
        print(f"  ✅ VALIDATED - Strategy works in {sector}")
        status = "VALIDATED"
    elif sharpe > 0.5 and win_rate >= 45:
        print(f"  🧪 TESTING - Shows promise but needs refinement")
        status = "TESTING"
    else:
        print(f"  ❌ FAILED - Strategy does not work in {sector}")
        status = "REJECTED"
    
    # Enhancement suggestions
    print(f"\n💡 ENHANCEMENT SUGGESTIONS:")
    if win_rate < 50:
        print(f"  - Try lower RSI threshold (e.g., 25 instead of 30)")
    if sharpe < 1.0:
        print(f"  - Add trend filter (only trade in direction of 50-day SMA)")
    if max_dd < -20:
        print(f"  - Tighter stop loss (currently implied by hold period)")
    if results['avg_winner'] < abs(results['avg_loser']) * 1.5:
        print(f"  - Need better profit targets (R:R ratio too low)")
    
    if sharpe >= 1.0:
        print(f"  - Current params are optimal, consider position sizing")
    
    return results, status


# Run first hypothesis
if __name__ == "__main__":
    print("="*70)
    print("HYPOTHESIS 1: RSI Mean Reversion by Industry")
    print("="*70)
    
    # Get sectors
    sectors = get_tickers_by_sector()
    print(f"\nAvailable sectors: {list(sectors.keys())}")
    
    all_results = []
    
    # Test on Tech sector
    if 'Tech' in sectors:
        print("\n" + "="*70)
        results, status = test_mean_reversion_detailed(
            'Tech',
            sectors['Tech'],
            {'rsi_period': 14, 'rsi_threshold': 30, 'hold_days': 5}
        )
        if results:
            all_results.append(('Tech', results, status))
    
    # Test on Equity sector
    if 'Equity' in sectors:
        print("\n" + "="*70)
        results, status = test_mean_reversion_detailed(
            'Equity',
            sectors['Equity'],
            {'rsi_period': 14, 'rsi_threshold': 30, 'hold_days': 5}
        )
        if results:
            all_results.append(('Equity', results, status))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY: RSI Mean Reversion by Industry")
    print("="*70)
    
    for sector, results, status in all_results:
        icon = "✅" if status == "VALIDATED" else "🧪" if status == "TESTING" else "❌"
        print(f"\n{icon} {sector}:")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Status: {status}")
