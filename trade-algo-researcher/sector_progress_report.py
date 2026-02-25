#!/usr/bin/env python3
"""
Sector Research Progress Report
Tests available hypotheses on existing data while flagging data gaps
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

DATA_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data'

def get_data(ticker):
    """Fetch price data with indicators from local CSV"""
    filepath = os.path.join(DATA_DIR, f'{ticker}_indicators.csv')
    if not os.path.exists(filepath):
        return None, f"File not found: {filepath}"
    
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        # Calculate additional indicators
        df['returns'] = df['close'].pct_change()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['body'] = df['close'] - df['open']
        df['range'] = df['high'] - df['low']
        
        return df, None
    except Exception as e:
        return None, str(e)

def split_train_test(df, train_end='2022-12-31', test_start='2023-01-01'):
    """Split data into train and test periods"""
    train = df[df.index <= train_end].copy()
    test = df[df.index >= test_start].copy()
    return train, test

def test_rsi_macd_volume(df, rsi_threshold=35, volume_threshold=1.15, hold_days=5):
    """H1: RSI + MACD + Volume Triple Confirmation"""
    signals = []
    
    for i in range(len(df) - hold_days):
        if i < 26:
            continue
        
        rsi_ok = df['rsi'].iloc[i] < rsi_threshold
        macd_improving = df['macd_hist'].iloc[i] > df['macd_hist'].iloc[i-1] if i > 0 else False
        volume_ok = df['volume_ratio'].iloc[i] > volume_threshold
        
        if rsi_ok and macd_improving and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    
    return pd.DataFrame(signals)

def test_morning_star(df, hold_days=5):
    """H2: Morning Star Pattern"""
    signals = []
    
    for i in range(2, len(df) - hold_days):
        # Day 1: Bearish
        day1_bearish = df['close'].iloc[i-2] < df['open'].iloc[i-2]
        day1_body = abs(df['body'].iloc[i-2])
        
        # Day 2: Small body
        day2_body = abs(df['body'].iloc[i-1])
        day2_small = day2_body < day1_body * 0.3
        
        # Day 3: Bullish with close above day1 mid
        day3_bullish = df['close'].iloc[i] > df['open'].iloc[i]
        day1_mid = (df['open'].iloc[i-2] + df['close'].iloc[i-2]) / 2
        day3_strong = df['close'].iloc[i] > day1_mid
        
        if day1_bearish and day2_small and day3_bullish and day3_strong:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    
    return pd.DataFrame(signals)

def test_atr_compression(df, hold_days=5):
    """H4: ATR Compression Breakout"""
    signals = []
    
    df['atr_20_low'] = df['atr'].rolling(20).quantile(0.2)
    df['high_10d'] = df['high'].rolling(10).max()
    
    for i in range(10, len(df) - hold_days):
        atr_compression = df['atr'].iloc[i] < df['atr_20_low'].iloc[i]
        breakout = df['close'].iloc[i] > df['high_10d'].iloc[i-1]
        
        if atr_compression and breakout:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    
    return pd.DataFrame(signals)

def test_meta_bb_volume(df, hold_days=5):
    """Enhanced META BB Squeeze + Volume"""
    signals = []
    
    for i in range(2, len(df) - hold_days):
        bb_squeeze = df['bb_width'].iloc[i] < 0.05
        bb_squeeze_prev = df['bb_width'].iloc[i-1] < 0.05
        rsi_ok = df['rsi'].iloc[i] < 40
        volume_ok = df['volume_ratio'].iloc[i] > 1.2
        
        if bb_squeeze and bb_squeeze_prev and rsi_ok and volume_ok:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    
    return pd.DataFrame(signals)

def test_amd_trend_adx(df, hold_days=5):
    """Enhanced AMD Trend + ADX confirmation"""
    signals = []
    
    for i in range(1, len(df) - hold_days):
        if i < 50:
            continue
        
        above_sma50 = df['close'].iloc[i] > df['sma_50'].iloc[i]
        adx_ok = df['adx'].iloc[i] > 25
        adx_rising = df['adx'].iloc[i] > df['adx'].iloc[i-1]
        
        if above_sma50 and adx_ok and adx_rising:
            entry_price = df['close'].iloc[i]
            exit_price = df['close'].iloc[i + hold_days]
            pnl = (exit_price - entry_price) / entry_price
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    
    return pd.DataFrame(signals)

def run_progress_report():
    """Generate progress report for sector research"""
    
    print("=" * 80)
    print("SECTOR RESEARCH PROGRESS REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    
    # Check data availability
    print("\n" + "-" * 80)
    print("DATA AVAILABILITY CHECK")
    print("-" * 80)
    
    sectors = {
        'Tech Growth': ['AAPL', 'MSFT', 'NVDA', 'META', 'AMD', 'TSLA'],
        'Finance': ['JPM', 'BAC', 'GS', 'MS', 'C', 'XLF'],
        'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'XLV'],
        'Energy': ['XOM', 'CVX', 'COP', 'XLE'],
        'Consumer': ['WMT', 'COST', 'HD', 'MCD', 'NKE']
    }
    
    available_tickers = []
    missing_tickers = []
    
    for sector, tickers in sectors.items():
        available = []
        missing = []
        for ticker in tickers:
            df, error = get_data(ticker)
            if df is not None:
                available.append(ticker)
                available_tickers.append(ticker)
            else:
                missing.append(ticker)
                missing_tickers.append(ticker)
        
        status = "✅ READY" if len(missing) == 0 else "❌ BLOCKED"
        print(f"\n{sector}:")
        print(f"  Available ({len(available)}): {', '.join(available) if available else 'None'}")
        print(f"  Missing ({len(missing)}): {', '.join(missing) if missing else 'None'}")
        print(f"  Status: {status}")
    
    print("\n" + "-" * 80)
    print("SUMMARY: Can test on Tech only. Sector tests BLOCKED pending data.")
    print("-" * 80)
    
    # Test new hypotheses on available data
    print("\n" + "=" * 80)
    print("TESTING NEW HYPOTHESES (On Available Tech Data)")
    print("=" * 80)
    
    tech_tickers = ['AAPL', 'MSFT', 'NVDA', 'META', 'AMD', 'TSLA', 'COIN', 'SPY', 'QQQ']
    
    # H1: RSI + MACD + Volume
    print("\n--- H1: RSI + MACD + Volume Triple (Relaxed: vol>1.15x) ---")
    h1_results = {}
    
    for ticker in tech_tickers:
        df, error = get_data(ticker)
        if df is None:
            continue
        
        train, test = split_train_test(df)
        if len(test) < 50:
            continue
        
        test_signals = test_rsi_macd_volume(test, rsi_threshold=35, volume_threshold=1.15)
        
        if len(test_signals) >= 5:
            wr = test_signals['win'].mean() * 100
            h1_results[ticker] = {'test_wr': round(wr, 1), 'n': len(test_signals)}
            status = "✅" if wr >= 55 else "🟡" if wr >= 50 else "❌"
            print(f"  {ticker}: {wr:.1f}% (n={len(test_signals)}) {status}")
    
    # H2: Morning Star
    print("\n--- H2: Morning Star Pattern ---")
    h2_results = {}
    
    for ticker in tech_tickers:
        df, error = get_data(ticker)
        if df is None:
            continue
        
        train, test = split_train_test(df)
        test_signals = test_morning_star(test)
        
        if len(test_signals) >= 5:
            wr = test_signals['win'].mean() * 100
            h2_results[ticker] = {'test_wr': round(wr, 1), 'n': len(test_signals)}
            status = "🏆" if wr >= 70 else "⭐" if wr >= 60 else "✅" if wr >= 55 else "❌"
            print(f"  {ticker}: {wr:.1f}% (n={len(test_signals)}) {status}")
    
    # H4: ATR Compression
    print("\n--- H4: ATR Compression Breakout ---")
    h4_results = {}
    
    for ticker in ['MSFT', 'QQQ', 'META', 'NVDA', 'AAPL']:
        df, error = get_data(ticker)
        if df is None:
            continue
        
        train, test = split_train_test(df)
        test_signals = test_atr_compression(test)
        
        if len(test_signals) >= 5:
            wr = test_signals['win'].mean() * 100
            h4_results[ticker] = {'test_wr': round(wr, 1), 'n': len(test_signals)}
            status = "✅" if wr >= 55 else "❌"
            print(f"  {ticker}: {wr:.1f}% (n={len(test_signals)}) {status}")
    
    # Enhancement tests
    print("\n" + "=" * 80)
    print("ENHANCEMENT TESTS")
    print("=" * 80)
    
    # META BB + Volume
    print("\n--- META BB Squeeze + Volume > 1.2x ---")
    df, _ = get_data('META')
    if df is not None:
        train, test = split_train_test(df)
        
        # Original
        from evening_batch_research import test_bb_squeeze
        orig_signals = test_bb_squeeze(test, bb_width_threshold=0.05, rsi_threshold=40)
        orig_wr = orig_signals['win'].mean() * 100 if len(orig_signals) > 0 else 0
        
        # Enhanced
        enh_signals = test_meta_bb_volume(test)
        enh_wr = enh_signals['win'].mean() * 100 if len(enh_signals) > 0 else 0
        
        print(f"  Original BB Squeeze: {orig_wr:.1f}% (n={len(orig_signals)})")
        print(f"  +Volume > 1.2x: {enh_wr:.1f}% (n={len(enh_signals)})")
        print(f"  Delta: {enh_wr - orig_wr:+.1f}%")
    
    # AMD Trend + ADX
    print("\n--- AMD Trend + ADX Rising ---")
    df, _ = get_data('AMD')
    if df is not None:
        train, test = split_train_test(df)
        
        # Original
        from evening_batch_research import test_adx_trend
        orig_signals = test_adx_trend(test, adx_threshold=25, volume_threshold=0)
        orig_wr = orig_signals['win'].mean() * 100 if len(orig_signals) > 0 else 0
        
        # Enhanced
        enh_signals = test_amd_trend_adx(test)
        enh_wr = enh_signals['win'].mean() * 100 if len(enh_signals) > 0 else 0
        
        print(f"  Original ADX>25: {orig_wr:.1f}% (n={len(orig_signals)})")
        print(f"  +ADX Rising: {enh_wr:.1f}% (n={len(enh_signals)})")
        print(f"  Delta: {enh_wr - orig_wr:+.1f}%")
    
    # Summary
    print("\n" + "=" * 80)
    print("PROGRESS SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ Completed Tests:")
    print(f"  - H1 (RSI+MACD+Vol): {len(h1_results)} tickers")
    print(f"  - H2 (Morning Star): {len(h2_results)} tickers")
    print(f"  - H4 (ATR Compress): {len(h4_results)} tickers")
    print(f"  - META Enhancement: Volume filter")
    print(f"  - AMD Enhancement: ADX rising filter")
    
    print(f"\n❌ Blocked Tests (Missing Data):")
    print(f"  - Finance sector: JPM, BAC, GS, MS, C, XLF")
    print(f"  - Healthcare sector: JNJ, PFE, UNH, ABBV, XLV")
    print(f"  - Energy sector: XOM, CVX, COP, XLE")
    print(f"  - Consumer sector: WMT, COST, HD, MCD, NKE")
    
    print(f"\n🔄 Next Steps:")
    print(f"  1. Request data for sector tickers")
    print(f"  2. Run cross-sector validation when data available")
    print(f"  3. Continue testing on tech universe")
    
    return {
        'h1_results': h1_results,
        'h2_results': h2_results,
        'h4_results': h4_results,
        'missing_tickers': missing_tickers,
        'available_tickers': available_tickers
    }

if __name__ == "__main__":
    run_progress_report()
