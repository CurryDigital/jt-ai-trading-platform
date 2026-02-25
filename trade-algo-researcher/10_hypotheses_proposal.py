#!/usr/bin/env python3
"""
10 HYPOTHESES FOR 3-TIER VALIDATION
Properly tested, null hypothesis first, rigorous methodology

Null Hypothesis: The strategy has no edge (win rate ≤ 50%)
Alternative: Win rate > 55% with statistical significance

Data Available:
- US: SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA, META, GOOGL, AMD, COIN, MSTR
- HK: 0700.HK, 9988.HK, 3690.HK (plus others)
- Sector ETFs: XLF, XLK, XLE, XLV, XLI, XLP, XLU, XLB
- FX: EURUSD, GBPUSD, USDJPY
- Technical Indicators: RSI, BB, MACD, ATR (pre-calculated for some)
"""

print('='*90)
print('10 HYPOTHESES FOR 3-TIER VALIDATION')
print('Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-Feb 2026')
print('='*90)

hypotheses = [
    {
        'id': 'H001',
        'name': 'QQQ RSI Extreme Mean Reversion',
        'description': 'QQQ RSI < 20 → 5-day mean reversion',
        'rationale': 'Index extreme oversold conditions revert due to diversification',
        'ticker': 'QQQ',
        'entry': 'RSI(14) < 20',
        'exit': '5 days or RSI > 50',
        'min_trades': 20,
        'expected_win': 0.60,
        'data_status': '✅ Available',
        'risk': 'Low - diversified index'
    },
    {
        'id': 'H002',
        'name': 'HK Tech Lead-Lag (QQQ → 0700.HK)',
        'description': 'QQQ performance predicts 0700.HK next-day direction',
        'rationale': 'Information diffusion from US tech to HK tech (12-16hr gap)',
        'ticker': '0700.HK',
        'entry': 'QQQ > +1% → Buy 0700.HK at HK open',
        'exit': '1 day hold',
        'min_trades': 50,
        'expected_win': 0.58,
        'data_status': '✅ Available',
        'risk': 'Medium - cross-market correlation decay'
    },
    {
        'id': 'H003',
        'name': 'Sector Rotation Momentum (XLK vs XLF)',
        'description': 'Tech/Financial relative momentum persistence',
        'rationale': 'Sector trends persist due to capital flow inertia',
        'ticker': 'XLK',
        'entry': 'XLK/XLF ratio > 20-day SMA + XLK > SMA50',
        'exit': '10 days or ratio < SMA',
        'min_trades': 30,
        'expected_win': 0.58,
        'data_status': '✅ Available',
        'risk': 'Low - sector ETF diversified'
    },
    {
        'id': 'H004',
        'name': 'Volatility Expansion After Compression (SPY)',
        'description': 'ATR compression → expansion pattern',
        'rationale': 'Volatility is mean-reverting; compression precedes expansion',
        'ticker': 'SPY',
        'entry': 'ATR(14) < 5th percentile(120d) + volume > 1.5x avg',
        'exit': '5 days or ATR > 50th percentile',
        'min_trades': 25,
        'expected_win': 0.62,
        'data_status': '✅ Available',
        'risk': 'Low - SPY liquid, defined exit'
    },
    {
        'id': 'H005',
        'name': 'NVDA Earnings Momentum Persistence',
        'description': 'Post-earnings drift continuation',
        'rationale': 'Underreaction to earnings news persists for days',
        'ticker': 'NVDA',
        'entry': 'Price > SMA20 + volume > 2x avg + close > open',
        'exit': '3 days',
        'min_trades': 40,
        'expected_win': 0.58,
        'data_status': '✅ Available',
        'risk': 'High - single stock concentration'
    },
    {
        'id': 'H006',
        'name': 'USD/JPY Trend Following (FX)',
        'description': 'Trend persistence in major FX pair',
        'rationale': 'Macro trends in USD/JPY persist due to rate differentials',
        'ticker': 'USDJPY',
        'entry': 'Price > SMA20 + SMA20 > SMA50',
        'exit': '10 days or price < SMA20',
        'min_trades': 60,
        'expected_win': 0.55,
        'data_status': '✅ Available (FX)',
        'risk': 'Medium - FX volatility, overnight gaps'
    },
    {
        'id': 'H007',
        'name': 'Defensive Sector Flight (XLU vs SPY)',
        'description': 'Utilities outperformance during SPY weakness',
        'rationale': 'Flight to safety in defensive sectors during market stress',
        'ticker': 'XLU',
        'entry': 'SPY < SMA50 (weak market) + XLU > SMA20',
        'exit': '5 days or SPY > SMA50',
        'min_trades': 30,
        'expected_win': 0.57,
        'data_status': '✅ Available',
        'risk': 'Low - defensive, regime-dependent'
    },
    {
        'id': 'H008',
        'name': 'Energy Momentum (XLE) with Oil Correlation',
        'description': 'Energy sector momentum during trend phases',
        'rationale': 'Energy stocks trend strongly during commodity cycles',
        'ticker': 'XLE',
        'entry': 'XLE > SMA20 + RSI > 50 + volume > 1.5x',
        'exit': '7 days or RSI < 40',
        'min_trades': 35,
        'expected_win': 0.56,
        'data_status': '✅ Available',
        'risk': 'Medium - commodity cyclical'
    },
    {
        'id': 'H009',
        'name': 'Crypto-Equity Correlation Arbitrage (MSTR vs BTC)',
        'description': 'MSTR leads/lags BTC price moves',
        'rationale': 'MSTR is BTC proxy; intraday correlation breakdowns revert',
        'ticker': 'MSTR',
        'entry': 'BTC +2% prior day + MSTR flat/open lower',
        'exit': '1 day',
        'min_trades': 40,
        'expected_win': 0.60,
        'data_status': '⚠️ BTC data in bronze.yf_prices (need to verify)',
        'risk': 'High - crypto volatility, single stock'
    },
    {
        'id': 'H010',
        'name': 'Alibaba HK Mean Reversion (9988.HK)',
        'description': 'Extreme moves in BABA HK revert',
        'rationale': 'China tech oversold conditions historically mean-revert',
        'ticker': '9988.HK',
        'entry': 'RSI < 25 + price < BB lower',
        'exit': '5 days or RSI > 50',
        'min_trades': 25,
        'expected_win': 0.58,
        'data_status': '✅ Available',
        'risk': 'High - China regulatory risk, single stock'
    }
]

for h in hypotheses:
    print(f'\n{"="*90}')
    print(f"{h['id']}: {h['name']}")
    print(f'{"="*90}')
    print(f"Ticker: {h['ticker']}")
    print(f"Rationale: {h['rationale']}")
    print(f"Entry: {h['entry']}")
    print(f"Exit: {h['exit']}")
    print(f"Min Trades Needed: {h['min_trades']}")
    print(f"Expected Win Rate: {h['expected_win']:.0%}")
    print(f"Data Status: {h['data_status']}")
    print(f"Risk Level: {h['risk']}")

print('\n' + '='*90)
print('DATA REQUESTS NEEDED')
print('='*90)

print('''
✅ NO IMMEDIATE REQUESTS
All 10 hypotheses can be tested with current data:
- US stocks: SPY, QQQ, NVDA, MSTR
- HK stocks: 0700.HK, 9988.HK
- ETFs: XLU, XLE, XLK, XLF
- FX: USDJPY

⚠️ NOTE: H009 (MSTR-BTC) requires BTC data verification
- BTC-USD should be in bronze.yf_prices based on indicators
- Will verify during testing
''')

print('\n' + '='*90)
print('TESTING PROTOCOL')
print('='*90)

print('''
For EACH hypothesis:
1. Calculate signals on full dataset (2021-2026)
2. Split into 3 periods:
   - Train: 2021-01-01 to 2022-12-31
   - Test: 2023-01-01 to 2024-12-31
   - Validate: 2025-01-01 to 2026-02-20

3. For each period:
   - Count trades (n)
   - Calculate win rate (%)
   - Calculate Sharpe ratio
   - Calculate 95% confidence interval
   - Check decay (Test vs Train, Validate vs Test)

4. Classification:
   - 🏆 Golden: All periods ≥60%, n≥20, decay <20%
   - ✅ Validated: Test ≥60%, Val ≥55%, n≥15
   - 🟡 Borderline: Test ≥55%, Val ≥50%
   - ❌ Failed: Val <50% or insufficient trades

5. Report:
   - Entry/exit rules
   - All 3 period results
   - Decay analysis
   - 95% confidence intervals
   - Deployment recommendation
''')

print('\n' + '='*90)
print('STARTING TESTING NOW')
print('='*90)
