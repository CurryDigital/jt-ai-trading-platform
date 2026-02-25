#!/usr/bin/env python3
"""
Asian Markets Validation Test
Test rejected hypotheses on HK, CN, SG markets to confirm universal failure
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

def backtest_3day_reversal(data):
    """3-Day Reversal test."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    returns = pd.Series(closes).pct_change().values
    avg_volume = pd.Series(volumes).rolling(20).mean().values
    
    trades = []
    for i in range(20, len(data) - 4):
        down_1 = returns[i-2] < 0
        down_2 = returns[i-1] < 0  
        down_3 = returns[i] < 0
        
        if not (down_1 and down_2 and down_3):
            continue
        
        decline_3d = (closes[i] - closes[i-3]) / closes[i-3]
        if decline_3d > -0.05:
            continue
        
        volume_spike = volumes[i] / avg_volume[i] if avg_volume[i] > 0 else 1
        if volume_spike < 1.3:
            continue
        
        entry_price = closes[i+1]
        exit_price = closes[i+4]
        pnl = (exit_price - entry_price) / entry_price
        
        trades.append({'pnl': pnl})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': '3Day_Reversal',
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/3) if df['pnl'].std() > 0 else 0
    }

def backtest_gap_fade(data):
    """Gap Fade test."""
    if data is None or len(data) < 20:
        return None
    
    opens = data['Open'].values.flatten()
    closes = data['Close'].values.flatten()
    
    trades = []
    for i in range(1, len(data)):
        gap = (opens[i] - closes[i-1]) / closes[i-1]
        
        if abs(gap) < 0.005:
            continue
        
        if gap > 0:
            pnl = (opens[i] - closes[i]) / opens[i]
        else:
            pnl = (closes[i] - opens[i]) / opens[i]
        
        trades.append({'pnl': pnl})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Gap_Fade',
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252) if df['pnl'].std() > 0 else 0
    }

def backtest_macd_divergence(data):
    """MACD Divergence test."""
    if data is None or len(data) < 50:
        return None
    
    closes = data['Close'].values.flatten()
    ema_fast = pd.Series(closes).ewm(span=12).mean()
    ema_slow = pd.Series(closes).ewm(span=26).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = macd - macd_signal
    
    trades = []
    for i in range(20, len(data) - 10):
        price_highs = pd.Series(closes[i-10:i]).max()
        price_lows = pd.Series(closes[i-10:i]).min()
        hist_highs = macd_hist.iloc[i-10:i].max()
        hist_lows = macd_hist.iloc[i-10:i].min()
        
        if closes[i] > price_highs * 0.98 and macd_hist.iloc[i] < hist_highs * 0.8:
            entry = closes[i+1]
            exit_p = closes[i+6]
            pnl = (entry - exit_p) / entry
            trades.append({'pnl': pnl})
        elif closes[i] < price_lows * 1.02 and macd_hist.iloc[i] > hist_lows * 1.2:
            entry = closes[i+1]
            exit_p = closes[i+6]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'MACD_Divergence',
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/5) if df['pnl'].std() > 0 else 0
    }

def backtest_engulfing(data):
    """Engulfing Pattern test."""
    if data is None or len(data) < 50:
        return None
    
    opens = data['Open'].values.flatten()
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    avg_volume = pd.Series(volumes).rolling(20).mean()
    
    trades = []
    for i in range(5, len(data) - 3):
        prev_red = closes[i-1] < opens[i-1]
        curr_green = closes[i] > opens[i]
        engulfs = opens[i] < closes[i-1] and closes[i] > opens[i-1]
        at_support = closes[i] < pd.Series(closes[i-20:i]).quantile(0.3)
        
        if prev_red and curr_green and engulfs and at_support and volumes[i] > avg_volume.iloc[i] * 1.3:
            entry = closes[i]
            exit_p = closes[i+3]
            pnl = (exit_p - entry) / entry
            trades.append({'pnl': pnl})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'strategy': 'Engulfing_Pattern',
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/3) if df['pnl'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("ASIAN MARKETS VALIDATION - REJECTED HYPOTHESES")
    print("=" * 80)
    print("Testing if rejected US strategies work in HK/CN/SG")
    print("If they fail here too = UNIVERSALLY REJECTED")
    print("=" * 80)
    
    # Asian tickers
    asian_tickers = {
        'HK': ['0700.HK', '0001.HK', '3690.HK', '9988.HK', '2318.HK', '1299.HK', '0005.HK'],
        'CN': ['BABA', 'JD', 'PDD', 'NIO', 'LI', 'XPEV', 'BIDU', 'TCEHY'],
        'SG': ['GLD', 'SLV', 'EWS', 'EWJ', 'ASHR']  # Singapore/Asia ETFs
    }
    
    strategies = [
        ('3-Day Reversal', backtest_3day_reversal),
        ('Gap Fade', backtest_gap_fade),
        ('MACD Divergence', backtest_macd_divergence),
        ('Engulfing Pattern', backtest_engulfing)
    ]
    
    all_results = []
    
    for region, tickers in asian_tickers.items():
        print(f"\n{'='*40}")
        print(f"REGION: {region}")
        print('='*40)
        
        for ticker in tickers:
            print(f"\n📊 {ticker}...", end=' ')
            data = get_data(ticker)
            
            if data is None or data.empty:
                print("❌ No data")
                continue
            
            print(f"✓ ({len(data)} days)")
            
            for strat_name, strat_func in strategies:
                try:
                    result = strat_func(data)
                    if result:
                        result['ticker'] = ticker
                        result['region'] = region
                        all_results.append(result)
                        status = "✅" if result['win_rate'] > 0.55 and result['sharpe'] > 0.5 else "❌"
                        print(f"  {strat_name}: {result['win_rate']:.1%} win, {result['sharpe']:.2f} Sharpe {status}")
                except Exception as e:
                    print(f"  ❌ {strat_name}: {e}")
    
    # Summary
    if all_results:
        print("\n" + "=" * 80)
        print("ASIAN MARKETS RESULTS SUMMARY")
        print("=" * 80)
        
        results_df = pd.DataFrame(all_results)
        
        # Summary by strategy
        summary = results_df.groupby(['strategy', 'region']).agg({
            'trades': 'sum',
            'win_rate': 'mean',
            'sharpe': 'mean'
        }).round(3)
        
        print("\nResults by Strategy and Region:")
        print(summary.to_string())
        
        # Overall by strategy
        print("\n" + "=" * 80)
        print("OVERALL BY STRATEGY (All Asian Markets)")
        print("=" * 80)
        
        overall = results_df.groupby('strategy').agg({
            'trades': 'sum',
            'win_rate': 'mean',
            'sharpe': 'mean'
        }).round(3)
        
        print(overall.to_string())
        
        # Compare to US results
        print("\n" + "=" * 80)
        print("COMPARISON: US vs ASIAN MARKETS")
        print("=" * 80)
        print("Strategy          | US Win Rate | Asia Win Rate | US Sharpe | Asia Sharpe")
        print("-" * 80)
        
        us_results = {
            '3Day_Reversal': {'win': 0.478, 'sharpe': -1.04},
            'Gap_Fade': {'win': 0.466, 'sharpe': -0.49},
            'MACD_Divergence': {'win': 0.465, 'sharpe': -0.35},
            'Engulfing_Pattern': {'win': 0.293, 'sharpe': -5.19}
        }
        
        for strategy in us_results.keys():
            us = us_results[strategy]
            asia_data = results_df[results_df['strategy'] == strategy]
            if not asia_data.empty:
                asia_win = asia_data['win_rate'].mean()
                asia_sharpe = asia_data['sharpe'].mean()
                print(f"{strategy:<18}| {us['win']:.1%}       | {asia_win:.1%}         | {us['sharpe']:.2f}     | {asia_sharpe:.2f}")
        
        # Final verdict
        print("\n" + "=" * 80)
        print("FINAL VERDICT")
        print("=" * 80)
        
        passing = results_df[(results_df['win_rate'] > 0.55) & (results_df['sharpe'] > 0.5)]
        total = len(results_df)
        
        print(f"Strategy-Region combinations tested: {total}")
        print(f"Passing in Asian markets: {len(passing)}")
        
        if len(passing) == 0:
            print("\n🔥 UNIVERSAL REJECTION CONFIRMED")
            print("These strategies fail in ALL markets tested (US, HK, CN, SG)")
            print("\nRecommended: PERMANENTLY ARCHIVE these hypotheses")
        elif len(passing) <= 2:
            print("\n⚠️ MINIMAL SUCCESS")
            print("Strategies show occasional success but not reliably")
            print("\nRecommended: REJECT - not worth the risk")
        else:
            print("\n✅ SOME SUCCESS")
            print("Strategies may work in specific markets")
            print("\nRecommended: Further investigation on specific tickers")
        
        # Save results
        results_df.to_csv(RESULTS_DIR / 'asian_markets_validation.csv', index=False)
        print(f"\n💾 Saved to results/asian_markets_validation.csv")
    else:
        print("\n❌ No results generated")

if __name__ == '__main__':
    main()
