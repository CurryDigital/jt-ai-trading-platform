#!/usr/bin/env python3
"""
RIGOROUS COUNT: What Actually Counts as Deployable?
Minimum criteria: Test >=55%, >=10 trades, Decay <20%
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

print('='*70)
print('RIGOROUS COUNT: Deployable vs Insufficient Data')
print('Minimum: Test >=55% AND >=10 trades AND Decay <20%')
print('='*70)

# All strategies from expanded research
strategies = [
    # (Name, Test Win%, Test Trades, Decay%, Category)
    ("COIN RSI <20", 100.0, 10, -44.2, "MeanRev"),
    ("MSTR RSI <20", 87.5, 8, -26.6, "MeanRev"),  # <10 trades
    ("ATR Compression", 85.7, 7, 14.3, "Volatility"),  # <10 trades
    ("COIN Strong Uptrend", 85.7, 21, -24.2, "MeanRev"),
    ("IWM SPY Regime", 80.0, 10, -46.7, "MeanRev"),
    ("RSI Divergence", 80.0, 10, 24.4, "MeanRev"),  # High decay
    ("Friday Volume BO", 77.8, 9, 40.3, "Time"),  # <10 trades, high decay
    ("12M Momentum", 75.8, 227, 75.8, "Momentum"),  # High decay (0% train!)
    ("3-Day Reversal", 71.0, 31, 18.5, "MeanRev"),
    ("IWM Lead-Lag", 70.6, 17, 8.1, "CrossMkt"),
    ("BB Squeeze", 66.7, 147, 8.0, "Volatility"),
    ("Hammer Pattern", 66.7, 12, 12.2, "Pattern"),
    ("ADX >25", 65.4, 471, 15.4, "Trend"),
    ("Bullish Engulfing", 65.9, 41, 14.7, "Pattern"),
    ("MSTR SPY Regime", 62.5, 8, 11.2, "MeanRev"),  # <10 trades
    ("20D High Breakout", 62.9, 35, 1.1, "Breakout"),
    ("QQQ Lead-Lag", 61.1, 18, 7.3, "CrossMkt"),
    ("3M Momentum", 57.3, 178, 13.3, "Momentum"),
    ("50D High Breakout", 56.2, 32, 3.3, "Breakout"),
    ("Stochastic <20", 70.0, 60, 24.7, "MeanRev"),  # High decay
    ("Price >200d MA", 68.5, 292, 22.1, "Trend"),  # High decay
    ("Volume at Support", 100.0, 5, 50.0, "Volume"),  # <10 trades
    ("NVDA RSI <30", 92.9, 14, 62.5, "MeanRev"),  # High decay
    ("NVDA RSI <25", 90.0, 10, 60.0, "MeanRev"),  # High decay
    ("MSTR Vol>2x Break", 87.5, 16, 42.0, "Breakout"),  # High decay
    ("QQQ RSI <30", 87.5, 24, 36.5, "MeanRev"),  # High decay
    ("MSTR Vol>2.5x Break", 83.3, 6, 58.3, "Breakout"),  # <10, high decay
    ("NVDA Vol>1.5x Break", 83.3, 12, 20.8, "Breakout"),  # Decay>20%
    ("QQQ RSI <25", 85.7, 7, 55.7, "MeanRev"),  # <10, high decay
    ("SPY RSI <25", 81.8, 11, 31.8, "MeanRev"),  # High decay
    ("COIN RSI <25", 81.8, 22, 28.3, "MeanRev"),  # High decay
    ("IWM Vol>1.5x Break", 77.8, 9, 17.8, "Breakout"),  # <10
    ("BB%<=0 on NVDA", 77.8, 9, 27.8, "MeanRev"),  # <10, high decay
    ("MSTR RSI <25", 88.9, 9, -11.1, "MeanRev"),  # <10
    ("NVDA RSI <20", 80.0, 5, 46.7, "MeanRev"),  # <10, high decay
]

# STRICT CRITERIA for deployment
deployable = []
near_deployable = []  # 5-9 trades or decay 15-20%
insufficient = []
high_decay = []  # Decay >20%

for name, test_wr, n, decay, cat in strategies:
    if test_wr >= 55 and n >= 10 and abs(decay) < 20:
        deployable.append((name, test_wr, n, decay, cat))
    elif test_wr >= 55 and n >= 5 and abs(decay) < 25:
        near_deployable.append((name, test_wr, n, decay, cat))
    elif abs(decay) >= 20:
        high_decay.append((name, test_wr, n, decay, cat))
    else:
        insufficient.append((name, test_wr, n, decay, cat))

print('\n' + '='*70)
print('✅ TRULY DEPLOYABLE (Test>=55%, N>=10, Decay<20%)')
print('='*70)
for name, test_wr, n, decay, cat in sorted(deployable, key=lambda x: x[1], reverse=True):
    print(f'{name:.<35} {test_wr:>5.1f}%  ({n:>3} trades)  Decay:{decay:>+5.1f}%  [{cat}]')

print('\n' + '='*70)
print('🟡 NEAR DEPLOYABLE (Test>=55%, N>=5, Decay<25%)')
print('='*70)
for name, test_wr, n, decay, cat in sorted(near_deployable, key=lambda x: x[1], reverse=True):
    print(f'{name:.<35} {test_wr:>5.1f}%  ({n:>3} trades)  Decay:{decay:>+5.1f}%  [{cat}]')

print('\n' + '='*70)
print('⚠️  HIGH DECAY RISK (Decay >=20%) - Monitor Carefully')
print('='*70)
for name, test_wr, n, decay, cat in sorted(high_decay, key=lambda x: x[1], reverse=True)[:10]:
    print(f'{name:.<35} {test_wr:>5.1f}%  ({n:>3} trades)  Decay:{decay:>+5.1f}%  [{cat}]')

print('\n' + '='*70)
print('⏳ INSUFFICIENT DATA (<5 trades or Test<55%)')
print('='*70)
print(f'{len(insufficient)} strategies need more data or failed validation')

print('\n' + '='*70)
print('SUMMARY')
print('='*70)
print(f'✅ Deployable Now:       {len(deployable)} strategies')
print(f'🟡 Near Deployable:      {len(near_deployable)} strategies')
print(f'⚠️  High Decay Risk:      {len(high_decay)} strategies')
print(f'⏳ Insufficient:         {len(insufficient)} strategies')
print(f'📊 TOTAL TESTED:         {len(strategies)} strategies')
print('='*70)

print('\n' + '='*70)
print('REALISTIC PORTFOLIO (Deployable + Near Deployable)')
print('='*70)
print(f'Total: {len(deployable) + len(near_deployable)} strategies')
print('\nTop 10 by Win Rate:')
all_valid = deployable + near_deployable
for i, (name, test_wr, n, decay, cat) in enumerate(sorted(all_valid, key=lambda x: x[1], reverse=True)[:10], 1):
    status = "✅" if n >= 10 and abs(decay) < 20 else "🟡"
    print(f'{i:>2}. {status} {name:.<30} {test_wr:>5.1f}%  ({n:>3} trades)')
