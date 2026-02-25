# Data Request Summary for JT Trading Platform

**Date:** 2026-02-20  
**From:** Trade Algo Researcher  
**To:** JT Trading Agent  
**Priority:** Mixed (High/Medium/Low)

---

## 🎯 EXECUTIVE SUMMARY

**Total Requests:** 5  
**Blocking:** 7 hypotheses (20% of testing queue)  
**Free Options:** 3 requests can be fulfilled at no cost  
**Budget Required:** 2 requests need subscription approval

---

## 📋 DATA REQUESTS

### 1. 🔴 HIGH PRIORITY

#### Request: Accruals Quality Data
**Hypothesis:** Accruals Quality + RSI (Sloan 1996)  
**Status:** BLOCKING 1 hypothesis (Tier 1 priority)  
**Cost:** FREE (multiple free sources available)

**Data Needed:**
- Table: `gold.fundamental_metrics` (new table)
- Columns: `ticker`, `date`, `net_income`, `operating_cash_flow`, `total_assets`, `accruals_ratio`
- Period: 2020-01-01 to 2024-12-31  
- Frequency: Quarterly  
- Universe: S&P 500, Russell 1000

**Sources (Free):**
1. **Financial Modeling Prep (FMP)** - Free tier available
   - Endpoints: /cash-flow-statement, /income-statement
   - Calculation: `(NI - OCF) / Assets`

2. **Calculate from existing data**
   - If Compustat or Bloomberg available
   - Formula: `(Net Income - Operating Cash Flow) / Total Assets`

3. **Yahoo Finance** (fallback)
   - `yfinance` Python library
   - Free but lower quality

**Why Needed:**
Sloan (1996) showed high accrual firms have lower future returns. Combining with RSI improves signal quality. Currently blocked because gold schema only has Feb 2026 data.

**Impact:**
- Unblocks Tier 1 hypothesis
- Expected Sharpe: 1.35
- Can enhance existing RSI strategy (currently 0.98 Sharpe, could push to 1.2+)

**Acceptance Criteria:**
- [ ] 5+ years of quarterly data
- [ ] 95%+ coverage of S&P 500
- [ ] No look-ahead bias (accruals at t, returns from t+1)

---

### 2. 🟡 MEDIUM PRIORITY

#### Request A: ETF Historical Data
**Hypotheses:** 
- Sector Rotation Tech/Utilities
- Sector Momentum
- Market Regime Detection

**Status:** BLOCKING 3 hypotheses  
**Cost:** FREE (Yahoo Finance or other free sources)

**Data Needed:**
- Table: `silver.etf_prices` (new table) or add to existing
- Tickers: XLK, XLU, XLF, XLE, XLI, XLP, XLB, XRT, SPY, QQQ, IWM, VTI
- Columns: `date`, `ticker`, `open`, `high`, `low`, `close`, `volume`
- Period: 2018-01-01 to 2024-12-31  
- Frequency: Daily

**Sources:**
1. **Yahoo Finance** (yfinance)
   - Free, reliable for ETFs
   - 20+ years history

2. **FRED** (Federal Reserve)
   - Some sector indices available
   - Free

**Why Needed:**
Sector rotation strategies require sector ETF data. Current silver schema has individual stocks but no sector ETFs.

**Impact:**
- Unblocks 3 hypotheses
- Enables sector rotation strategies
- Sharpe targets: 0.8-1.2 range

---

#### Request B: Hourly FX Data
**Hypothesis:** Asian Session Liquidity Fade  
**Status:** BLOCKING 1 hypothesis  
**Cost:** FREE

**Data Needed:**
- Table: `gold.fx_hourly` (new table)
- Pairs: USDJPY, EURUSD, GBPUSD, USDCNH, AUDUSD, EURJPY, AUDJPY
- Columns: `timestamp`, `pair`, `bid`, `ask`, `volume`
- Period: 2020-01-01 to 2024-12-31  
- Frequency: Hourly (Tokyo 00:00-08:00 UTC, London 08:00-16:00, NY 13:00-21:00)

**Sources (Free):**
1. **TrueFX** (Recommended)
   - Free tick data
   - Convert to hourly
   - 10+ years history

2. **IBKR Historical Data**
   - Free for account holders
   - Good quality

3. **Dukascopy**
   - Free forex data
   - Download limits apply

**Why Needed:**
Previous test with daily overnight gap proxy **FAILED** (35.5% win rate). Daily data cannot capture Asian Session dynamics. Must have hourly to test this hypothesis properly.

**Impact:**
- Unblocks 1 hypothesis
- Target Sharpe: 1.0-1.3
- Tests FX microstructure alpha

**Note:** Previous proxy test rejected per policy - no compromises.

---

#### Request C: Crypto Funding Rates
**Hypothesis:** Crypto Funding Rate Arbitrage  
**Status:** BLOCKING 1 hypothesis  
**Cost:** FREE (API key needed)

**Data Needed:**
- Table: `gold.crypto_funding` (new table)
- Exchanges: Binance, Bybit, OKX
- Symbols: BTCUSDT, ETHUSDT, major altcoins
- Columns: `timestamp`, `exchange`, `symbol`, `funding_rate`, `mark_price`, `index_price`
- Period: 2020-01-01 to 2024-12-31  
- Frequency: 8-hour (00:00, 08:00, 16:00 UTC)

**Sources:**
1. **Binance API** (Recommended)
   - Endpoint: GET /fapi/v1/fundingRate
   - Cost: FREE
   - History: 2+ years
   - Need: API key

2. **Bybit API**
   - Endpoint: GET /v2/public/funding-rate
   - Cost: FREE

**Why Needed:**
Previous test with 3-day price move proxy **FAILED** (50% win rate). Price moves do NOT capture funding rate pressure. Must have actual funding rates.

**Impact:**
- Unblocks 1 hypothesis  
- Target Sharpe: 1.5-2.5
- Yield strategy component

**Action Required:**
- Register Binance API key
- Configure in JT platform
- Backfill historical funding rates

---

### 3. 🟢 LOW PRIORITY (Budget Required)

#### Request: Options Chain Data
**Hypotheses:**
- Volatility Risk Premium (VRP)
- Options Gamma Gravity
- Post-Earnings Vol Crush

**Status:** BLOCKING 3 hypotheses  
**Cost:** $2,400 - $24,000/year

**Data Needed:**
- Table: `gold.options_chain` (new table)
- Universe: SPY, QQQ, IWM, AAPL, TSLA, high-volume stocks
- Columns: `date`, `ticker`, `expiration`, `strike`, `option_type`, `bid`, `ask`, `volume`, `open_interest`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`
- Period: 2020-01-01 to 2024-12-31  
- Frequency: End-of-day

**Sources:**
1. **Polygon.io** (Recommended to start)
   - Cost: $200-500/month ($2,400-6,000/year)
   - Quality: Good for research
   - History: 3+ years

2. **ORATS** (Best quality)
   - Cost: $300-1,000/month ($3,600-12,000/year)
   - Quality: Excellent, backtest-ready
   - History: 10+ years

3. **Cboe DataShop**
   - Cost: $500-2,000/month ($6,000-24,000/year)
   - Quality: Gold standard
   - History: 10+ years

**Why Needed:**
3 hypotheses require options data. No acceptable proxy exists. VRP requires IV vs realized vol. Gamma requires OI and Greeks by strike.

**ROI Analysis:**
- Cost: $2,400-24,000/year
- Benefit: Validate 3 hypotheses
- Combined target Sharpe: 1.2-1.5 average
- **Recommendation:** Start with Polygon.io ($200-500/month). Upgrade if strategies prove viable.

**Budget Approval Required:** Yes

---

#### Request: ESG Ratings History
**Hypothesis:** ESG Improvers  
**Status:** BLOCKING 1 hypothesis  
**Cost:** $12,000 - $60,000/year

**Data Needed:**
- Table: `gold.esg_ratings` (new table)
- Provider: MSCI or Sustainalytics
- Columns: `ticker`, `date`, `esg_score`, `environment_score`, `social_score`, `governance_score`, `rating_change`
- Period: 2018-01-01 to 2024-12-31  
- Frequency: Monthly/Quarterly

**Sources:**
1. **MSCI ESG Direct** - $3,000-5,000/month
2. **Sustainalytics (Morningstar)** - $1,000-3,000/month
3. **Refinitiv ESG** - $1,500-4,000/month

**Why Needed:**
2024 academic research shows ESG *levels* don't predict returns, but ESG *upgrades* do. Need historical rating changes to validate.

**ROI Analysis:**
- Cost: $12-60K/year
- Benefit: Validate 1 hypothesis
- Target Sharpe: 0.90
- **Recommendation:** Defer until higher-Sharpe hypotheses validated. Cost/benefit unfavorable.

**Budget Approval Required:** Yes

---

## 📊 SUMMARY TABLE

| Priority | Request | Cost | Hypotheses | Block Time |
|----------|---------|------|------------|------------|
| 🔴 High | Accruals Quality | **FREE** | 1 | 1 day |
| 🟡 Medium | ETF Data | **FREE** | 3 | 1 day |
| 🟡 Medium | Hourly FX | **FREE** | 1 | 2-3 days |
| 🟡 Medium | Crypto Funding | **FREE** | 1 | 1 day |
| 🟢 Low | Options Data | $2.4-24K/year | 3 | Pending budget |
| 🟢 Low | ESG Ratings | $12-60K/year | 1 | Pending budget |

---

## ✅ IMMEDIATE ACTIONS (FREE)

### Can Implement Today:
1. **Set up Binance API key**
   - Register at binance.com
   - Create API key with read-only permissions
   - Provide to Trade Algo Researcher

2. **Download TrueFX data**
   - Website: truefx.com
   - Download USDJPY, EURUSD hourly 2020-2024
   - Import to gold.fx_hourly

3. **Register FMP account**
   - Website: financialmodelingprep.com
   - Free tier: 250 API calls/day
   - Query income statement + cash flow for S&P 500

4. **Pull ETF data via yfinance**
   - Python: `yfinance.download(['XLK', 'XLU', 'SPY'], start='2018-01-01')`
   - Import to silver.etf_prices

---

## 💰 BUDGET REQUESTS

### If Budget Available:

**Option A: Minimal ($200-500/month)**
- Polygon.io for options data
- Test VRP, Gamma, Vol Crush
- 3 months trial, evaluate ROI

**Option B: Moderate ($500-1,000/month)**
- Polygon.io + Sustainalytics ESG
- Test options + ESG hypotheses
- 6 months commitment

**Option C: Full ($1,000-2,000/month)**
- ORATS (options) + MSCI ESG
- Best quality data
- 12 months commitment

---

## 🎯 RECOMMENDED PRIORITY ORDER

### Week 1 (Immediate - FREE):
1. ✅ Accruals Quality data (FMP/yfinance)
2. ✅ ETF data (yfinance)
3. ✅ Crypto funding (Binance API key)
4. ✅ Hourly FX (TrueFX download)

### Week 2-4 (If Free Successful):
5. ⏳ Options data trial (Polygon.io)
6. ⏳ Evaluate ESG ROI

---

## 📧 NEXT STEPS

**For JT Trading Agent:**

1. Review this request
2. Confirm which FREE sources to use
3. Set up data pipelines
4. Backfill historical data
5. Notify Trade Algo Researcher when complete

**For Jacky (Budget):**

1. Review paid data options (Options, ESG)
2. Approve/reject budget requests
3. Prioritize based on Sharpe targets

---

**Contact:** Trade Algo Researcher  
**Files:** data_requests/REQUEST_001-005.md  
**Policy:** NO COMPROMISE - All blocked hypotheses await fulfillment
