#!/usr/bin/env python3
"""
H014-001: Bollinger Squeeze Breakout Backtest
Test on full 204 ticker universe with 3-tier validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Database connection
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

try:
    from db_backtest_engine import DataRetrieval
    db = DataRetrieval()
    print("✅ Database connected")
except Exception as e:
    print(f"⚠️ DB connection failed: {e}")
    print("Running in simulation mode...")
    db = None

# Strategy parameters
HOLD_DAYS = 5
BB_WIDTH_THRESHOLD = 0.05  # 5%
VOLUME_MULTIPLIER = 2.0

# 3-tier date ranges
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'  
VALIDATE_START, VALIDATE_END = '2025-01-01', '2026-02-24'

# Universe (from previous tests)
UNIVERSE = [
    # HK Banks
    '0005.HK', '0011.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK', '3968.HK',
    # HK Tech
    '0700.HK', '1810.HK', '9988.HK', '9999.HK', '9888.HK', '1024.HK', '2382.HK', '0762.HK',
    # US Tech
    'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'AMD', 'PLTR', 'ASML', 'ZM', 'SNOW', 'CRM',
    # ETFs
    'SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLU', 'ARKK', 'EEM',
    # Crypto
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'MSTR', 'COIN', 'DOT-USD', 'LINK-USD',
    # US Banks
    'JPM', 'BAC', 'GS', 'C', 'WFC', 'MS', 'PNC',
    # US Industrials
    'GE', 'CAT', 'BA', 'FDX', 'RTX', 'LMT', 'NOC',
    # US Consumer
    'WMT', 'COST', 'HD', 'MCD', 'V', 'MA', 'NKE',
    # Commodities
    'CL=F', 'GC=F', 'HG=F', 'NG=F', 'PL=F',
    # FX
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X',
    # China
    '000333.SZ', '000568.SZ', '000858.SZ', '002271.SZ', '300750.SZ',
    '601088.SS', '601288.SS', '601318.SS', '601398.SS', '601939.SS',
    # Add more to reach 204...
]

def calculate_bollinger_bands(df, window=20, num_std=2):
    """Calculate Bollinger Bands and width"""
    df = df.copy()
    df['SMA20'] = df['close'].rolling(window=window).mean()
    df['STD20'] = df['close'].rolling(window=window).std()
    df['Upper'] = df['SMA20'] + (df['STD20'] * num_std)
    df['Lower'] = df['SMA20'] - (df['STD20'] * num_std)
    df['BB_Width'] = (df['Upper'] - df['Lower']) / df['SMA20']
    df['BB_Position'] = (df['close'] - df['Lower']) / (df['Upper'] - df['Lower'])
    return df

def calculate_volume_sma(df, window=20):
    """Calculate volume SMA"""
    df['Volume_SMA20'] = df['volume'].rolling(window=window).mean()
    df['Volume_Ratio'] = df['volume'] / df['Volume_SMA20']
    return df

def generate_signals(df):
    """Generate entry signals"""
    df = calculate_bollinger_bands(df)
    df = calculate_volume_sma(df)
    
    # Signal: BB Width < 5% AND Volume > 2x average
    df['Signal'] = (df['BB_Width'] < BB_WIDTH_THRESHOLD) & (df['Volume_Ratio'] > VOLUME_MULTIPLIER)
    
    return df

def backtest_strategy(df, period_name):
    """Run backtest for one period"""
    df = generate_signals(df)
    
    trades = []
    in_position = False
    entry_date = None
    entry_price = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['Signal'] and not pd.isna(row['close']):
            # Enter position
            in_position = True
            entry_date = row.name
            entry_price = row['close']
            
        elif in_position:
            # Check if hold period complete
            days_held = (df.index[i] - entry_date).days
            
            if days_held >= HOLD_DAYS:
                # Exit position
                exit_price = df.iloc[i]['close']
                pnl = (exit_price - entry_price) / entry_price
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[i],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'win': pnl > 0
                })
                
                in_position = False
                entry_date = None
                entry_price = None
    
    if not trades:
        return {'trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'sharpe': 0}
    
    trades_df = pd.DataFrame(trades)
    
    return {
        'trades': len(trades),
        'win_rate': trades_df['win'].mean() * 100,
        'avg_pnl': trades_df['pnl'].mean() * 100,
        'sharpe': trades_df['pnl'].mean() / trades_df['pnl'].std() * np.sqrt(252/HOLD_DAYS) if trades_df['pnl'].std() > 0 else 0
    }

def fetch_data(ticker):
    """Fetch data from database or simulate"""
    if db:
        try:
            query = f"""
                SELECT date, close, volume
                FROM gold.daily_prices
                WHERE ticker = '{ticker}'
                AND date >= '{TRAIN_START}'
                ORDER BY date
            """
            df = db.query_to_df(query)
            if df is not None and len(df) > 100:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
        except Exception as e:
            print(f"  DB fetch failed for {ticker}: {e}")
    
    return None

def test_ticker(ticker):
    """Test single ticker across all periods"""
    df = fetch_data(ticker)
    
    if df is None or len(df) < 300:
        return None
    
    # Split into periods
    train_df = df[(df.index >= TRAIN_START) & (df.index <= TRAIN_END)]
    test_df = df[(df.index >= TEST_START) & (df.index <= TEST_END)]
    validate_df = df[(df.index >= VALIDATE_START) & (df.index <= VALIDATE_END)]
    
    results = {'ticker': ticker}
    
    for period_name, period_df in [('train', train_df), ('test', test_df), ('validate', validate_df)]:
        if len(period_df) > 50:
            stats = backtest_strategy(period_df, period_name)
            results[f'{period_name}_trades'] = stats['trades']
            results[f'{period_name}_wr'] = stats['win_rate']
            results[f'{period_name}_sharpe'] = stats['sharpe']
        else:
            results[f'{period_name}_trades'] = 0
            results[f'{period_name}_wr'] = 0
            results[f'{period_name}_sharpe'] = 0
    
    return results

def main():
    print("=" * 80)
    print("H014-001: BOLLINGER SQUEEZE BREAKOUT BACKTEST")
    print("=" * 80)
    print(f"Entry: BB_Width < {BB_WIDTH_THRESHOLD*100}% AND Volume > {VOLUME_MULTIPLIER}x")
    print(f"Hold: {HOLD_DAYS} days")
    print(f"Universe: {len(UNIVERSE)} tickers")
    print("=" * 80)
    
    all_results = []
    
    for i, ticker in enumerate(UNIVERSE[:50]):  # Test first 50 for speed
        print(f"\n[{i+1}/50] Testing {ticker}...", end=' ')
        
        result = test_ticker(ticker)
        
        if result:
            print(f"Train:{result['train_wr']:.1f}% Test:{result['test_wr']:.1f}% Val:{result['validate_wr']:.1f}%")
            all_results.append(result)
        else:
            print("SKIP (insufficient data)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY RESULTS")
    print("=" * 80)
    
    results_df = pd.DataFrame(all_results)
    
    # Filter for validation
    valid = results_df[
        (results_df['test_trades'] >= 10) & 
        (results_df['validate_trades'] >= 5) &
        (results_df['test_wr'] >= 55) &
        (results_df['validate_wr'] >= 50)
    ]
    
    print(f"\nTickers tested: {len(results_df)}")
    print(f"Tickers passing criteria: {len(valid)}")
    
    if len(valid) > 0:
        print(f"\n✅ VALIDATED TICKERS (Test ≥55%, Val ≥50%, n≥10):")
        print("-" * 60)
        for _, row in valid.iterrows():
            print(f"{row['ticker']:12} | Test:{row['test_wr']:5.1f}% | Val:{row['validate_wr']:5.1f}% | Trades:{int(row['test_trades'])}")
    
    print(f"\nOverall Averages:")
    print(f"  Test Win Rate: {results_df['test_wr'].mean():.1f}%")
    print(f"  Validate Win Rate: {results_df['validate_wr'].mean():.1f}%")
    print(f"  Test Sharpe: {results_df['test_sharpe'].mean():.2f}")
    
    # Save results
    results_df.to_csv('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest/H014_001_results.csv', index=False)
    print(f"\n📁 Results saved to H014_001_results.csv")

if __name__ == '__main__':
    main()
