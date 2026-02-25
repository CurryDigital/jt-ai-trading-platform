# Research Initiative: New Strategy Development (Q1 2026)

**Date:** 2026-02-17  
**Objective:** Research and develop new trading strategies across asset classes  
**Target:** 2-3 new validated strategies for JT platform  

---

## Research Framework

Following Three-Layer Architecture:
1. **NEWS** → Market intelligence, academic papers, data sources
2. **HYPOTHESES** → Testable ideas with validation criteria
3. **STRATEGIES** → Backtested, production-ready with strategy.yaml

---

## Current Portfolio Gap Analysis

| Asset Class | Direction | Horizon | Current | Gap |
|-------------|-----------|---------|---------|-----|
| Equities | Long | Short-term | ❌ | **NEEDED** |
| Equities | Long | Long-term | ❌ | **NEEDED** |
| Equities | Short | Short-term | ✅ ARASO, Info Arb | — |
| Equities | Short | Long-term | ❌ | Opportunity |
| FX | Long | Short-term | ✅ Carry Mom | — |
| FX | Long | Long-term | ❌ | **NEEDED** |
| FX | Short | Short-term | ❌ | Opportunity |
| Crypto | Long | Short-term | ✅ Funding Arb | — |
| Crypto | Long | Long-term | ❌ | **NEEDED** |
| Crypto | Short | Any | ❌ | **NEEDED** |
| Commodities | Any | Any | ❌ | **NEEDED** |
| Cross-Asset | Any | Any | ❌ | **NEEDED** |

**Priority Gaps:**
1. Long-only equity momentum (short-term)
2. Long-term trend following (any asset)
3. Commodity carry/seasonality
4. Crypto long-term (halving cycle)
5. Cross-asset risk parity

---

## Research Targets by Trading Type

### 1. Momentum Strategies
**What:** Price momentum, earnings momentum, news momentum  
**Gap:** No long-only momentum in portfolio  
**Research Questions:**
- Does 12-1 month momentum still work post-2020?
- Can we improve with earnings acceleration overlay?
- What about intraday momentum (hourly)?

### 2. Mean Reversion
**What:** Statistical arbitrage, pairs trading, Bollinger bands  
**Gap:** ARASO covers this, but limited to sector-neutral  
**Research Questions:**
- Cross-asset mean reversion (e.g., gold vs real rates)?
- Volatility-adjusted mean reversion?

### 3. Carry Strategies
**What:** Yield capture, roll yield, funding arbitrage  
**Gap:** Only FX carry exists  
**Research Questions:**
- Commodity carry (contango/backwardation)?
- Crypto staking yield + hedging?
- Dividend carry strategies?

### 4. Event-Driven
**What:** Earnings, M&A, splits, index changes  
**Gap:** None currently  
**Research Questions:**
- Post-earnings announcement drift (PEAD)?
- Index addition/deletion effects?
- Corporate action arbitrage?

### 5. Volatility Strategies
**What:** Vol selling, VIX futures, vol term structure  
**Gap:** None currently  
**Research Questions:**
- Short vol during low VIX regimes?
- Volatility risk premium capture?
- Correlation trading?

### 6. Trend Following
**What:** Time-series momentum, CTA-style  
**Gap:** No long-term trend strategies  
**Research Questions:**
- Multi-asset trend following (pods approach)?
- Trend + carry combination?
- Regime detection for trend vs mean reversion?

### 7. Machine Learning Alpha
**What:** Feature engineering, ensemble models, alternative data  
**Gap:** ARASO uses HMM but limited ML  
**Research Questions:**
- Can job posting data improve DVS?
- Satellite data for retail/commodities?
- NLP on earnings call sentiment?

---

## Initial Hypothesis Candidates

### H1: Post-Earnings Announcement Drift (PEAD)
**Asset:** Equities  
**Direction:** Long/Neutral  
**Horizon:** Short-term (1-5 days)  
**Idea:** Stocks with positive earnings surprises continue drifting up for 1-5 days post-announcement  
**Expected Sharpe:** 1.5-2.0  
**Status:** idea → needs validation

### H2: Commodity Seasonality
**Asset:** Commodities (energy, ags)  
**Direction:** Long/Short  
**Horizon:** Short-term (weekly)  
**Idea:** Seasonal patterns in natural gas (winter), gasoline (summer), agriculture (planting/harvest)  
**Expected Sharpe:** 1.0-1.5  
**Status:** idea → needs validation

### H3: Crypto Long-Term Trend (Halving Cycle)
**Asset:** Crypto (BTC, ETH)  
**Direction:** Long  
**Horizon:** Long-term (months)  
**Idea:** 4-year halving cycle creates predictable boom-bust; trend-follow with HMM regime detection  
**Expected Sharpe:** 2.0+ (high volatility but strong signal)  
**Status:** idea → needs validation

### H4: Volatility Risk Premium
**Asset:** Equities (via options)  
**Direction:** Short vol (sell options)  
**Horizon:** Short-term (weekly)  
**Idea:** Sell straddles/strangles when VIX < 20; capture volatility risk premium  
**Expected Sharpe:** 1.0-1.3 (with proper risk management)  
**Status:** idea → needs validation

### H5: Cross-Asset Momentum (Risk Parity Style)
**Asset:** Cross-asset (stocks, bonds, FX, commodities)  
**Direction:** Long/Short  
**Horizon:** Long-term (monthly rebal)  
**Idea:** Risk-adjusted momentum across asset classes; weight by inverse volatility  
**Expected Sharpe:** 1.2-1.5  
**Status:** idea → needs validation

### H6: Intraday VWAP Momentum
**Asset:** Equities (liquid large-cap)  
**Direction:** Long/Short  
**Horizon:** Ultra-short (intraday)  
**Idea:** Stocks breaking above/below VWAP with volume continuation  
**Expected Sharpe:** 1.5-2.0 (high turnover)  
**Status:** idea → needs validation

---

## Research Plan

### Week 1-2: Literature Review & Data Collection
- [ ] Review academic papers on PEAD (post-2020)
- [ ] Gather commodity seasonal data
- [ ] Analyze crypto halving cycle returns
- [ ] Study volatility risk premium literature

### Week 3-4: Hypothesis Formation
- [ ] Write 3-4 formal hypothesis documents
- [ ] Define validation criteria for each
- [ ] Set up data pipelines

### Week 5-8: Backtesting
- [ ] Run initial backtests for top 3 hypotheses
- [ ] Parameter optimization
- [ ] Walk-forward validation

### Week 9-12: Strategy Promotion
- [ ] Promote validated hypotheses to strategies
- [ ] Create strategy.yaml files
- [ ] JT platform integration testing

---

## Next Actions

1. **Start with PEAD** — Most established academic phenomenon
2. **Parallel track:** Commodity seasonality (data readily available)
3. **Background:** Crypto halving analysis (longer time horizon)

---

*Research initiative started 2026-02-17*  
*Next update: Weekly progress report*
