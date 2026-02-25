#!/usr/bin/env python3
"""
Sector Expansion Research - Financials & Energy
Tests if successful Tech strategies transfer to other sectors
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data'
RESULTS_DIR = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results'

def get_data(ticker):
    filepath = os.path.join(DATA_DIR, f'{ticker}_indicators.csv')
    if not os.path.exists(filepath):
        return None
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        return df
    except:
        return None

def calculate_95_ci(wins, total):
    if total == 0:
        return 0, 0
    p = wins / total
    z = 1.96
    se = np.sqrt(p * (1 - p) / total)
    return max(0, p - z * se) * 100, min(1, p + z * se) * 100

def backtest_bb_walk_adx(df, hold_days=5, adx_threshold=25):
    """BB Walk with ADX filter - Strong trend continuation"""
    df = df.copy()
    df['adx_strong'] = df['adx'] > adx_threshold
    df['price_above_bb_mid'] = df['close'] > df['bb_middle']
    df['signal'] = df['adx_strong'] & df['price_above_bb_mid'] & (df['rsi'] < 70)
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry = df['close'].iloc[i]
            exit_p = df['close'].iloc[i + hold_days]
            if pd.isna(entry) or pd.isna(exit_p):
                continue
            pnl = (exit_p - entry) / entry
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_strong_uptrend(df, hold_days=5):
    """Strong Uptrend - Price > SMA50 > SMA200 + ADX > 20"""
    df = df.copy()
    df['price_above_sma50'] = df['close'] > df['sma_50']
    df['sma50_above_sma200'] = df['sma_50'] > df['sma_200']
    df['adx_trending'] = df['adx'] > 20
    df['signal'] = df['price_above_sma50'] & df['sma50_above_sma200'] & df['adx_trending']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry = df['close'].iloc[i]
            exit_p = df['close'].iloc[i + hold_days]
            if pd.isna(entry) or pd.isna(exit_p):
                continue
            pnl = (exit_p - entry) / entry
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def backtest_macd_momentum(df, hold_days=5):
    """MACD Momentum - MACD > 0, Histogram > 0, RSI < 65"""
    df = df.copy()
    df['macd_bullish'] = df['macd'] > 0
    df['macd_hist_positive'] = df['macd_hist'] > 0
    df['rsi_not_overbought'] = df['rsi'] < 65
    df['signal'] = df['macd_bullish'] & df['macd_hist_positive'] & df['rsi_not_overbought']
    
    signals = []
    for i in range(len(df) - hold_days):
        if df['signal'].iloc[i] and not pd.isna(df['close'].iloc[i]):
            entry = df['close'].iloc[i]
            exit_p = df['close'].iloc[i + hold_days]
            if pd.isna(entry) or pd.isna(exit_p):
                continue
            pnl = (exit_p - entry) / entry
            signals.append({'pnl': pnl, 'win': 1 if pnl > 0 else 0})
    return pd.DataFrame(signals)

def analyze(train_df, test_df, ticker, strategy):
    train_wr = (train_df['win'].sum() / len(train_df) * 100) if len(train_df) > 0 else 0
    test_wr = (test_df['win'].sum() / len(test_df) * 100) if len(test_df) > 0 else 0
    decay = train_wr - test_wr
    ci_lower, ci_upper = calculate_95_ci(test_df['win'].sum(), len(test_df))
    avg_ret = test_df['pnl'].mean() * 100 if len(test_df) > 0 else 0
    
    is_golden = test_wr >= 70 and len(test_df) >= 30 and abs(decay) < 15
    is_validated = test_wr >= 55 and len(test_df) >= 10 and abs(decay) < 25
    
    return {
        'ticker': ticker, 'strategy': strategy,
        'train_wr': round(train_wr, 1), 'train_n': len(train_df),
        'test_wr': round(test_wr, 1), 'test_n': len(test_df),
        'decay': round(decay, 1), 'ci_lower': round(ci_lower, 1), 'ci_upper': round(ci_upper, 1),
        'avg_return': round(avg_ret, 2),
        'status': '🏆 GOLDEN' if is_golden else ('✅ Validated' if is_validated else '❌ Rejected'),
        'is_golden': is_golden, 'is_validated': is_validated
    }

def split_data(df):
    n = len(df)
    train_size = int(n * 0.6)
    return df.iloc[:train_size], df.iloc[train_size:]

def run_sector_expansion():
    print("=" * 80)
    print("SECTOR EXPANSION RESEARCH - Financials & Energy")
    print("Testing if Tech strategies transfer to other sectors")
    print("=" * 80)
    
    sectors = {
        'Financials': ['JPM', 'BAC', 'GS', 'V', 'MA'],
        'Energy': ['XOM', 'CVX', 'COP'],
        'Healthcare': ['JNJ', 'PFE', 'UNH'],
        'Tech': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMD'],
        'ETF': ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE']
    }
    
    strategies = [
        ('BB Walk ADX35', backtest_bb_walk_adx),
        ('Strong Uptrend', backtest_strong_uptrend),
        ('MACD Momentum', backtest_macd_momentum)
    ]
    
    results = []
    
    for sector, tickers in sectors.items():
        print(f"\n{'=' * 40}")
        print(f"SECTOR: {sector}")
        print("=" * 40)
        
        for ticker in tickers:
            df = get_data(ticker)
            if df is None:
                continue
            
            for strat_name, strat_func in strategies:
                try:
                    signals = strat_func(df)
                    if len(signals) == 0:
                        continue
                    train, test = split_data(signals)
                    result = analyze(train, test, ticker, strat_name)
                    results.append(result)
                    
                    icon = "🏆" if result['is_golden'] else ("✅" if result['is_validated'] else "❌")
                    print(f"  {icon} {ticker:5} {strat_name:18} | Test={result['test_wr']:5.1f}% (n={result['test_n']:3})")
                except:
                    continue
    
    return results

def summarize(results):
    golden = [r for r in results if r['is_golden']]
    validated = [r for r in results if r['is_validated'] and not r['is_golden']]
    
    print("\n" + "=" * 80)
    print("SECTOR EXPANSION SUMMARY")
    print("=" * 80)
    print(f"\n🏆 Golden: {len(golden)}")
    for r in golden:
        print(f"   • {r['ticker']:5} {r['strategy']:20} | {r['test_wr']:5.1f}% (n={r['test_n']})")
    
    print(f"\n✅ Validated: {len(validated)}")
    for r in validated[:10]:
        print(f"   • {r['ticker']:5} {r['strategy']:20} | {r['test_wr']:5.1f}% (n={r['test_n']})")
    
    # Sector breakdown
    print("\n📊 By Sector:")
    sectors = {}
    for r in results:
        sector = 'Other'
        for s in ['Financials', 'Energy', 'Healthcare', 'Tech', 'ETF']:
            if r['ticker'] in ['JPM', 'BAC', 'GS', 'V', 'MA'] and s == 'Financials':
                sector = 'Financials'
            elif r['ticker'] in ['XOM', 'CVX', 'COP'] and s == 'Energy':
                sector = 'Energy'
            elif r['ticker'] in ['JNJ', 'PFE', 'UNH'] and s == 'Healthcare':
                sector = 'Healthcare'
            elif r['ticker'] in ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMD'] and s == 'Tech':
                sector = 'Tech'
            elif r['ticker'] in ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE'] and s == 'ETF':
                sector = 'ETF'
        sectors.setdefault(sector, {'golden': 0, 'validated': 0, 'total': 0, 'avg_wr': []})
        sectors[sector]['total'] += 1
        sectors[sector]['avg_wr'].append(r['test_wr'])
        if r['is_golden']:
            sectors[sector]['golden'] += 1
        elif r['is_validated']:
            sectors[sector]['validated'] += 1
    
    for sector, data in sectors.items():
        avg_wr = np.mean(data['avg_wr']) if data['avg_wr'] else 0
        print(f"   {sector:12}: {data['golden']} Golden, {data['validated']} Validated | Avg WR: {avg_wr:.1f}%")
    
    filename = f"{RESULTS_DIR}/sector_expansion_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved to: {filename}")
    
    return golden, validated

if __name__ == '__main__':
    results = run_sector_expansion()
    if results:
        summarize(results)
        print("\n✅ Sector expansion complete!")
