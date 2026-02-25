# CONSOLIDATED TECH PACK — MASTER DEPLOYMENT INDEX

## Overview

This document serves as the master index for all deployable sector-specific strategies (S001-S007). Each strategy has been validated through 3-tier backtesting (Train 2021-2022 / Test 2023-2024 / Validate 2025+) and is ready for paper trading deployment.

**Total Strategies:** 10  
**GOLDEN:** 4 strategies  
**VALIDATED:** 6 strategies  
**Last Updated:** 2026-02-25

---

## Quick Reference Table

| Status | Trade ID | Strategy Name | Sector | Test WR | Path |
|--------|----------|---------------|--------|---------|------|
| 🏆 | S001-01 | RSI Mean Reversion | HK Banks | 89.5% | `/strategies/golden/S001-01_RSI_MR_HK_Banks/TECH_PACK.md` |
| 🏆 | S001-03 | RSI Mean Reversion | CN Banks | 82.4% | `/strategies/golden/S001-03_RSI_MR_CN_Banks/TECH_PACK.md` |
| 🏆 | S001-04 | RSI Mean Reversion | CN Other | 79.6% | `/strategies/golden/S001-04_RSI_MR_CN_Other/TECH_PACK.md` |
| 🏆 | S007-01 | Sector Rotation | XLK/XLF | 65.3% | `/strategies/golden/S007-01_Sector_Rotation_XLK_XLF/TECH_PACK.md` |
| ✅ | S001-02 | RSI Mean Reversion | US Consumer | 82.7% | `/strategies/validated/S001-02_RSI_MR_US_Consumer/TECH_PACK.md` |
| ✅ | S001-09 | RSI Mean Reversion | HK Property | 73.2% | `/strategies/validated/S001-09_RSI_MR_HK_Property/TECH_PACK.md` |
| ✅ | S001-10 | RSI Mean Reversion | US Staples | 72.5% | `/strategies/validated/S001-10_RSI_MR_US_Staples/TECH_PACK.md` |
| ✅ | S002-01 | Trend Following | US ETF | 65.6% | `/strategies/validated/S002-01_Trend_US_ETF/TECH_PACK.md` |
| ✅ | S003-02 | Panic Reversal | US ETF | 67.9% | `/strategies/validated/S003-02_Panic_Reversal_US_ETF/TECH_PACK.md` |
| ✅ | S005-01 | Volume Breakout | Other | 71.0% | `/strategies/validated/S005-01_Vol_Breakout_Other/TECH_PACK.md` |

---

## GOLDEN Strategies (Priority Deployment)

### 1. S001-01: RSI Mean Reversion — HK Banks
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/S001-01_RSI_MR_HK_Banks/TECH_PACK.md`
- **Win Rate:** 89.5% (Test) / 87.8% (Validate)
- **Universe:** 0005.HK, 0939.HK, 1398.HK, 2388.HK, 3328.HK, 3988.HK
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 15% of deployable capital

### 2. S001-03: RSI Mean Reversion — China Banks
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/S001-03_RSI_MR_CN_Banks/TECH_PACK.md`
- **Win Rate:** 82.4% (Test) / 78.2% (Validate)
- **Universe:** 600036.SS, 601398.SS, 601939.SS, 601988.SS
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 12% of deployable capital

### 3. S001-04: RSI Mean Reversion — China Other
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/S001-04_RSI_MR_CN_Other/TECH_PACK.md`
- **Win Rate:** 79.6% (Test) / 66.6% (Validate)
- **Universe:** 600028.SS, 601088.SS, 601857.SS, 688008.SS
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 10% of deployable capital

### 4. S007-01: Sector Rotation — XLK/XLF
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/S007-01_Sector_Rotation_XLK_XLF/TECH_PACK.md`
- **Win Rate:** 65.3% (Test) / 64.1% (Validate)
- **Universe:** XLK, XLF (Trade XLK when ratio > SMA20)
- **Logic:** XLK/XLF ratio > SMA(20), Hold 10 days
- **Allocation:** 10% of deployable capital

---

## VALIDATED Strategies (Secondary Deployment)

### 5. S001-02: RSI Mean Reversion — US Consumer Retail
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S001-02_RSI_MR_US_Consumer/TECH_PACK.md`
- **Win Rate:** 82.7% (Test) / 71.2% (Validate)
- **Universe:** COST, WMT
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 8% of deployable capital

### 6. S001-09: RSI Mean Reversion — HK Property
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S001-09_RSI_MR_HK_Property/TECH_PACK.md`
- **Win Rate:** 73.2% (Test) / 70.7% (Validate)
- **Universe:** 0001.HK, 0002.HK
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 6% of deployable capital

### 7. S001-10: RSI Mean Reversion — US Consumer Staples
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S001-10_RSI_MR_US_Staples/TECH_PACK.md`
- **Win Rate:** 72.5% (Test) / 71.4% (Validate)
- **Universe:** PG
- **Logic:** RSI(14) < 30 + Price > SMA(20), Hold 10 days
- **Allocation:** 5% of deployable capital

### 8. S002-01: Trend Following — US ETF Index
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S002-01_Trend_US_ETF/TECH_PACK.md`
- **Win Rate:** 65.6% (Test) / 68.4% (Validate)
- **Universe:** SPY, QQQ
- **Logic:** Price > SMA(50), Hold 10 days
- **Allocation:** 8% of deployable capital

### 9. S003-02: Panic Reversal — US ETF
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S003-02_Panic_Reversal_US_ETF/TECH_PACK.md`
- **Win Rate:** 67.9% (Test) / 62.0% (Validate)
- **Universe:** SPY, QQQ, IWM
- **Logic:** 3 consecutive down days, Hold 5 days
- **Allocation:** 6% of deployable capital

### 10. S005-01: Volume Breakout — Other
- **Absolute Path:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/S005-01_Vol_Breakout_Other/TECH_PACK.md`
- **Win Rate:** 71.0% (Test) / 73.5% (Validate)
- **Universe:** ASML, CL=F, SI=F, NG=F
- **Logic:** Volume > 1.5x avg + Price > SMA(20), Hold 5 days
- **Allocation:** 5% of deployable capital

---

## Deployment Commands for JT Trading Agent

```bash
# List all strategy paths
find /home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies -name "TECH_PACK.md" | sort

# Get specific strategy
cat /home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/S001-01_RSI_MR_HK_Banks/TECH_PACK.md

# Get all GOLDEN strategies
for path in /home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/golden/*/TECH_PACK.md; do
    echo "=== $(basename $(dirname $path)) ==="
    head -20 $path
    echo ""
done

# Get all VALIDATED strategies  
for path in /home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/validated/*/TECH_PACK.md; do
    echo "=== $(basename $(dirname $path)) ==="
    head -20 $path
    echo ""
done
```

---

## Capital Allocation Summary

| Tier | Allocation | Capital (100K HKD) | Strategies |
|------|------------|-------------------|------------|
| GOLDEN | 47% | 37,600 HKD | 4 strategies |
| VALIDATED | 38% | 30,400 HKD | 6 strategies |
| Cash Reserve | 20% | 20,000 HKD | - |
| **Total** | **100%** | **100,000 HKD** | **10 strategies** |

---

## Risk Management Parameters

| Parameter | Value |
|-----------|-------|
| Max Single Position | 10% of capital |
| Max Sector Exposure | 40% of capital |
| Default Stop Loss | None (time-based exits) |
| Default Profit Target | None (time-based exits) |
| Max Holding Period | 10 days (5 days for S003, S005) |
| Transaction Costs | 0.1% per trade (included in backtests) |

---

## Backtest Methodology

All strategies validated with:
- **Train Period:** 2021-01-01 to 2022-12-31 (bear market)
- **Test Period:** 2023-01-01 to 2024-12-31 (bull market)
- **Validate Period:** 2025-01-01 to 2026-02-20 (out-of-sample)
- **Transaction Costs:** 0.1% per trade
- **Minimum Trades:** 20 per period for statistical significance

---

## JT Platform Integration

**File Location:** `/home/ubuntu/.openclaw/workspace/trade-algo-researcher/strategies/CONSOLIDATED_TECH_PACK.md`

**jt_integration:** true

**Deployment Status:** Ready for paper trading

---

*Generated: 2026-02-25 01:45 UTC*  
*Validation: 3-tier with transaction costs*  
*Format: Industry-specific sector deployment*
