#!/usr/bin/env python3
"""
Peer Firm Lag Test - Asian Markets
Test if XOM move predicts SNP/PTR move with lag (Asian oil companies)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"

def get_data(ticker, start='2019-01-01', end='2024-12-31'):
    """Get price data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data['Close'].values.flatten()
    except:
        return None

def analyze_lead_lag(lead, lag, max_lag=5):
    """Analyze lead-lag relationship."""
    lead_ret = pd.Series(lead).pct_change().dropna()
    lag_ret = pd.Series(lag).pct_change().dropna()
    
    min_len = min(len(lead_ret), len(lag_ret))
    lead_ret = lead_ret.iloc[:min_len]
    lag_ret = lag_ret.iloc[:min_len]
    
    best_corr = -1
    best_lag = 0
    
    for lag_days in range(0, max_lag + 1):
        if lag_days == 0:
            corr = lead_ret.corr(lag_ret)
        else:
            corr = lead_ret.shift(lag_days).corr(lag_ret)
        
        if corr > best_corr:
            best_corr = corr
            best_lag = lag_days
    
    return best_lag, best_corr

def backtest_peer_lag(leader_data, follower_data, threshold=0.03, hold_days=3):
    """Backtest peer lag strategy."""
    if leader_data is None or follower_data is None:
        return None
    
    min_len = min(len(leader_data), len(follower_data))
    leader = leader_data[:min_len]
    follower = follower_data[:min_len]
    
    leader_ret = pd.Series(leader).pct_change()
    
    trades = []
    for i in range(5, min_len - hold_days - 1):
        if abs(leader_ret.iloc[i]) > threshold:
            # Leader moved >3%, trade follower next day
            direction = 1 if leader_ret.iloc[i] > 0 else -1
            entry = follower[i+1]
            exit_p = follower[min(i+1+hold_days, min_len-1)]
            pnl = (exit_p - entry) / entry * direction
            trades.append({'pnl': pnl, 'leader_move': leader_ret.iloc[i]})
    
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    return {
        'trades': len(df),
        'win_rate': (df['pnl'] > 0).mean(),
        'avg_return': df['pnl'].mean(),
        'sharpe': df['pnl'].mean() / df['pnl'].std() * np.sqrt(252/hold_days) if df['pnl'].std() > 0 else 0
    }

def main():
    print("=" * 80)
    print("PEER FIRM LAG - ASIAN MARKETS TEST")
    print("=" * 80)
    print("Testing if US/global leaders predict Asian peer moves")
    print("=" * 80)
    
    # Oil sector pairs
    oil_pairs = [
        ('XOM', 'SNP', 'US vs China Oil'),
        ('XOM', 'PTR', 'US vs PetroChina'),
        ('CVX', 'SNP', 'Chevron vs Sinopec'),
        ('CVX', 'PTR', 'Chevron vs PetroChina'),
        ('COP', 'SNP', 'Conoco vs Sinopec'),
    ]
    
    # Tech sector pairs
    tech_pairs = [
        ('NVDA', 'AI', 'Nvidia vs C3.ai'),
        ('AMD', 'TSM', 'AMD vs TSMC'),
        ('INTC', 'TSM', 'Intel vs TSMC'),
    ]
    
    # Bank pairs
    bank_pairs = [
        ('JPM', '0005.HK', 'JPM vs HSBC'),
        ('BAC', '0005.HK', 'BAC vs HSBC'),
        ('GS', '0005.HK', 'GS vs HSBC'),
    ]
    
    all_results = []
    
    print("\n" + "=" * 40)
    print("OIL SECTOR")
    print("=" * 40)
    
    for leader, follower, desc in oil_pairs:
        print(f"\n{desc}: {leader} → {follower}")
        leader_data = get_data(leader)
        follower_data = get_data(follower)
        
        if leader_data is None or follower_data is None:
            print("  ❌ Data unavailable")
            continue
        
        # Lead-lag analysis
        lag, corr = analyze_lead_lag(leader_data, follower_data)
        print(f"  Correlation: {corr:.3f}, Best lag: {lag} days")
        
        if lag > 0 and corr > 0.5:
            print(f"  ✅ Lead-lag detected: {leader} leads {follower} by {lag} days")
        else:
            print(f"  ⚠️ No reliable lag (simultaneous or weak)")
        
        # Backtest
        result = backtest_peer_lag(leader_data, follower_data)
        if result:
            print(f"  Backtest: {result['trades']} trades, {result['win_rate']:.1%} win, Sharpe: {result['sharpe']:.2f}")
            result['pair'] = f"{leader}_{follower}"
            result['sector'] = 'Oil'
            result['lag_days'] = lag
            result['correlation'] = corr
            all_results.append(result)
    
    print("\n" + "=" * 40)
    print("TECH SECTOR")
    print("=" * 40)
    
    for leader, follower, desc in tech_pairs:
        print(f"\n{desc}: {leader} → {follower}")
        leader_data = get_data(leader)
        follower_data = get_data(follower)
        
        if leader_data is None or follower_data is None:
            print("  ❌ Data unavailable")
            continue
        
        lag, corr = analyze_lead_lag(leader_data, follower_data)
        print(f"  Correlation: {corr:.3f}, Best lag: {lag} days")
        
        if lag > 0 and corr > 0.5:
            print(f"  ✅ Lead-lag detected")
        else:
            print(f"  ⚠️ No reliable lag")
        
        result = backtest_peer_lag(leader_data, follower_data)
        if result:
            print(f"  Backtest: {result['trades']} trades, {result['win_rate']:.1%} win, Sharpe: {result['sharpe']:.2f}")
            result['pair'] = f"{leader}_{follower}"
            result['sector'] = 'Tech'
            result['lag_days'] = lag
            result['correlation'] = corr
            all_results.append(result)
    
    print("\n" + "=" * 40)
    print("BANKING SECTOR")
    print("=" * 40)
    
    for leader, follower, desc in bank_pairs:
        print(f"\n{desc}: {leader} → {follower}")
        leader_data = get_data(leader)
        follower_data = get_data(follower)
        
        if leader_data is None or follower_data is None:
            print("  ❌ Data unavailable")
            continue
        
        lag, corr = analyze_lead_lag(leader_data, follower_data)
        print(f"  Correlation: {corr:.3f}, Best lag: {lag} days")
        
        if lag > 0 and corr > 0.5:
            print(f"  ✅ Lead-lag detected")
        else:
            print(f"  ⚠️ No reliable lag")
        
        result = backtest_peer_lag(leader_data, follower_data)
        if result:
            print(f"  Backtest: {result['trades']} trades, {result['win_rate']:.1%} win, Sharpe: {result['sharpe']:.2f}")
            result['pair'] = f"{leader}_{follower}"
            result['sector'] = 'Banking'
            result['lag_days'] = lag
            result['correlation'] = corr
            all_results.append(result)
    
    # Summary
    if all_results:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        results_df = pd.DataFrame(all_results)
        print("\nAll Results:")
        print(results_df[['pair', 'trades', 'win_rate', 'sharpe', 'lag_days', 'correlation']].to_string(index=False))
        
        # Check for any with positive lag and decent performance
        viable = results_df[(results_df['lag_days'] > 0) & (results_df['correlation'] > 0.4) & (results_df['win_rate'] > 0.52)]
        
        print("\n" + "=" * 80)
        print("VIABLE PAIRS (Lag >0, Corr >0.4, Win >52%)")
        print("=" * 80)
        
        if not viable.empty:
            print(viable[['pair', 'trades', 'win_rate', 'sharpe', 'lag_days']].to_string(index=False))
            print("\n🎯 Peer lag works on these pairs!")
        else:
            print("⚠️ No viable pairs found")
            print("\n🔥 Peer Firm Lag hypothesis REJECTED globally")
            print("US markets too efficient, Asian markets also too correlated")
    
    # Save results
    if all_results:
        results_df.to_csv(RESULTS_DIR / 'peer_lag_asian_test.csv', index=False)
        print(f"\n💾 Saved to results/peer_lag_asian_test.csv")

if __name__ == '__main__':
    main()
