#!/usr/bin/env python3
"""
Batch Backtest Runner - Technical Analysis Stack
Runs all technical analysis backtests with yfinance data
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def get_data(ticker, start='2019-01-01', end='2024-12-31'):
    """Get OHLCV data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calculate_bollinger(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    bandwidth = (upper - lower) / sma
    return upper, lower, sma, bandwidth

def backtest_rsi_mean_reversion(data, ticker):
    """RSI Mean Reversion + Volume."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    
    rsi = calculate_rsi(pd.Series(closes))
    avg_volume = pd.Series(volumes).rolling(20).mean()
    
    trades = []
    for i in range(30, len(data) - 5):
        if rsi.iloc[i] < 30 and volumes[i] > avg_volume.iloc[i] * 1.3:
            entry = closes[i+1]
            exit_p = closes[i+5]  # 4-day hold
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long'})
        elif rsi.iloc[i] > 70 and volumes[i] > avg_volume.iloc[i] * 1.3:
            entry = closes[i+1]
            exit_p = closes[i+5]
            pnl = (entry - exit_p) / entry  # Short
            trades.append({'pnl': pnl, 'type': 'short'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'RSI_Mean_Reversion',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/4) if df['pnl'].std() > 0 else 0
    }

def backtest_macd_divergence(data, ticker):
    """MACD Histogram Divergence."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    macd, _, macd_hist = calculate_macd(pd.Series(closes))
    
    trades = []
    for i in range(20, len(data) - 10):
        # Look for divergence pattern over 10 days
        if i < 20:
            continue
        
        price_highs = pd.Series(closes[i-10:i]).max()
        price_lows = pd.Series(closes[i-10:i]).min()
        hist_highs = macd_hist.iloc[i-10:i].max()
        hist_lows = macd_hist.iloc[i-10:i].min()
        
        # Bearish divergence: higher price, lower hist
        if closes[i] > price_highs * 0.98 and macd_hist.iloc[i] < hist_highs * 0.8:
            entry = closes[i+1]
            exit_p = closes[i+6]
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl, 'type': 'short'})
        # Bullish divergence: lower price, higher hist
        elif closes[i] < price_lows * 1.02 and macd_hist.iloc[i] > hist_lows * 1.2:
            entry = closes[i+1]
            exit_p = closes[i+6]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'MACD_Divergence',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/5) if df['pnl'].std() > 0 else 0
    }

def backtest_bollinger_squeeze(data, ticker):
    """Bollinger Bands Squeeze Breakout."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    highs = data['High'].values.flatten()
    lows = data['Low'].values.flatten()
    volumes = data['Volume'].values.flatten()
    
    upper, lower, middle, bandwidth = calculate_bollinger(pd.Series(closes))
    avg_volume = pd.Series(volumes).rolling(20).mean()
    
    trades = []
    in_squeeze = False
    squeeze_start = 0
    
    for i in range(30, len(data) - 5):
        # Detect squeeze (bandwidth < 6% for 5+ days)
        if bandwidth.iloc[i] < 0.06:
            if not in_squeeze:
                in_squeeze = True
                squeeze_start = i
        else:
            if in_squeeze and i - squeeze_start >= 5:
                # Squeeze ended - trade breakout
                if closes[i] > upper.iloc[i] and volumes[i] > avg_volume.iloc[i] * 1.5:
                    entry = closes[i]
                    exit_p = closes[i+5]
                    pnl = (exit_p - entry) / entry
                    trades.append({'pnl': pnl, 'type': 'long'})
                elif closes[i] < lower.iloc[i] and volumes[i] > avg_volume.iloc[i] * 1.5:
                    entry = closes[i]
                    exit_p = closes[i+5]
                    pnl = (entry - exit_p) / entry
                    trades.append({'pnl': pnl, 'type': 'short'})
            in_squeeze = False
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Bollinger_Squeeze',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/5) if df['pnl'].std() > 0 else 0
    }

def backtest_engulfing(data, ticker):
    """Engulfing Candlestick Pattern."""
    if data is None or len(data) < 50:
        return None
    
    opens = data['Open'].values.flatten()
    highs = data['High'].values.flatten()
    lows = data['Low'].values.flatten()
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    
    avg_volume = pd.Series(volumes).rolling(20).mean()
    
    trades = []
    for i in range(5, len(data) - 3):
        # Bullish engulfing
        prev_red = closes[i-1] < opens[i-1]
        curr_green = closes[i] > opens[i]
        engulfs = opens[i] < closes[i-1] and closes[i] > opens[i-1]
        at_support = closes[i] < pd.Series(closes[i-20:i]).quantile(0.3)  # Lower 30%
        
        if prev_red and curr_green and engulfs and at_support and volumes[i] > avg_volume.iloc[i] * 1.3:
            entry = closes[i]
            exit_p = closes[i+3]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long'})
        
        # Bearish engulfing
        prev_green = closes[i-1] > opens[i-1]
        curr_red = closes[i] < opens[i]
        engulfs_bear = opens[i] > closes[i-1] and closes[i] < opens[i-1]
        at_resistance = closes[i] > pd.Series(closes[i-20:i]).quantile(0.7)  # Upper 30%
        
        if prev_green and curr_red and engulfs_bear and at_resistance and volumes[i] > avg_volume.iloc[i] * 1.3:
            entry = closes[i]
            exit_p = closes[i+3]
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl, 'type': 'short'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Engulfing_Pattern',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/3) if df['pnl'].std() > 0 else 0
    }

def backtest_momentum_20day(data, ticker):
    """Simple 20-day momentum."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    returns_20d = pd.Series(closes).pct_change(20)
    
    trades = []
    for i in range(30, len(data) - 20):
        if returns_20d.iloc[i] > 0.05:  # 5% momentum
            entry = closes[i+1]
            exit_p = closes[i+21]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl, 'type': 'long'})
        elif returns_20d.iloc[i] < -0.05:
            entry = closes[i+1]
            exit_p = closes[i+21]
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl, 'type': 'short'})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Momentum_20Day',
        'ticker': ticker,
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/20) if df['pnl'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("BATCH TECHNICAL ANALYSIS BACKTEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Data: yfinance (free)")
    print("=" * 80)
    
    tickers = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']
    strategies = [
        backtest_rsi_mean_reversion,
        backtest_macd_divergence,
        backtest_bollinger_squeeze,
        backtest_engulfing,
        backtest_momentum_20day
    ]
    
    all_results = []
    
    for ticker in tickers:
        print(f"\n📊 {ticker}...", end=' ')
        data = get_data(ticker)
        
        if data is None:
            print("❌ No data")
            continue
        
        print(f"✓ ({len(data)} days)")
        
        for strategy_func in strategies:
            try:
                result = strategy_func(data, ticker)
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"  ❌ {strategy_func.__name__}: {e}")
    
    # Compile results
    if not all_results:
        print("\n❌ No results generated")
        return
    
    results_df = pd.DataFrame(all_results)
    
    # Summary by strategy
    print("\n" + "=" * 80)
    print("RESULTS BY STRATEGY")
    print("=" * 80)
    
    summary = results_df.groupby('strategy').agg({
        'trades': 'sum',
        'win_rate': 'mean',
        'avg_return': 'mean',
        'sharpe': 'mean'
    }).round(3)
    
    print(summary.to_string())
    
    # Best performers
    print("\n" + "=" * 80)
    print("TOP PERFORMERS (Win Rate > 55% AND Sharpe > 0.5)")
    print("=" * 80)
    
    top = results_df[(results_df['win_rate'] > 0.55) & (results_df['sharpe'] > 0.5)]
    if not top.empty:
        top_sorted = top.sort_values('sharpe', ascending=False)
        print(top_sorted[['strategy', 'ticker', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
    else:
        print("⚠️ No strategies passed both filters")
    
    # Save results
    results_df.to_csv(RESULTS_DIR / 'batch_technical_backtest.csv', index=False)
    print(f"\n💾 Saved to results/batch_technical_backtest.csv")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    
    passing = len(top)
    total = len(results_df)
    
    print(f"Passing: {passing}/{total} strategy-ticker combinations")
    
    if passing >= 3:
        print("🎯 STRONG RESULTS - Multiple strategies show promise")
    elif passing >= 1:
        print("✅ MIXED RESULTS - Some strategies worth deeper study")
    else:
        print("⚠️ WEAK RESULTS - Technical strategies underperform in current market")
    
    return results_df

if __name__ == '__main__':
    main()
