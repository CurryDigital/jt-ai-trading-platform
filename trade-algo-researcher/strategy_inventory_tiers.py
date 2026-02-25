#!/usr/bin/env python3
"""
COMPLETE STRATEGY INVENTORY WITH 3-PERIOD TIERS
All strategies tested with Train/Test/Validate
"""

print('='*100)
print('COMPLETE STRATEGY INVENTORY')
print('3-Period Validation: Train (2021-22) | Test (2023-24) | Validate (2025-26)')
print('='*100)

# Results from comprehensive validation
results = [
    # (ID, Name, Ticker, Train_WR, Test_WR, Val_WR, Train_n, Test_n, Val_n, Tier)
    ('G012', 'BB Squeeze Breakout', 'SPY', 62.5, 73.3, 63.2, 8, 15, 19, '🏆 TIER 1: True Golden'),
    ('G007', 'Momentum Trend', 'NVDA', 51.5, 62.9, 73.5, 204, 275, 113, '✅ TIER 2: Validated'),
    ('Near-Golden', 'Momentum Trend', 'QQQ', 40.9, 71.1, 79.0, 149, 242, 81, '✅ TIER 2: Validated'),
    ('G005', 'Momentum Trend', 'MSFT', 48.0, 59.2, 73.4, 177, 213, 94, '✅ TIER 2: Validated'),
    ('Near-Golden', 'BB Squeeze', 'NVDA', 41.2, 66.7, 60.0, 17, 12, 10, '✅ TIER 2: Validated'),
    ('G002', 'RSI <20 Mean Rev', 'MSTR', 52.9, 87.5, 55.6, 17, 8, 9, '🟡 TIER 3: Monitor'),
    ('G001', 'RSI <20 Mean Rev', 'COIN', 45.8, 100.0, 58.3, 24, 10, 12, '🟡 TIER 3: Monitor'),
    ('G003', 'Momentum Trend', 'MSTR', 30.5, 49.4, 36.0, 118, 235, 50, '❌ TIER 4: Failed'),
    ('G006', 'Momentum Trend', 'TSLA', 39.3, 55.2, 45.2, 135, 181, 93, '❌ TIER 4: Failed'),
    ('G010', '3-Day Reversal', 'QQQ', 64.3, 83.3, 0.0, 14, 6, 0, '❌ TIER 4: Failed'),
]

print('\n' + '='*100)
print('🏆 TIER 1: TRUE GOLDEN (All Periods ≥60%)')
print('='*100)
print(f'{"ID":<8} {"Strategy":<25} {"Ticker":<8} {"Train":<8} {"Test":<8} {"Val":<8} {"n":<12}')
print('-'*100)
for r in results:
    if r[9] == '🏆 TIER 1: True Golden':
        print(f'{r[0]:<8} {r[1]:<25} {r[2]:<8} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}% ({r[6]}/{r[7]}/{r[8]})')

print('\n' + '='*100)
print('✅ TIER 2: VALIDATED (Test≥60%, Val≥55%)')
print('='*100)
print(f'{"ID":<8} {"Strategy":<25} {"Ticker":<8} {"Train":<8} {"Test":<8} {"Val":<8} {"n":<12}')
print('-'*100)
for r in results:
    if r[9] == '✅ TIER 2: Validated':
        print(f'{r[0]:<8} {r[1]:<25} {r[2]:<8} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}% ({r[6]}/{r[7]}/{r[8]})')

print('\n' + '='*100)
print('🟡 TIER 3: MONITOR (Test outlier or inconsistent)')
print('='*100)
print(f'{"ID":<8} {"Strategy":<25} {"Ticker":<8} {"Train":<8} {"Test":<8} {"Val":<8} {"n":<12}')
print('-'*100)
for r in results:
    if r[9] == '🟡 TIER 3: Monitor':
        print(f'{r[0]:<8} {r[1]:<25} {r[2]:<8} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}% ({r[6]}/{r[7]}/{r[8]})')

print('\n' + '='*100)
print('❌ TIER 4: FAILED (Validate <50%)')
print('='*100)
print(f'{"ID":<8} {"Strategy":<25} {"Ticker":<8} {"Train":<8} {"Test":<8} {"Val":<8} {"n":<12}')
print('-'*100)
for r in results:
    if r[9] == '❌ TIER 4: Failed':
        print(f'{r[0]:<8} {r[1]:<25} {r[2]:<8} {r[3]:>6.1f}% {r[4]:>6.1f}% {r[5]:>6.1f}% ({r[6]}/{r[7]}/{r[8]})')

print('\n' + '='*100)
print('SUMMARY BY TIER')
print('='*100)

tier_counts = {}
for r in results:
    tier = r[9]
    tier_counts[tier] = tier_counts.get(tier, 0) + 1

for tier, count in sorted(tier_counts.items()):
    print(f'{tier}: {count} strategies')

print(f'\nTotal Strategies Tested: {len(results)}')
print('='*100)

print('\n' + '='*100)
print('DEPLOYMENT RECOMMENDATIONS')
print('='*100)
print('''
🏆 TIER 1 (Deploy with FULL confidence):
   → G012 SPY BB Squeeze only
   → All 3 periods ≥60%, consistent performance
   → 1 strategy

✅ TIER 2 (Deploy with CAUTION):
   → G007 NVDA Momentum, QQQ Momentum, G005 MSFT, NVDA BB Squeeze
   → Test ≥60%, Validate ≥55%, improving trend
   → 4 strategies
   → Position size: 50% of normal
   → Monitor closely for first 10 trades

🟡 TIER 3 (MONITOR only - Paper trading):
   → G001 COIN RSI<20, G002 MSTR RSI<20
   → Test was bull market outlier (100%, 87.5%)
   → Validate much lower (58%, 55%)
   → 2 strategies
   → Paper trade only
   → Need 20 more validate trades to decide

❌ TIER 4 (DO NOT DEPLOY):
   → G003 MSTR Momentum, G006 TSLA Momentum, G010 QQQ 3-Day Rev
   → Validate <50% or zero trades
   → 3 strategies
   → Rejected from deployment
''')
print('='*100)
