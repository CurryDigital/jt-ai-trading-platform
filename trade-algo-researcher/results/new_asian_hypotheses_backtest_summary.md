# New Asian Hypotheses Backtest Results

**Date:** 2026-02-19  
**Tested:** 5 new hypotheses  
**Status:** Complete

---

## 1. AH Premium Arbitrage ✅ VALIDATED

**Concept:** Buy H-shares when AH premium > 30%, hold for mean reversion

### Results Summary

| Metric | Value |
|--------|-------|
| Pairs Tested | 9 dual-listed stocks |
| Pairs Viable | 9/9 (100%) |
| **Avg Win Rate** | **72.1%** |
| **Avg Sharpe** | **2.33** |
| **Avg Return/Trade** | **4.59%** |
| Hold Period | 20 days |

### Best Performers

| Pair | Win Rate | Sharpe | Total Return |
|------|----------|--------|--------------|
| ICBC (1398.HK/601398.SS) | **90.0%** | **4.56** | 100.6% |
| CCB (0939.HK/601939.SS) | **78.9%** | **2.38** | 88.9% |
| Bank of China (3988.HK/601988.SS) | **76.9%** | **2.99** | 52.3% |
| Agricultural Bank (1288.HK/601288.SS) | **68.8%** | **2.73** | 119.8% |
| Sinopec (0998.HK/600028.SS) | **69.6%** | **2.02** | 108.3% |

### Key Insights

- **All banks show strong performance** - Financials have most reliable AH premium mean reversion
- **Average entry premium:** 40-50% (H-shares at 40-50% discount to A-shares)
- **Average exit premium:** 30-40% (partial convergence)
- **ICBC best performer** - 90% win rate, highest Sharpe

### Deployment Recommendation

**Status:** ✅ **DEPLOY**

**Universe:** 
- 1398.HK (ICBC) - 90% win rate
- 0939.HK (CCB) - 79% win rate
- 3988.HK (Bank of China) - 77% win rate
- 1288.HK (Agricultural Bank) - 69% win rate
- 0998.HK (Sinopec) - 70% win rate

**Entry:** AH premium > 30% AND above historical average
**Exit:** 20 days or premium < 25%
**Sizing:** 2-3% per pair

---

## 2. Singapore REIT Dividend Capture ✅ VALIDATED

**Concept:** Buy S-REITs 14 days before quarter start, hold 21 days after

### Results Summary

| Metric | Value |
|--------|-------|
| REITs Tested | 6 (5 Singapore + 1 ETF proxy) |
| REITs Viable | 6/6 (100%) |
| **Avg Win Rate** | **72.9%** |
| **Avg Sharpe** | **0.73** |
| **Avg Total Return** | **2.46% per quarter** |
| Annualized Yield | ~10% (4 quarters × 2.5%) |

### Best Performers

| REIT | Win Rate | Total Return | Sharpe |
|------|----------|--------------|--------|
| EWS (Singapore ETF) | **87.5%** | 96.6% | **1.41** |
| AJBU.SI (Keppel Infra) | **75.0%** | 128.4% | 0.75 |
| ME8U.SI (Mapletree Industrial) | **75.0%** | 97.9% | 0.92 |
| M44U.SI (Mapletree Logistics) | **70.8%** | 76.8% | 0.67 |
| N2IU.SI (Mapletree Commercial) | **66.7%** | 21.8% | 0.31 |
| C38U.SI (CapitaLand ICT) | **62.5%** | 19.7% | 0.31 |

### Key Insights

- **EWS ETF best risk-adjusted** - 87.5% win rate, 1.41 Sharpe
- **Keppel Infrastructure highest return** - 128% total over 5 years
- **Price recovery + dividend = total return**
  - Price return: -0.3% to +2.8% (varies)
  - Dividend: +1.25% per quarter
  - **Total: 0.9% to 4.0% per quarter**

### Deployment Recommendation

**Status:** ✅ **DEPLOY**

**Universe (Best Risk-Adjusted):**
- EWS (diversified Singapore exposure) - 87.5% win
- AJBU.SI (Keppel Infrastructure) - 75% win, 4.01% avg return
- ME8U.SI (Mapletree Industrial) - 75% win, 3.10% avg return

**Schedule:**
- Entry: January, April, July, October (14 days before month start)
- Exit: 21 days after month start
- **Or use EWS for simplified single-ticker approach**

---

## 3. China Policy Announcement Drift ⏳ NOT TESTED

**Reason:** Requires real-time news data + NLP classification

**Data Needed:**
- Xinhua/SCMP/Caixin news feeds
- Policy announcement timestamps
- NLP model to classify bullish/bearish

**Estimated Performance:** Based on literature, 60-70% win rate expected

**Recommendation:** Test with news API subscription

---

## 4. HK Property NAV Discount ⏳ NOT TESTED

**Reason:** Requires NAV estimates not available via yfinance

**Data Needed:**
- Broker NAV estimates (Bloomberg, broker reports)
- Land sales data
- HIBOR rates

**Estimated Performance:** Based on current discounts (0.5-0.6x NAV), significant upside potential when Fed cuts

**Recommendation:** Wait for rate cut cycle, use broker reports for entry timing

---

## 5. Northbound Stock Connect Flow ⏳ NOT TESTED

**Reason:** Requires HKEX Stock Connect daily flow data

**Data Available:** HKEX website (free, but needs scraping)

**Estimated Performance:** 58-62% win rate based on flow persistence literature

**Recommendation:** Scrape HKEX data or use Eastmoney API

---

## Overall Assessment

| Hypothesis | Status | Win Rate | Sharpe | Deployable |
|------------|--------|----------|--------|------------|
| **AH Premium Arbitrage** | ✅ Validated | 72% | 2.33 | **YES** |
| **SG REIT Dividend** | ✅ Validated | 73% | 0.73 | **YES** |
| China Policy Drift | ⏳ Needs data | — | — | No |
| HK Property NAV | ⏳ Needs data | — | — | No |
| Northbound Flow | ⏳ Needs data | — | — | No |

---

## Immediate Deployment (Free Data)

### 1. AH Premium Strategy
- **Tickers:** 1398.HK, 0939.HK, 3988.HK, 1288.HK, 0998.HK
- **Frequency:** 2-4 trades per year per stock
- **Expected:** 70%+ win rate, 2.0+ Sharpe

### 2. SG REIT Strategy
- **Tickers:** EWS (simple), AJBU.SI, ME8U.SI
- **Frequency:** Quarterly (4x per year)
- **Expected:** 75%+ win rate, 2.5% per quarter

---

## Files

- `results/ah_premium_backtest.csv` - Detailed pair results
- `results/sg_reit_dividend_backtest.csv` - REIT results
- `ah_premium_backtest.py` - Backtest script
- `sg_reit_dividend_backtest.py` - Backtest script

---

**2 of 5 hypotheses validated with strong results. 3 require additional data subscriptions.**
