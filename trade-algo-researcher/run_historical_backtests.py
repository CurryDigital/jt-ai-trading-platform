#!/usr/bin/env python3
"""
Historical Backtest Engine using Silver Schema
Calculates indicators on-the-fly from OHLCV data
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

from db_backtest_engine import TradeAlgoDB, BacktestStorage
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_rsi(prices, window=14):
    """Calculate RSI for a price series"""
    deltas = prices.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=window).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(prices, window):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=window).mean()


def run_historical_rsi_backtest(
    tickers,
    start_date,
    end_date,
    rsi_entry=30,
    rsi_exit=50,
    volume_threshold=1.3,
    max_hold_days=5,
    stop_loss=0.03
):
    """
    Run RSI Mean Reversion backtest using silver.historical_stock_data
    Calculates RSI on-the-fly from price data
    """
    print(f"Running Historical RSI Backtest")
    print(f"Tickers: {len(tickers)}")
    print(f"Period: {start_date} to {end_date}")
    print("-" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    # Get OHLCV data from silver
    ticker_list = "','".join(tickers)
    sql = f"""
    SELECT date, ticker, open, high, low, close, volume
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY ticker, date
    """
    
    prices = db.query(sql)
    
    if len(prices) == 0:
        print("No data retrieved!")
        db.close()
        return None
    
    print(f"Retrieved {len(prices)} price records")
    
    trades = []
    
    for ticker in tickers:
        ticker_data = prices[prices['ticker'] == ticker].sort_values('date').copy()
        
        if len(ticker_data) < 50:  # Need enough data for RSI
            continue
        
        # Calculate RSI
        ticker_data['rsi_14'] = calculate_rsi(ticker_data['close'], 14)
        ticker_data['volume_sma_20'] = calculate_sma(ticker_data['volume'], 20)
        ticker_data['volume_ratio'] = ticker_data['volume'] / ticker_data['volume_sma_20']
        
        # Drop rows with NaN RSI
        ticker_data = ticker_data.dropna(subset=['rsi_14'])
        
        position = None
        entry_date = None
        entry_price = None
        entry_rsi = None
        
        for idx, row in ticker_data.iterrows():
            if position is None:
                # Look for entry: RSI < threshold
                if row['rsi_14'] < rsi_entry:
                    position = 'LONG'
                    entry_date = row['date']
                    entry_price = row['close']
                    entry_rsi = row['rsi_14']
            else:
                # Calculate P&L
                current_pnl = (row['close'] - entry_price) / entry_price
                hold_days = (row['date'] - entry_date).days if isinstance(row['date'], datetime) else 0
                
                # Exit conditions
                exit_rsi = row['rsi_14'] > rsi_exit
                exit_time = hold_days >= max_hold_days
                exit_stop = current_pnl < -stop_loss
                
                if exit_rsi or exit_time or exit_stop:
                    trades.append({
                        'ticker': ticker,
                        'entry_date': entry_date,
                        'exit_date': row['date'],
                        'entry_price': entry_price,
                        'exit_price': row['close'],
                        'entry_rsi': entry_rsi,
                        'exit_rsi': row['rsi_14'],
                        'pnl_pct': current_pnl * 100,
                        'hold_days': hold_days,
                        'exit_reason': 'RSI' if exit_rsi else ('TIME' if exit_time else 'STOP')
                    })
                    position = None
    
    db.close()
    
    if len(trades) == 0:
        print("No trades generated!")
        return None
    
    trades_df = pd.DataFrame(trades)
    
    # Calculate statistics
    results = {
        'total_trades': len(trades_df),
        'winning_trades': (trades_df['pnl_pct'] > 0).sum(),
        'losing_trades': (trades_df['pnl_pct'] <= 0).sum(),
        'win_rate': (trades_df['pnl_pct'] > 0).mean() * 100,
        'avg_return': trades_df['pnl_pct'].mean(),
        'total_return': trades_df['pnl_pct'].sum(),
        'max_drawdown': trades_df['pnl_pct'].min(),
        'best_trade': trades_df['pnl_pct'].max(),
        'avg_hold_days': trades_df['hold_days'].mean(),
        'trades': trades_df.to_dict('records')
    }
    
    # Calculate Sharpe (simplified)
    returns = trades_df['pnl_pct']
    if returns.std() > 0:
        results['sharpe'] = returns.mean() / returns.std() * np.sqrt(252 / results['avg_hold_days']) if results['avg_hold_days'] > 0 else 0
    else:
        results['sharpe'] = 0
    
    return results


def run_historical_momentum_backtest(
    tickers,
    start_date,
    end_date,
    lookback_days=20,
    hold_days=20,
    momentum_threshold=0.05
):
    """
    Run Momentum backtest using silver.historical_stock_data
    """
    print(f"\nRunning Historical Momentum Backtest")
    print(f"Lookback: {lookback_days} days, Hold: {hold_days} days")
    print("-" * 60)
    
    db = TradeAlgoDB()
    db.connect()
    
    # Get data
    ticker_list = "','".join(tickers)
    sql = f"""
    SELECT date, ticker, close
    FROM silver.historical_stock_data
    WHERE ticker IN ('{ticker_list}')
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY ticker, date
    """
    
    prices = db.query(sql)
    db.close()
    
    if len(prices) == 0:
        return None
    
    trades = []
    
    for ticker in tickers:
        ticker_data = prices[prices['ticker'] == ticker].sort_values('date')
        
        if len(ticker_data) < lookback_days + hold_days + 10:
            continue
        
        for i in range(lookback_days, len(ticker_data) - hold_days):
            # Calculate past return
            past_return = (ticker_data.iloc[i]['close'] / 
                          ticker_data.iloc[i - lookback_days]['close'] - 1)
            
            if past_return > momentum_threshold:
                # Future return
                future_return = (ticker_data.iloc[i + hold_days]['close'] / 
                                ticker_data.iloc[i]['close'] - 1)
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': ticker_data.iloc[i]['date'],
                    'exit_date': ticker_data.iloc[i + hold_days]['date'],
                    'past_return': past_return * 100,
                    'future_return': future_return * 100
                })
    
    if len(trades) == 0:
        return None
    
    trades_df = pd.DataFrame(trades)
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['future_return'] > 0).mean() * 100,
        'avg_return': trades_df['future_return'].mean(),
        'momentum_persistence': np.corrcoef(trades_df['past_return'], trades_df['future_return'])[0,1] if len(trades_df) > 1 else 0,
        'trades': trades_df.to_dict('records')
    }
    
    return results


def test_rsi_mean_reversion():
    """Test RSI Mean Reversion on historical data"""
    print("=" * 70)
    print("BACKTEST: RSI Mean Reversion (Tier 1)")
    print("Using silver.historical_stock_data (2021-2024)")
    print("=" * 70)
    
    tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 
               'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV']
    
    results = run_historical_rsi_backtest(
        tickers=tickers,
        start_date='2021-03-01',  # Start after RSI warm-up
        end_date='2024-12-31',
        rsi_entry=30,
        rsi_exit=50,
        volume_threshold=1.0,  # Relaxed since we calculate volume SMA
        max_hold_days=5,
        stop_loss=0.03
    )
    
    if results:
        print(f"\n📊 RESULTS:")
        print(f"  Total Trades: {results['total_trades']}")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Avg Return: {results['avg_return']:.2f}%")
        print(f"  Sharpe Ratio: {results['sharpe']:.2f}")
        print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"  Avg Hold Days: {results['avg_hold_days']:.1f}")
        
        # Save to database
        db = TradeAlgoDB()
        db.connect()
        storage = BacktestStorage(db)
        
        backtest_id = storage.save_backtest_result(
            hypothesis_name='RSI Mean Reversion Historical',
            start_date='2021-03-01',
            end_date='2024-12-31',
            results=results,
            parameters={
                'rsi_entry': 30,
                'rsi_exit': 50,
                'max_hold_days': 5,
                'stop_loss': 0.03,
                'universe': tickers
            }
        )
        
        storage.save_trades(backtest_id, results['trades'])
        
        # Update status
        status = 'validated' if results['sharpe'] > 1.0 else 'testing'
        storage.update_hypothesis_status(
            hypothesis_name='RSI Mean Reversion',
            sharpe=results['sharpe'],
            status=status
        )
        
        db.close()
        
        print(f"\n✅ Backtest saved. ID: {backtest_id}")
        print(f"📈 Status: {status.upper()}")
    
    return results


def test_momentum_strategy():
    """Test Momentum strategy"""
    print("\n" + "=" * 70)
    print("BACKTEST: Momentum Strategy (Tier 1)")
    print("Academic Basis: Jegadeesh & Titman (1993)")
    print("=" * 70)
    
    tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
               'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV',
               'PFE', 'KO', 'PEP', 'COST']
    
    results = run_historical_momentum_backtest(
        tickers=tickers,
        start_date='2021-06-01',
        end_date='2024-12-31',
        lookback_days=20,
        hold_days=20,
        momentum_threshold=0.05
    )
    
    if results:
        print(f"\n📊 RESULTS:")
        print(f"  Total Trades: {results['total_trades']}")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Avg Return: {results['avg_return']:.2f}%")
        print(f"  Momentum Persistence: {results['momentum_persistence']:.3f}")
        
        # Save
        db = TradeAlgoDB()
        db.connect()
        storage = BacktestStorage(db)
        
        backtest_id = storage.save_backtest_result(
            hypothesis_name='Momentum Lifecycle',
            start_date='2021-06-01',
            end_date='2024-12-31',
            results=results,
            parameters={
                'lookback_days': 20,
                'hold_days': 20,
                'momentum_threshold': 0.05,
                'academic_basis': 'Jegadeesh & Titman (1993)'
            }
        )
        
        storage.save_trades(backtest_id, results['trades'])
        
        status = 'validated' if results.get('sharpe', 0) > 1.0 else 'testing'
        storage.update_hypothesis_status(
            hypothesis_name='Momentum Lifecycle',
            sharpe=results.get('sharpe', 0),
            status=status
        )
        
        db.close()
        
        print(f"\n✅ Backtest saved. ID: {backtest_id}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', choices=['rsi', 'momentum', 'all'], default='all')
    args = parser.parse_args()
    
    if args.test in ['rsi', 'all']:
        test_rsi_mean_reversion()
    
    if args.test in ['momentum', 'all']:
        test_momentum_strategy()
    
    print("\n" + "=" * 70)
    print("Backtests complete!")
    print("=" * 70)
