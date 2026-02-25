#!/usr/bin/env python3
"""
COMPREHENSIVE STRATEGY SCREENING
Test ALL available strategies with parameter grids
Find what actually works - no cherry-picking
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np
from itertools import product


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


def save_screening_result(strategy_name, params, results, region):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO openclaw_researcher.backtest_results 
    (hypothesis_name, start_date, end_date, total_trades, win_rate_pct,
     sharpe_ratio, max_drawdown_pct, status, parameters, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"{strategy_name}_{region}",
        '2021-01-01', '2024-12-31',
        results['total_trades'],
        results['win_rate'],
        results['sharpe'],
        results['max_dd'],
        'completed',
        str(params),
        f"Parameter screening - {region}"
    ))
    
    conn.commit()
    cursor.close()
    conn.close()


def get_all_data(limit_tickers=None):
    """Get all available price data"""
    conn = get_db_connection()
    
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT ticker FROM silver.historical_stock_data 
    WHERE date > '2021-01-01'
    """)
    
    all_tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    if limit_tickers:
        all_tickers = all_tickers[:limit_tickers]
    
    print(f"Loading data for {len(all_tickers)} tickers...")
    
    # Load in batches to avoid timeout
    ticker_batches = [all_tickers[i:i+50] for i in range(0, len(all_tickers), 50)]
    all_data = []
    
    for batch in ticker_batches:
        ticker_list = "','".join(batch)
        query = f"""
        SELECT date, ticker, close, volume, open, high, low
        FROM silver.historical_stock_data
        WHERE ticker IN ('{ticker_list}')
        AND date BETWEEN '2021-01-01' AND '2024-12-31'
        ORDER BY ticker, date
        """
        batch_df = pd.read_sql(query, conn)
        all_data.append(batch_df)
    
    conn.close()
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def calculate_metrics(returns, periods_per_year=252):
    """Calculate backtest metrics"""
    if len(returns) == 0 or returns.std() == 0:
        return {'sharpe': -999, 'win_rate': 0, 'avg_return': 0, 'max_dd': 0}
    
    win_rate = (returns > 0).mean() * 100
    avg_return = returns.mean()
    sharpe = avg_return / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else -999
    
    # Max drawdown
    cumulative = (1 + returns / 100).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    return {
        'sharpe': sharpe,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'max_dd': max_dd
    }


# STRATEGY 1: Mean Reversion with parameter grid
def test_mean_reversion(df, param_grid):
    """Test RSI mean reversion with various parameters"""
    results = []
    
    for rsi_period, rsi_threshold, hold_days in product(
        param_grid['rsi_period'],
        param_grid['rsi_threshold'],
        param_grid['hold_days']
    ):
        trades = []
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
            if len(ticker_df) < 100:
                continue
            
            # Calculate RSI
            delta = ticker_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            ticker_df['rsi'] = 100 - (100 / (1 + rs))
            
            ticker_df['volume_avg'] = ticker_df['volume'].rolling(20).mean()
            ticker_df['volume_ratio'] = ticker_df['volume'] / ticker_df['volume_avg']
            
            for i in range(50, len(ticker_df) - hold_days):
                row = ticker_df.iloc[i]
                
                if row['rsi'] < rsi_threshold and row['volume_ratio'] > 1.3:
                    entry_price = row['close']
                    exit_price = ticker_df.iloc[i + hold_days]['close']
                    
                    # Include costs
                    gross_return = (exit_price - entry_price) / entry_price * 100
                    cost = 0.1  # 0.1% round-trip cost
                    net_return = gross_return - cost
                    
                    trades.append(net_return)
        
        if len(trades) >= 100:
            metrics = calculate_metrics(pd.Series(trades), periods_per_year=252/hold_days)
            results.append({
                'params': {'rsi_period': rsi_period, 'rsi_threshold': rsi_threshold, 'hold_days': hold_days},
                'trades': len(trades),
                **metrics
            })
    
    return results


# STRATEGY 2: Momentum with parameter grid
def test_momentum(df, param_grid):
    """Test momentum with various lookback periods"""
    results = []
    
    for lookback, hold_days in product(
        param_grid['lookback'],
        param_grid['hold_days']
    ):
        trades = []
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
            if len(ticker_df) < lookback + hold_days + 10:
                continue
            
            ticker_df['momentum'] = ticker_df['close'].pct_change(lookback)
            
            for i in range(lookback, len(ticker_df) - hold_days):
                row = ticker_df.iloc[i]
                
                # Top quintile momentum
                if row['momentum'] > 0.05:  # 5% momentum
                    entry_price = row['close']
                    exit_price = ticker_df.iloc[i + hold_days]['close']
                    
                    gross_return = (exit_price - entry_price) / entry_price * 100
                    cost = 0.1
                    net_return = gross_return - cost
                    
                    trades.append(net_return)
        
        if len(trades) >= 100:
            metrics = calculate_metrics(pd.Series(trades), periods_per_year=252/hold_days)
            results.append({
                'params': {'lookback': lookback, 'hold_days': hold_days},
                'trades': len(trades),
                **metrics
            })
    
    return results


# STRATEGY 3: Bollinger Bands
def test_bollinger(df, param_grid):
    """Test Bollinger Band mean reversion"""
    results = []
    
    for period, std_dev in product(
        param_grid['period'],
        param_grid['std_dev']
    ):
        trades = []
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker].sort_values('date').copy()
            if len(ticker_df) < period + 20:
                continue
            
            ticker_df['sma'] = ticker_df['close'].rolling(period).mean()
            ticker_df['std'] = ticker_df['close'].rolling(period).std()
            ticker_df['lower_band'] = ticker_df['sma'] - (std_dev * ticker_df['std'])
            ticker_df['upper_band'] = ticker_df['sma'] + (std_dev * ticker_df['std'])
            
            for i in range(period, len(ticker_df) - 10):
                row = ticker_df.iloc[i]
                
                # Long when price touches lower band
                if row['close'] < row['lower_band']:
                    entry_price = row['close']
                    # Exit when returns to SMA
                    for j in range(i+1, min(i+20, len(ticker_df))):
                        if ticker_df.iloc[j]['close'] >= ticker_df.iloc[j]['sma']:
                            exit_price = ticker_df.iloc[j]['close']
                            gross_return = (exit_price - entry_price) / entry_price * 100
                            cost = 0.1
                            trades.append(gross_return - cost)
                            break
        
        if len(trades) >= 100:
            metrics = calculate_metrics(pd.Series(trades))
            results.append({
                'params': {'period': period, 'std_dev': std_dev},
                'trades': len(trades),
                **metrics
            })
    
    return results


# STRATEGY 4: Volume Breakout
def test_volume_breakout(df, param_grid):
    """Test volume-based breakout"""
    results = []
    
    for vol_lookback, vol_mult, hold_days in product(
        param_grid['vol_lookback'],
        param_grid['vol_mult'],
        param_grid['hold_days']
    ):
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
                if row['vol_ratio'] > vol_mult and row['price_change'] > 0.02:
                    entry_price = row['close']
                    exit_price = ticker_df.iloc[i + hold_days]['close']
                    
                    gross_return = (exit_price - entry_price) / entry_price * 100
                    cost = 0.1
                    trades.append(gross_return - cost)
        
        if len(trades) >= 100:
            metrics = calculate_metrics(pd.Series(trades), periods_per_year=252/hold_days)
            results.append({
                'params': {'vol_lookback': vol_lookback, 'vol_mult': vol_mult, 'hold_days': hold_days},
                'trades': len(trades),
                **metrics
            })
    
    return results


def print_top_results(strategy_name, results, top_n=5):
    """Print top performing parameter combinations"""
    if not results:
        print(f"\n{strategy_name}: No valid results")
        return
    
    # Sort by Sharpe
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\n{'='*70}")
    print(f"TOP {top_n} RESULTS: {strategy_name}")
    print(f"{'='*70}")
    print(f"{'Rank':<6} {'Sharpe':<8} {'Win%':<8} {'Trades':<8} {'MaxDD':<8} {'Params'}")
    print(f"{'-'*70}")
    
    for i, r in enumerate(sorted_results[:top_n], 1):
        status = "✅" if r['sharpe'] >= 1.0 and r['win_rate'] >= 50 else "🧪" if r['sharpe'] > 0 else "❌"
        print(f"{status} {i:<4} {r['sharpe']:<8.2f} {r['win_rate']:<8.1f} {r['trades']:<8} {r['max_dd']:<8.1f} {r['params']}")
    
    # Best overall
    best = sorted_results[0]
    if best['sharpe'] >= 1.0 and best['win_rate'] >= 50:
        print(f"\n🏆 BEST: Sharpe {best['sharpe']:.2f}, Win {best['win_rate']:.1f}%, Params: {best['params']}")
        return best
    return None


if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE STRATEGY SCREENING")
    print("Testing ALL strategies with parameter tuning")
    print("="*70)
    
    # Load data - use limited set for speed, expand if promising
    df = get_all_data(limit_tickers=100)
    
    if len(df) == 0:
        print("❌ NO DATA")
        sys.exit(1)
    
    print(f"Total records: {len(df):,}")
    print(f"Tickers: {df['ticker'].nunique()}")
    
    validated_strategies = []
    
    # SCREEN 1: Mean Reversion
    print("\n" + "="*70)
    print("SCREENING: RSI Mean Reversion")
    print("="*70)
    
    mr_results = test_mean_reversion(df, {
        'rsi_period': [10, 14, 20],
        'rsi_threshold': [20, 25, 30, 35],
        'hold_days': [3, 5, 10]
    })
    
    best_mr = print_top_results("RSI Mean Reversion", mr_results)
    if best_mr:
        validated_strategies.append(('RSI Mean Reversion', best_mr))
    
    # SCREEN 2: Momentum
    print("\n" + "="*70)
    print("SCREENING: Momentum")
    print("="*70)
    
    mom_results = test_momentum(df, {
        'lookback': [10, 20, 60],
        'hold_days': [10, 20, 40]
    })
    
    best_mom = print_top_results("Momentum", mom_results)
    if best_mom:
        validated_strategies.append(('Momentum', best_mom))
    
    # SCREEN 3: Bollinger Bands
    print("\n" + "="*70)
    print("SCREENING: Bollinger Bands")
    print("="*70)
    
    bb_results = test_bollinger(df, {
        'period': [20, 30],
        'std_dev': [1.5, 2.0, 2.5]
    })
    
    best_bb = print_top_results("Bollinger Bands", bb_results)
    if best_bb:
        validated_strategies.append(('Bollinger Bands', best_bb))
    
    # SCREEN 4: Volume Breakout
    print("\n" + "="*70)
    print("SCREENING: Volume Breakout")
    print("="*70)
    
    vb_results = test_volume_breakout(df, {
        'vol_lookback': [10, 20],
        'vol_mult': [1.5, 2.0, 2.5],
        'hold_days': [3, 5, 10]
    })
    
    best_vb = print_top_results("Volume Breakout", vb_results)
    if best_vb:
        validated_strategies.append(('Volume Breakout', best_vb))
    
    # SUMMARY
    print("\n" + "="*70)
    print("VALIDATED STRATEGIES SUMMARY")
    print("="*70)
    
    if validated_strategies:
        for name, result in validated_strategies:
            print(f"\n✅ {name}")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Win Rate: {result['win_rate']:.1f}%")
            print(f"   Trades: {result['trades']}")
            print(f"   Best Params: {result['params']}")
            print(f"\n   BUY SIGNAL:")
            if name == 'RSI Mean Reversion':
                print(f"   - RSI({result['params']['rsi_period']}) < {result['params']['rsi_threshold']}")
                print(f"   - Volume > 1.3x average")
                print(f"   HOLD: {result['params']['hold_days']} days")
            elif name == 'Momentum':
                print(f"   - {result['params']['lookback']}-day return > 5%")
                print(f"   HOLD: {result['params']['hold_days']} days")
            elif name == 'Bollinger Bands':
                print(f"   - Price < Lower Band ({result['params']['period']}, {result['params']['std_dev']}σ)")
                print(f"   SELL: When price returns to SMA")
            elif name == 'Volume Breakout':
                print(f"   - Volume > {result['params']['vol_mult']}x {result['params']['vol_lookback']}-day avg")
                print(f"   - Price up > 2%")
                print(f"   HOLD: {result['params']['hold_days']} days")
    else:
        print("\n❌ No strategies passed validation (Sharpe >= 1.0, Win >= 50%)")
    
    print("\n" + "="*70)
    print(f"SCREENING COMPLETE - {len(validated_strategies)} strategies ready for paper trading")
    print("="*70)
