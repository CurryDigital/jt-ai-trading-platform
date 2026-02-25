#!/usr/bin/env python3
"""
Example: Testing Latest 3-Month P&L Feature
Demonstrates how recent performance affects feasibility assessment
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest')
from backtest_analytics import BacktestAnalytics

# Create example trade data with dates spanning 1 year
np.random.seed(42)

# Generate dates (trading days only)
end_date = datetime(2025, 2, 25)
dates = []
current = end_date - timedelta(days=365)
while current <= end_date:
    if current.weekday() < 5:  # Monday = 0, Friday = 4
        dates.append(current)
    current += timedelta(days=1)

# Simulate trade P&Ls
# Scenario A: Strong recent performance (last 3 months hot)
np.random.seed(42)
trades_a = []
for date in dates[::10]:  # Trade every 10 days
    # Recent trades (last 3 months) are profitable
    if date > end_date - timedelta(days=90):
        pnl = np.random.uniform(1, 4)  # Profitable
    else:
        pnl = np.random.uniform(-2, 3)  # Mixed
    trades_a.append({'exit_date': date, 'pnl': pnl})

# Scenario B: Declining recent performance (last 3 months cold)
trades_b = []
for date in dates[::10]:
    # Recent trades (last 3 months) are unprofitable
    if date > end_date - timedelta(days=90):
        pnl = np.random.uniform(-3, 1)  # Losing
    else:
        pnl = np.random.uniform(-1, 4)  # Profitable historically
    trades_b.append({'exit_date': date, 'pnl': pnl})

# Scenario C: Consistent performance
trades_c = []
for date in dates[::10]:
    pnl = np.random.uniform(-1.5, 3.5)  # Consistently profitable
    trades_c.append({'exit_date': date, 'pnl': pnl})

# Calculate metrics for each scenario
analytics = BacktestAnalytics()

df_a = pd.DataFrame(trades_a)
df_b = pd.DataFrame(trades_b)
df_c = pd.DataFrame(trades_c)

metrics_a = analytics.calculate_metrics(df_a, hold_days=10)
metrics_b = analytics.calculate_metrics(df_b, hold_days=10)
metrics_c = analytics.calculate_metrics(df_c, hold_days=10)

print("="*80)
print("LATEST 3-MONTH P&L DEMONSTRATION")
print("="*80)
print("\nThis shows why latest 3-month performance matters for feasibility:")
print("-"*80)

print("\n" + "="*80)
print("SCENARIO A: HOT RECENT PERFORMANCE (Last 3M Strong)")
print("="*80)
print(f"Historical Return:    {metrics_a['total_return_pct']:+.2f}%")
print(f"Historical Win Rate:  {metrics_a['win_rate']:.1f}%")
print(f"\n📅 LATEST 3-MONTH:")
print(f"  3M Return:          {metrics_a['latest_3m_return']:+.2f}%")
print(f"  3M Trades:          {metrics_a['latest_3m_trades']}")
print(f"  3M Win Rate:        {metrics_a['latest_3m_wr']:.1f}%")
print(f"  3M Expectancy:      {metrics_a['latest_3m_expectancy']:+.2f}%")
if metrics_a['latest_3m_return'] > 5:
    print(f"  🟢 FEASIBILITY:     HOT — Deploy now!")

print("\n" + "="*80)
print("SCENARIO B: COLD RECENT PERFORMANCE (Last 3M Weak)")
print("="*80)
print(f"Historical Return:    {metrics_b['total_return_pct']:+.2f}%")
print(f"Historical Win Rate:  {metrics_b['win_rate']:.1f}%")
print(f"\n📅 LATEST 3-MONTH:")
print(f"  3M Return:          {metrics_b['latest_3m_return']:+.2f}%")
print(f"  3M Trades:          {metrics_b['latest_3m_trades']}")
print(f"  3M Win Rate:        {metrics_b['latest_3m_wr']:.1f}%")
print(f"  3M Expectancy:      {metrics_b['latest_3m_expectancy']:+.2f}%")
if metrics_b['latest_3m_return'] < 0:
    print(f"  🔴 FEASIBILITY:     COLD — Strategy decay/regime change detected!")

print("\n" + "="*80)
print("SCENARIO C: CONSISTENT PERFORMANCE (No Decay)")
print("="*80)
print(f"Historical Return:    {metrics_c['total_return_pct']:+.2f}%")
print(f"Historical Win Rate:  {metrics_c['win_rate']:.1f}%")
print(f"\n📅 LATEST 3-MONTH:")
print(f"  3M Return:          {metrics_c['latest_3m_return']:+.2f}%")
print(f"  3M Trades:          {metrics_c['latest_3m_trades']}")
print(f"  3M Win Rate:        {metrics_c['latest_3m_wr']:.1f}%")
print(f"  3M Expectancy:      {metrics_c['latest_3m_expectancy']:+.2f}%")
if metrics_c['latest_3m_return'] > 0:
    print(f"  🟡 FEASIBILITY:     WARM — Consistent performance")

print("\n" + "="*80)
print("KEY INSIGHT:")
print("="*80)
print("""
Historical performance can be misleading if recent performance has degraded.

The "Latest 3-Month P&L" metric helps identify:
1. 🟢 HOT strategies — Recent strong performance (deploy now)
2. 🔴 COLD strategies — Recent weakness (avoid, possible decay)
3. 🟡 WARM strategies — Consistent (safe to deploy)
4. ⚪ UNKNOWN — Insufficient recent data (wait for more signals)

This is critical for assessing REAL feasibility for paper/live trading.
""")
