# RESEARCH BATCH 14 — RESULTS SUMMARY
## Hypothesis Testing & Backtesting Report

**Generated:** 2026-02-25  
**Status:** IN PROGRESS  
**Hypotheses Tested:** 3 of 7

---

## EXECUTIVE SUMMARY

| Hypothesis | Status | Win Rate | Sharpe | Verdict |
|------------|--------|----------|--------|---------|
| **H014-001** Bollinger Squeeze | 🔄 TESTING | — | — | Script ready |
| **H014-002** CMV Filter | ✅ VALIDATED | +7.7% vs base | — | DEPLOY |
| **H014-003** ADR Arbitrage | ❌ REJECTED | 48.9% | — | ABANDON |
| **H014-004** Buyback Yield | ⏳ PENDING | — | — | Next |
| **H014-005** Crypto Capitulation | ⏳ PENDING | — | — | Next |
| **H014-006** CN Policy Drift | ⏳ PENDING | — | — | Next |
| **H014-007** Credit-Equity Lag | ⏳ PENDING | — | — | Next |

---

## DETAILED RESULTS

### ✅ H014-002: CMV Multi-Factor Filter — VALIDATED

**Objective:** Enhance S001 (RSI Mean Reversion) with Carry/Momentum/Value filter

**Methodology:**
- Base: RSI < 25 only
- Enhanced: RSI < 25 + CMV score filter
- Universe: 7 HK Bank tickers
- Hold: 10 days

**Results:**

| Metric | Base Strategy | CMV Enhanced | Delta |
|--------|---------------|--------------|-------|
| **Win Rate** | 52.4% | 60.1% | **+7.7%** |
| **Total Trades** | 96 | 60 | -36 |
| **Avg PnL** | 0.64% | 2.24% | +1.60% |
| **Boosted Trades** | — | 28 | — |
| **Avg Boosted PnL** | — | 3.42% | — |

**Key Findings:**
- ✅ Win rate improved from 52.4% to 60.1%
- ✅ Average PnL increased 3.5x (0.64% → 2.24%)
- ✅ Filter reduced trades by 37.5% (quality over quantity)
- ✅ Boosted trades (CMV > 0.6) showed 3.42% avg return

**Ticker Breakdown:**

| Ticker | Base WR | CMV WR | Improvement |
|--------|---------|--------|-------------|
| 3988.HK | 57.1% | 83.3% | **+26.2%** |
| 1398.HK | 58.8% | 63.6% | +4.8% |
| 3328.HK | 50.0% | 60.0% | +10.0% |
| 0939.HK | 42.9% | 50.0% | +7.1% |
| 2388.HK | 66.7% | 69.2% | +2.5% |
| 0005.HK | 52.9% | 50.0% | -2.9% |
| 3968.HK | 38.5% | 44.4% | +5.9% |

**Decision:** ✅ **VALIDATED** — Deploy CMV filter to S001 strategies

**Next Steps:**
- [ ] Apply CMV filter to full S001 universe (56 tickers)
- [ ] Test on S001-US-TECH and S001-CRYPTO
- [ ] Update position sizing logic in existing strategies

---

### ❌ H014-003: ADR-Local Arbitrage — REJECTED

**Objective:** Exploit price divergence between HK local shares and ADRs

**Methodology:**
- Entry: |Z-score| > 2.0 (price divergence)
- Exit: 3 days later (mean reversion)
- Pairs: 4 (9988/BABA, 0700/TCEHY, 2318/PNGAY, 0005/HSBC)

**Results:**

| Pair | Trades | Win Rate | Avg PnL | Status |
|------|--------|----------|---------|--------|
| 9988.HK/BABA | 63 | 50.8% | -0.12% | ❌ |
| 0700.HK/TCEHY | 58 | 53.4% | -0.00% | ❌ |
| 2318.HK/PNGAY | 54 | 46.3% | -0.33% | ❌ |
| 0005.HK/HSBC | 71 | 45.1% | -0.15% | ❌ |
| **TOTAL** | **246** | **48.9%** | **-0.15%** | ❌ |

**Key Findings:**
- ❌ No pair achieved 55%+ win rate
- ❌ Negative average PnL across all pairs
- ❌ Transaction costs would worsen results
- ❌ Divergence doesn't reliably mean-revert in 3 days

**Reasons for Failure:**
1. **Currency noise:** HKD/USD fluctuations add noise
2. **Timing mismatch:** ADR and local markets open at different times
3. **Liquidity differences:** Slippage on reversion trades
4. **3-day hold too short:** Mean reversion takes longer

**Decision:** ❌ **REJECTED** — Abandon ADR arbitrage strategy

**Lessons Learned:**
- ADR arbitrage requires real-time execution (sub-minute)
- 3-day hold insufficient for convergence
- Need to account for currency hedging costs
- Better suited for HFT, not swing trading

---

## INSIGHTS & DISCOVERIES

### What Worked:
1. **CMV Multi-Factor Filter** — Adding fundamental filters to technical signals improved win rate +7.7%
2. **Quality over Quantity** — Reducing trades by 37.5% improved average return 3.5x
3. **Ticker-Specific Optimization** — 3988.HK showed +26% improvement with CMV

### What Didn't Work:
1. **ADR Arbitrage** — Cross-market arbitrage too noisy for 3-day holds
2. **Simple Z-Score Divergence** — Doesn't account for regime changes
3. **Short Hold Periods** — Mean reversion in ADR spreads requires longer holds

### New Hypotheses to Explore:
Based on these results, consider testing:
1. **H014-011:** Longer hold (10+ days) for ADR divergence
2. **H014-012:** CMV filter on other strategies (S004, S005)
3. **H014-013:** Currency-hedged ADR arbitrage

---

## FILES CREATED

```
rigorous_retest/
├── BATCH_14_TESTING.md           # Testing pipeline
├── H014_001_backtest.py          # Bollinger Squeeze (ready)
├── H014_002_backtest.py          # CMV Filter ✅
├── H014_003_backtest.py          # ADR Arbitrage ❌
├── H014_002_results.csv          # CMV results
├── H014_003_results.csv          # ADR results
└── BATCH_14_RESULTS.md           # This file
```

---

## NEXT ACTIONS

### Immediate (Today):
- [ ] Run H014-001 (Bollinger Squeeze) on 204 tickers
- [ ] Extend H014-002 to full S001 universe

### This Week:
- [ ] Test H014-004 (Buyback Yield Premium)
- [ ] Test H014-005 (Crypto Miner Capitulation)
- [ ] Test H014-006 (CN Policy Drift)
- [ ] File data requests for H014-008/009/010

### Research Notes:
- CMV filter shows promise — expand to other strategies
- ADR arbitrage rejected — focus on single-market strategies
- Bollinger Squeeze still testing — expect results by EOD

---

*Research cycle active — 4 more hypotheses in queue*
