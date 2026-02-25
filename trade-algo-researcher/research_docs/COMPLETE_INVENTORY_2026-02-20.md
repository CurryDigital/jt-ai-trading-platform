# Complete Strategy & Hypothesis Inventory

**Date:** 2026-02-20  
**Total Strategies:** 22  
**Total Hypotheses:** 100  
**Verified by Jacky:** 22/22 ✅

---

## 📊 EXECUTIVE SUMMARY

| Category | Count | Status |
|----------|-------|--------|
| **Golden Strategies** | 5 | Production-ready |
| **Strategy-Region Combos** | 17 | Validated across 4 markets |
| **Total Deployable** | **22** | Ready for JT platform |
| **Active Hypotheses** | 35 | In testing phase |
| **Idea Stage** | 48 | Awaiting research |
| **Validated (Real Data)** | 4 | Proven with backtests |
| **Validated (Synthetic)** | 1 | PEAD (needs real data) |
| **Promoted to Golden** | 1 | Gold/Silver |
| **Rejected** | 10 | Failed validation ❌ |

**Total Hypotheses:** 100 (48 idea + 35 testing + 6 validated + 1 promoted + 10 rejected)

---

## 🏆 LAYER 1: GOLDEN STRATEGIES (5)

**Location:** `/strategies/[asset_class]/[strategy_name]/strategy.yaml`  
**Status:** Production-ready, backtested → paper → live

| # | Strategy | Asset Class | Direction | Sharpe | Win Rate | Status |
|---|----------|-------------|-----------|--------|----------|--------|
| 1 | **ARASO Factor Model** | Equities | Neutral | 2.7 | 67% | Enhanced v2.0 |
| 2 | **Information Arbitrage (Secondary/Tertiary)** | Equities | Short | 1.8 | 58% | Active |
| 3 | **FX Carry Momentum** | FX | Long | 1.2 | 55% | Backtested |
| 4 | **Crypto Funding Rate Arbitrage** | Crypto | Neutral | 2.5 | 75% | Backtested |
| 5 | **Gold/Silver Ratio** | Commodities | Neutral | 1.11 | 65.2% | **Promoted** |

**Total Golden:** 5 strategies

---

## 🌍 LAYER 1B: STRATEGY-REGION COMBINATIONS (17)

**Format:** `{Strategy}_{Region}` with specific ticker universes  
**Total Tickers:** 261 deployable across 4 markets

### RSI Mean Reversion (Universal - All 4 Markets)
| Strategy | Region | Universe | Win Rate | Sharpe | Classification |
|----------|--------|----------|----------|--------|----------------|
| RSI_MeanReversion_US | US | 32 tickers | 65% | 1.2 | Universal |
| RSI_MeanReversion_HK | HK | 20 tickers | 68% | 1.25 | Universal |
| RSI_MeanReversion_CN | CN | 14 tickers | 70% | 1.35 | Universal |
| RSI_MeanReversion_SG | SG | 11 tickers | 65% | 1.1 | Universal |

### 3-Day Reversal (Multi-Market)
| Strategy | Region | Universe | Win Rate | Sharpe | Classification |
|----------|--------|----------|----------|--------|----------------|
| 3Day_Reversal_US | US | 33 tickers | 58% | 1.15 | Multi-market |
| 3Day_Reversal_HK | HK | 21 tickers | 61% | 1.28 | Multi-market |
| 3Day_Reversal_CN | CN | 14 tickers | 59% | 1.18 | Multi-market |
| 3Day_Reversal_SG | SG | 8 tickers | 57% | 1.05 | Multi-market |

### 20-Day Momentum (Multi-Market)
| Strategy | Region | Universe | Win Rate | Sharpe | Classification |
|----------|--------|----------|----------|--------|----------------|
| Momentum_20Day_US | US | 42 tickers | 61% | 1.4 | Multi-market |
| Momentum_20Day_HK | HK | 8 tickers | 60% | 1.35 | Multi-market |
| Momentum_20Day_SG | SG | 7 tickers | 59% | 1.28 | Multi-market |

### MACD Divergence (Asia-Focused)
| Strategy | Region | Universe | Win Rate | Sharpe | Classification |
|----------|--------|----------|----------|--------|----------------|
| MACD_Divergence_HK | HK | 16 tickers | 58% | 1.2 | Asia-focused |
| MACD_Divergence_CN | CN | 6 tickers | 56% | 1.05 | Asia-focused |
| MACD_Divergence_SG | SG | 2 tickers | 59% | 1.05 | Asia-focused |

### Gap Fade (Market-Specific)
| Strategy | Region | Universe | Win Rate | Sharpe | Classification |
|----------|--------|----------|----------|--------|----------------|
| **Gap_Fade_HK** ⚡ | HK | 24 tickers | 62% | **3.45** | HK-focused |
| Gap_Fade_US | US | 2 tickers | 57% | 1.05 | Limited |
| Gap_Fade_SG | SG | 1 ticker | 58% | 1.05 | Limited |

**Total Strategy-Region Combos:** 17

---

## 🔬 LAYER 2: ACTIVE HYPOTHESES IN TESTING (35)

### Newly Moved to Testing (13) - From Academic Research

#### From Recent Papers (2020-2026)
| # | Hypothesis | Academic Source | Asset | Target Sharpe | Target Win% |
|---|------------|-----------------|-------|---------------|-------------|
| 1 | ESG Improvers | Berkeley Haas (2024) | Equities | 0.9 | 58% |
| 2 | Retail Order Flow | Barber/Odean (2023) | Equities | 1.25 | 60% |
| 3 | Supply Chain Reshoring | Baldwin/IMF (2022-23) | Equities | 1.05 | 62% |
| 4 | Inflation Regime Switch | Reis/Blanchard (2022-23) | Multi-asset | 1.15 | 70% |
| 5 | LLM NLP Sentiment | Lopez-Lira (2023) | Equities | 1.2 | 62% |

#### From Famous Papers (1993-2018)
| # | Hypothesis | Academic Source | Asset | Target Sharpe | Target Win% |
|---|------------|-----------------|-------|---------------|-------------|
| 6 | Momentum Lifecycle | Jegadeesh/Titman (1993) + Hong/Stein (1999) | Equities | 1.25 | 62% |
| 7 | **Accruals Quality + RSI** | Sloan (1996) | Equities | **1.35** | **64%** |
| 8 | Time-Series Momentum | Hurst/Ooi/Pedersen (2017) | Multi-asset | 1.15 | 58% |
| 9 | Volatility Risk Premium | Coval/Shumway (2001) | Options/Equities | 1.25 | 62% |
| 10 | Quality Value QARP | Asness (2018) | Equities | 1.25 | 62% |
| 11 | **CMV Multi-Factor** | Asness (2013) + Koijen (2018) | Multi-asset | **1.35** | **62%** |
| 12 | Limits to Arbitrage | Shleifer/Vishny (1997) | Equities | 1.15 | 62% |
| 13 | **PEAD NLP Enhanced** | Ball/Brown (1968) + Lopez-Lira (2023) | Equities | **1.45** | **67%** |

**Subtotal New:** 13 hypotheses

### Existing Testing Hypotheses (22)

| # | Hypothesis | Status | Asset | Target Sharpe |
|---|------------|--------|-------|---------------|
| 14 | Job Postings Lead Time | testing | Equities | TBD |
| 15 | Lead-Lag Sector Timing | testing | Equities | +0.3 to ARASO |
| 16 | Peer Firm Lag (Oil) | testing | Equities | 1.2-1.8 |
| 17 | ADR-Local Arbitrage | testing | Equities | 1.5-2.5 |
| 18 | FX Central Bank NLP | testing | FX | 1.2-1.8 |
| 19 | Crypto Miner Capitulation | testing | Crypto | 1.5-2.5 |
| 20 | Credit-Equity Lag | testing | Multi-asset | 1.0-1.5 |
| 21 | Volume Profile Value Area | testing | Equities | 1.1-1.5 |
| 22 | Doji at Support/Resistance | testing | Equities | 0.7-0.9 |
| 23 | Trump Policy Momentum | testing | Equities | 1.2-1.6 |
| 24 | Elon Musk Twitter Alpha | testing | Equities | 0.6-1.0 |
| 25 | Fed Speech NLP | testing | Equities | 1.0-1.4 |
| 26 | Earnings Options Flow | testing | Options | 1.2-1.6 |
| 27 | Geopolitical Risk Premium | testing | Multi-asset | 1.0-1.5 |
| 28 | Analyst Rating Momentum | testing | Equities | 0.9-1.2 |
| 29 | Dividend Aristocrat Momentum | testing | Equities | 0.8-0.9 |
| 30 | NAV Discount Reversion | testing | REITs/CEFs | 0.9-1.1 |
| 31 | Cash-Rich Growth | testing | Equities | 0.8-1.0 |
| 32 | EPS Growth Persistence | testing | Equities | 0.9-1.1 |
| 33 | Northbound Flow | testing | HK/China | 0.9-1.2 |
| 34 | China Policy Drift | testing | China | 1.2-1.8 |
| 35 | HK Property NAV | testing | HK | 0.8-1.0 |

**Total Testing:** 35 hypotheses

---

## 💡 LAYER 2: HYPOTHESES IN IDEA STAGE (48)

### Options Strategies
| # | Hypothesis | Target Sharpe |
|---|------------|---------------|
| 36 | VIX Term Structure | 0.8-1.2 |
| 37 | Options Gamma Gravity | 1.2-1.6 |
| 38 | Post-Earnings Vol Crush | 1.2-1.6 |

### Asian Market
| # | Hypothesis | Target Sharpe |
|---|------------|---------------|
| 39 | Asian Session FX | 1.0-1.3 |
| 40 | ETF Creation/Redemption | 1.3-1.8 |
| 41 | Commodity Crack Spread | 0.7-1.0 |

### Remaining (45)
Various hypotheses covering:
- ESG themes (3)
- Crypto themes (4)
- Alternative data (6)
- Technical patterns (8)
- Fundamental factors (12)
- Macro/Market timing (12)

**Total Idea Stage:** 48 hypotheses

---

## ✅ VALIDATED HYPOTHESES (4 Real Data + 1 Synthetic)

| # | Hypothesis | Sharpe | Win Rate | Status |
|---|------------|--------|----------|--------|
| V1 | Macro Scaling > Stops | N/A | N/A | Ready for promotion |
| V2 | PEAD Earnings Drift | 2.43 | TBD | Synthetic only |
| V3 | Sector Rotation Tech/Util | 0.83 | 66% | Validated |
| V4 | RSI Mean Reversion | 1.42 | 60% | Validated |
| V5 | Bollinger Squeeze | 3.64 | 67% | Validated |
| V6 | Engulfing Pattern | 3.90 | 80% | Validated |

**Total Validated:** 6 (4 real, 1 synthetic, 1 ready)

---

## 🚀 DEPLOYED STRATEGIES

| # | Strategy | Sharpe | Win Rate | Status |
|---|----------|--------|----------|--------|
| D1 | AH Premium Arbitrage | 2.33 | 72% | Live |
| D2 | SG REIT Dividend | 0.73 | 73% | Live |
| D3 | RSI Mean Reversion (4 markets) | 1.2-1.35 | 60-63% | Deployed |

**Total Deployed:** 3 strategies

---

## ❌ REJECTED HYPOTHESES (10)

**Status:** Failed validation after testing  
**Documentation:** Full rejection reasons in database  
**Lesson:** Fail fast, document learnings

| # | Hypothesis | Actual Sharpe | Win% | Rejection Reason | Date |
|---|------------|---------------|------|------------------|------|
| R1 | MACD_Divergence | 0.65 | 46% | Win rate below 50% threshold | 2026-02 |
| R2 | 3-Day_Reversal_Generic | 0.72 | 48% | Not viable as universal (only HK works) | 2026-02 |
| R3 | Gap_Fade_Universal | 0.68 | 47% | Universal failed, only HK viable | 2026-02 |
| R4 | Peer_Firm_Lag_Simple | 0.45 | 52% | Zero lag found (0.7-0.8 correlation, no predictive lag) | 2026-02 |
| R5 | VIX_Contango_VXX | N/A | N/A | VXX delisted 2024, no alternative | 2026-02 |
| R6 | Asian_Session_FX_Daily_Proxy | 0.35 | 35.5% | Daily proxy failed, needs hourly FX data | 2026-02 |
| R7 | Crypto_Funding_Rate_Proxy | 0.60 | 50% | 3-day move proxy failed, needs real funding data | 2026-02 |
| R8 | Random_Walk_Breakout | 0.42 | 48.5% | No edge, indistinguishable from random | 2026-01 |
| R9 | Social_Media_Sentiment_Levels | 0.55 | 51% | Levels not predictive (momentum of sentiment works) | 2026-01 |
| R10 | IPO_First_Day_Momentum | N/A | N/A | Data unavailable, execution impossible at scale | 2026-01 |

**Common Rejection Reasons:**
- **Low Win Rate** (40%): Strategy underperforms random
- **Proxy Inadequate** (20%): Simplified data doesn't capture edge
- **Data Unavailable** (20%): Cannot obtain required data
- **No Edge Found** (10%): Academic paper doesn't replicate
- **Practical Constraints** (10%): Cannot execute at scale

**Key Insight:** Target Sharpe (avg 1.23) vs Actual (avg 0.54) = 56% overestimation

**SQL Access:** `SELECT * FROM openclaw_researcher.v_rejected_hypotheses;`

---

## 📈 ACADEMIC SOURCE BREAKDOWN

| Source Type | Count | Examples |
|-------------|-------|----------|
| **Classic (1990s-2000s)** | 8 | Jegadeesh/Titman, Fama/French, Sloan, Shleifer/Vishny |
| **Modern (2010s)** | 12 | Asness (Value/Momentum/Quality), Hurst/Ooi/Pedersen |
| **Recent (2020-2026)** | 13 | Lopez-Lira (LLM), Berkeley Haas (ESG), KAMA (2025) |

---

## 🎯 ASSET CLASS DISTRIBUTION

| Asset Class | Strategy Count | Hypothesis Count |
|-------------|----------------|------------------|
| **Equities** | 15 | 62 |
| **FX** | 2 | 10 |
| **Commodities** | 2 | 12 |
| **Crypto** | 2 | 10 |
| **Multi-asset** | 1 | 6 |

---

## 📋 COMPLETE LIST: 22 VERIFIED STRATEGIES

| Rank | Strategy | Sharpe | Win% | Buy Signal | Sell Signal |
|------|----------|--------|------|------------|-------------|
| 1 | Gap Fade (HK) ⚡ | 3.45 | 62% | Gap >0.5% | Intraday exit |
| 2 | Crypto Funding | 2.5 | 75% | Funding >0.01% | Funding negative |
| 3 | ARASO Factor | 2.7 | 67% | Mean rev >70%+BB | Price > mid BB |
| 4 | AH Premium | 2.33 | 72% | Premium >30% | Premium <15% |
| 5 | Info Arb | 1.8 | 58% | Peer drops >10% | Recover 50% |
| 6 | Momentum (US) | 1.4 | 61% | 20-day ret >5% | Momentum <0 |
| 7 | Momentum (HK) | 1.35 | 60% | 20-day ret >5% | Momentum <0 |
| 8 | RSI (CN) | 1.35 | 63% | RSI <30 | RSI >50 |
| 9 | Momentum (SG) | 1.28 | 59% | 20-day ret >5% | Momentum <0 |
| 10 | 3-Day Rev (HK) | 1.28 | 61% | 3 down days +5% | Price > entry |
| 11 | RSI (HK) | 1.25 | 61% | RSI <30 | RSI >50 |
| 12 | RSI (Universal) | 1.2 | 61% | RSI <30 | RSI >50 |
| 13 | RSI (US) | 1.2 | 60% | RSI <30 | RSI >50 |
| 14 | FX Carry | 1.2 | 55% | Rate diff >3% | Diff <1% |
| 15 | MACD (HK) | 1.2 | 58% | MACD divergence | MACD cross zero |
| 16 | 3-Day Rev (CN) | 1.18 | 59% | 3 down days +5% | Price > entry |
| 17 | 3-Day Rev (US) | 1.15 | 58% | 3 down days +5% | Price > entry |
| 18 | Gold/Silver | 1.11 | 65% | Z-score >±1.5 | Z-score reverts |
| 19 | RSI (SG) | 1.1 | 58% | RSI <30 | RSI >50 |
| 20 | MACD (CN) | 1.05 | 56% | MACD divergence | MACD cross zero |
| 21 | 3-Day Rev (SG) | 1.05 | 57% | 3 down days +5% | Price > entry |
| 22 | SG REIT Dividend | 0.73 | 73% | Jan/Apr/Jul/Oct | Ex-div or 30 days |

**Verified by Jacky:** 2026-02-19 ✅

---

*Inventory last updated: 2026-02-20*
