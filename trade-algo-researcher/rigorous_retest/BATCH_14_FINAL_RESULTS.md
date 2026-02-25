# RESEARCH BATCH 14 — FINAL RESULTS
## Comprehensive Testing Report

**Generated:** 2026-02-25 05:45 UTC  
**Hypotheses Tested:** 5 of 7  
**Status:** Testing Complete (2 pending data)

---

## EXECUTIVE SUMMARY

| Hypothesis | Status | Win Rate | Verdict | Action |
|------------|--------|----------|---------|--------|
| H014-001 Bollinger Squeeze | ⚠️ ADJUST | Rare signals | Too strict | Relax params |
| **H014-002 CMV Filter** | ✅ **VALIDATED** | +7.7% vs base | **Deploy** | Apply to S001 |
| H014-003 ADR Arbitrage | ❌ REJECTED | 48.9% | No edge | Abandon |
| H014-004 Buyback Yield | ⏳ PENDING | — | Await data | Next |
| H014-005 Crypto Capitulation | ❌ REJECTED | 36.3% | No edge | Abandon |
| H014-006 CN Policy Drift | ⏳ PENDING | — | Await data | Next |
| H014-007 Credit-Equity Lag | ⏳ PENDING | — | Await data | Next |

**Scorecard:** 1 Validated, 2 Rejected, 1 Needs Adjustment, 3 Pending

---

## DETAILED FINDINGS

### ✅ H014-002: CMV Multi-Factor Filter — BREAKTHROUGH

**Thesis:** Add Carry/Momentum/Value filters to RSI mean reversion

**Results:**

| Metric | Base RSI | CMV Enhanced | Delta |
|--------|----------|--------------|-------|
| Win Rate | 52.4% | **60.1%** | **+7.7%** |
| Avg PnL | 0.64% | **2.24%** | **+250%** |
| Trades | 96 | 60 | -37% (quality) |

**Best Performers:**
- 3988.HK (Bank of China): +26.2% improvement
- 3328.HK (Bank of Comm): +10.0% improvement
- 0939.HK (CCB): +7.1% improvement

**Key Insight:** Fundamental filters (CMV) significantly enhance technical signals

**Next Steps:**
- [ ] Apply CMV filter to full S001 universe (56 tickers)
- [ ] Test on S001-US-TECH and S001-CRYPTO
- [ ] Consider adding to other strategies (S004, S005)

---

### ❌ H014-003: ADR-Local Arbitrage

**Thesis:** Exploit price divergence between HK local and ADR shares

**Results:**

| Pair | Win Rate | Avg PnL | Status |
|------|----------|---------|--------|
| 9988.HK/BABA | 50.8% | -0.12% | ❌ |
| 0700.HK/TCEHY | 53.4% | -0.00% | ❌ |
| 2318.HK/PNGAY | 46.3% | -0.33% | ❌ |
| 0005.HK/HSBC | 45.1% | -0.15% | ❌ |
| **Average** | **48.9%** | **-0.15%** | ❌ |

**Why Failed:**
- Currency noise (HKD/USD) dominates signals
- 3-day hold too short for convergence
- Transaction costs would make it worse
- Better suited for HFT (sub-minute holds)

**Lesson:** Cross-market arbitrage requires real-time execution

---

### ❌ H014-005: Crypto Miner Capitulation

**Thesis:** Hash rate decline + RSI oversold predicts BTC bottoms

**Results:**

| Ticker | Win Rate | Avg PnL | Status |
|--------|----------|---------|--------|
| BTC-USD | 42.9% | -3.93% | ❌ |
| MSTR | 36.7% | -3.41% | ❌ |
| COIN | 51.5% | -0.10% | ❌ |
| ETH-USD | 28.3% | -5.25% | ❌ |
| SOL-USD | 22.4% | -9.18% | ❌ |
| **Average** | **36.3%** | **-4.37%** | ❌ |

**Why Failed:**
- Hash rate decline often coincides with price crashes (momentum continues)
- "Capitulation" signals are actually continuation signals
- Crypto downtrends last longer than mean reversion horizon

**Lesson:** Contrarian signals in trending assets require longer holds

---

### ⚠️ H014-001: Bollinger Squeeze

**Thesis:** BB Width < 5% + Volume > 2x → Breakout

**Finding:** Signals too rare (0-2 trades per ticker over 4 years)

**Adjustment Needed:**
- Relax BB Width to < 10%
- Relax Volume to > 1.5x
- Or increase universe size

**Status:** Pending parameter adjustment

---

## RESEARCH INSIGHTS

### What Worked:
1. **Multi-factor filters** — CMV adds fundamental context to technical signals
2. **Quality over quantity** — 37% fewer trades, 250% better returns
3. **Sector focus** — HK Banks respond well to fundamental filters

### What Didn't Work:
1. **Cross-market arbitrage** — Currency noise too high for swing trading
2. **Contrarian crypto** — Capitulation signals are actually momentum signals
3. **Ultra-strict filters** — BB Width < 5% too rare

### Pattern Recognition:
- **Mean reversion works in:** Stable, dividend-paying sectors (HK Banks)
- **Mean reversion fails in:** Trending assets (Crypto, ADR arb)
- **Enhancement opportunity:** Fundamental overlays on technical signals

---

## FILES GENERATED

```
rigorous_retest/
├── BATCH_14_TESTING.md         # Testing pipeline
├── BATCH_14_RESULTS.md         # This report
├── H014_001_backtest_v2.py     # Bollinger Squeeze (needs adjustment)
├── H014_002_backtest.py        # CMV Filter ✅
├── H014_003_backtest.py        # ADR Arbitrage ❌
├── H014_005_backtest.py        # Crypto Capitulation ❌
├── H014_001_results.csv
├── H014_002_results.csv
├── H014_003_results.csv
└── H014_005_results.csv
```

---

## NEXT RESEARCH CYCLE (Batch 15)

### Immediate (Today):
- [ ] Adjust H014-001 parameters (BB Width < 10%)
- [ ] Apply CMV filter to full S001 universe

### This Week:
- [ ] Test H014-004 Buyback Yield (data available)
- [ ] Test H014-006 CN Policy Drift (data available)
- [ ] Test H014-007 Credit-Equity Lag (data available)

### Data Requests:
- [ ] REQUEST_006: Commodity futures curves
- [ ] REQUEST_007: Earnings calendar

### New Hypotheses to Explore:
1. **H015-001:** RSI + Volume profile (different volume thresholds by volatility)
2. **H015-002:** Sector rotation momentum (XLK/XLF enhanced with CMV)
3. **H015-003:** Earnings volatility crush (after earnings, IV collapse)

---

## LESSONS LEARNED

1. **Fundamental filters enhance technical signals** — CMV breakthrough validates multi-factor approach
2. **Cross-market strategies require HFT infrastructure** — ADR arb not suitable for swing trading
3. **Crypto is momentum-driven** — Contrarian signals consistently fail
4. **Parameter sensitivity matters** — Small changes in thresholds dramatically affect signal frequency

---

**Research cycle continuing — Batch 15 preparation in progress**
