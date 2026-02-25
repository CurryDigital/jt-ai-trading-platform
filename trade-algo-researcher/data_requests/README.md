# Data Request Summary

**Date:** 2026-02-20  
**From:** Trade Algo Researcher  
**To:** Jacky (for JT Trading Agent)  
**Policy:** NO COMPROMISE - All requests blocking until fulfilled

---

## 🚨 ACTIVE DATA REQUESTS

### HIGH PRIORITY

| # | Hypothesis | Data Needed | Cost | Status |
|---|------------|-------------|------|--------|
| 001 | **Accruals Quality** | Historical accruals (2020-2024) | Free* | ⏳ PENDING |

**Details:** Need net income, operating cash flow, total assets from Compustat or FMP.
Free sources available (FMP, calculated from statements).

---

### MEDIUM PRIORITY

| # | Hypothesis | Data Needed | Cost | Recommendation |
|---|------------|-------------|------|----------------|
| 002 | **ESG Improvers** | ESG ratings history (2018-2024) | $12-60K/year | Budget approval needed |
| 003 | **Asian Session FX** | Hourly FX data (2020-2024) | FREE | TrueFX recommended |
| 004 | **Crypto Funding** | Funding rates (2020-2024) | FREE | Binance API |

**Details:**
- ESG: MSCI/Sustainalytics subscription
- FX: TrueFX free download
- Crypto: Binance API (need API key)

---

### LOW PRIORITY (Budget Required)

| # | Hypothesis | Data Needed | Cost | Affected Strategies |
|---|------------|-------------|------|---------------------|
| 005 | **Options Suite** | Options chain + Greeks | $2.4-24K/year | VRP, Gamma, Vol Crush |

**Details:**
- 3 hypotheses blocked
- Recommend Polygon.io ($200-500/month) to start
- Upgrade to ORATS if viable

---

## 💰 TOTAL COST ESTIMATE

| Priority | Annual Cost | Hypotheses Unblocked |
|----------|-------------|---------------------|
| High | $0 | 1 |
| Medium | $12-60K | 3 |
| Low | $2.4-24K | 3 |
| **TOTAL** | **$14.4-84K/year** | **7 hypotheses** |

---

## ✅ FREE OPTIONS AVAILABLE

1. **Accruals Quality:** Financial Modeling Prep (FMP) - FREE tier
2. **Asian Session FX:** TrueFX - FREE download
3. **Crypto Funding:** Binance API - FREE with API key

**Recommendation:** Start with free options for high/medium priority.

---

## 📊 IMPACT ON BACKLOG

### Currently BLOCKED (Cannot Test):
- Accruals Quality
- ESG Improvers
- Asian Session FX
- Crypto Funding Rate
- VRP
- Gamma Gravity
- Vol Crush

**Total: 7 of 35 testing hypotheses (20%)**

### Can Proceed Without Data:
- Momentum Lifecycle ✅ (tested, validated)
- RSI Mean Reversion ✅ (tested, 0.98 Sharpe)
- Quality Value QARP (can use gold.stock_metrics)
- Time-Series Momentum (can use silver prices)
- Inflation Regime (can use BLS macro data)
- PEAD (can use gold.earnings_data)

---

## 🎯 RECOMMENDED ACTION PLAN

### Week 1 (Immediate):
1. ✅ Approve FREE data requests
2. Set up Binance API key
3. Download TrueFX hourly data
4. Register FMP account for accruals

### Week 2-4:
5. Evaluate ESG data ROI ($12-60K/year for 1 hypothesis)
6. Test options data with Polygon.io trial
7. Prioritize based on validation results

---

## 📝 FILES CREATED

```
data_requests/
├── REQUEST_001_Accruals_Quality.md
├── REQUEST_002_ESG_Ratings.md
├── REQUEST_003_FX_Hourly.md
├── REQUEST_004_Crypto_Funding.md
└── REQUEST_005_Options_Data.md
```

---

## 🛑 POLICY REMINDER

**NO PROXY DATA. NO WORKAROUNDS. NO COMPROMISE.**

All 7 hypotheses above are **BLOCKED** until:
- JT Trading Agent backfills data, OR
- User approves budget for paid data, OR
- User approves free alternative

**Current approach:**
- ✅ Test hypotheses with available data (silver/gold)
- ⏳ Pause blocked hypotheses
- 📧 Send requests to JT Trading Agent
- ⏱️ Wait for fulfillment

---

**Next Update:** After data requests fulfilled
