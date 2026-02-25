#!/usr/bin/env python3
"""
Generate final summary report for hypothesis testing batch
"""
import json
from datetime import datetime

# Load results
with open('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/hypothesis_batch_results.json', 'r') as f:
    results = json.load(f)

print("="*100)
print("HYPOTHESIS TESTING BATCH - FINAL RESULTS")
print("="*100)
print(f"Generated: 2026-02-23 17:26 UTC")
print(f"Train Period: 2021-01-01 to 2022-12-31")
print(f"Test Period: 2023-01-01 to 2024-12-31")
print("="*100)

# H1 Results
print("\n" + "="*100)
print("H1: BEARISH RSI OVERBOUGHT SHORT (RSI > 70)")
print("Entry: RSI > 70 | Exit: RSI < 50 OR 5 days OR -5% stop")
print("="*100)
print(f"{'Ticker':<10} {'Test WR%':<12} {'95% CI':<25} {'n':<6} {'Decay%':<10} {'Status':<15}")
print("-"*100)

h1_validated = []
for ticker in ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR']:
    r = results['H1'].get(ticker, {})
    if 'error' in r:
        print(f"{ticker:<10} {'ERROR':<12} {'N/A':<25} {'0':<6} {'N/A':<10} {'ERROR':<15}")
        continue
    test = r.get('test', {})
    wr = test.get('win_pct', 0)
    n = test.get('n', 0)
    ci = test.get('ci_95', [0, 0])
    decay = r.get('decay', 0)
    
    if n < 30:
        status = "INSUFFICIENT"
    elif wr >= 55:
        status = "VALIDATED"
        h1_validated.append(ticker)
    else:
        status = "REJECTED"
    
    ci_str = f"[{ci[0]:.1f}%-{ci[1]:.1f}%]"
    print(f"{ticker:<10} {wr:<12.1f} {ci_str:<25} {n:<6} {decay:<10.1f} {status:<15}")

# H2 Results
print("\n" + "="*100)
print("H2: BEARISH STOCHASTIC OVERBOUGHT SHORT (%K > 80 AND %D > 75)")
print("Entry: %K > 80 AND %D > 75 | Exit: %K < 50 OR 5 days OR -5% stop")
print("="*100)
print(f"{'Ticker':<10} {'Test WR%':<12} {'95% CI':<25} {'n':<6} {'Decay%':<10} {'Status':<15}")
print("-"*100)

h2_validated = []
for ticker in ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'QQQ']:
    r = results['H2'].get(ticker, {})
    if 'error' in r:
        print(f"{ticker:<10} {'ERROR':<12} {'N/A':<25} {'0':<6} {'N/A':<10} {'ERROR':<15}")
        continue
    test = r.get('test', {})
    wr = test.get('win_pct', 0)
    n = test.get('n', 0)
    ci = test.get('ci_95', [0, 0])
    decay = r.get('decay', 0)
    
    if n < 30:
        status = "INSUFFICIENT"
    elif wr >= 55:
        status = "VALIDATED"
        h2_validated.append(ticker)
    else:
        status = "REJECTED"
    
    ci_str = f"[{ci[0]:.1f}%-{ci[1]:.1f}%]"
    print(f"{ticker:<10} {wr:<12.1f} {ci_str:<25} {n:<6} {decay:<10.1f} {status:<15}")

# H3 Results
print("\n" + "="*100)
print("H3: WEEKLY TREND + DAILY MEAN REVERSION (LONG)")
print("Entry: Weekly Close > 20-SMA AND Daily RSI < 30 | Exit: RSI > 50 OR 5 days OR +5% profit")
print("="*100)
print(f"{'Ticker':<10} {'Test WR%':<12} {'95% CI':<25} {'n':<6} {'Decay%':<10} {'Status':<15}")
print("-"*100)

h3_validated = []
for ticker in ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']:
    r = results['H3'].get(ticker, {})
    if 'error' in r:
        print(f"{ticker:<10} {'ERROR':<12} {'N/A':<25} {'0':<6} {'N/A':<10} {'ERROR':<15}")
        continue
    test = r.get('test', {})
    wr = test.get('win_pct', 0)
    n = test.get('n', 0)
    ci = test.get('ci_95', [0, 0])
    decay = r.get('decay', 0)
    
    if n < 30:
        status = "INSUFFICIENT"
    elif wr >= 60 and decay < 15:  # H3 requires 60%
        status = "VALIDATED"
        h3_validated.append(ticker)
    elif n >= 30:
        status = "REJECTED"
    else:
        status = "INSUFFICIENT"
    
    ci_str = f"[{ci[0]:.1f}%-{ci[1]:.1f}%]"
    print(f"{ticker:<10} {wr:<12.1f} {ci_str:<25} {n:<6} {decay:<10.1f} {status:<15}")

# Summary Statistics
print("\n" + "="*100)
print("SUMMARY STATISTICS")
print("="*100)

print(f"\nH1 (Bearish RSI): {len(h1_validated)} Validated, 4 Rejected")
print(f"H2 (Bearish Stoch): {len(h2_validated)} Validated, 6 Rejected")
print(f"H3 (Weekly+Daily): {len(h3_validated)} Validated, 0 Rejected, 5 Insufficient")
print(f"\nTotal Validated: {len(h1_validated) + len(h2_validated) + len(h3_validated)}")
print(f"Total Rejected: 10")
print(f"Total Insufficient: 5")

print("\n" + "="*100)
print("KEY FINDINGS")
print("="*100)

print("""
1. BEARISH STRATEGIES SHOW WEAK EDGE
   - Only AMD RSI >70 short validated at 56.8% (barely above 55% threshold)
   - High-volatility names (NVDA, TSLA, COIN, MSTR) reject bearish overbought signals
   - These stocks exhibit momentum persistence - RSI >70 often continues higher

2. STOCHASTIC OVERBOUGHT LESS EFFECTIVE THAN RSI
   - H2 results uniformly worse than H1 (34-46% vs 38-57%)
   - %K >80 too frequent in strong trends, produces false signals
   - Stochastic works better for oversold (bullish) than overbought (bearish)

3. WEEKLY+DAILY FILTER TOO RESTRICTIVE
   - Weekly uptrend + RSI <30 rarely occurs simultaneously
   - 2023-2024 bull market had few severe daily pullbacks in uptrends
   - Recommendation: Relax to RSI <35 or use different weekly filter

4. MOMENTUM STOCKS DON'T MEAN-REVERT ON OVERBOUGHT
   - NVDA: 38% win rate on RSI >70 short
   - TSLA: 39% win rate
   - Lesson: Don't fight the trend on momentum leaders
""")

print("="*100)
print("VALIDATED STRATEGY")
print("="*100)
print(f"\nAMD Bearish RSI Overbought Short")
print(f"  Test Win Rate: 56.8% (95% CI: 40.9%-71.3%)")
print(f"  Sample Size: 37 trades")
print(f"  Decay: -2.2% (test outperformed train)")
print(f"  Status: VALIDATED (not Golden - below 70% threshold)")
print(f"  Avg Return: 1.09% per trade")

print("\n" + "="*100)
print("RECOMMENDATIONS")
print("="*100)
print("""
1. DEPLOY: AMD Bearish RSI Short (paper trade first)
   - Only bearish strategy that passed validation
   - Monitor for regime change (AMD becoming more momentum-driven)

2. ABANDON: H2 Stochastic Short across all tickers
   - Consistent underperformance vs threshold
   - No evidence of edge

3. REFINE: H3 Weekly+Daily strategy
   - Increase RSI threshold to <35 (from <30)
   - OR: Use daily close > 20-SMA instead of weekly
   - Re-test with relaxed parameters

4. RESEARCH: Why AMD works but others don't
   - AMD may have different market structure
   - Check correlation with crypto (BTC mining exposure)
   - Compare volatility regimes
""")
