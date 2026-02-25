# BATCH 15: New Hypotheses for Testing
## Research Pipeline — Continuous Testing Until 18:00 HKT

**Start Time:** 2026-02-25 08:00 UTC  
**Target End:** 2026-02-25 10:00 UTC (18:00 HKT)  
**Status:** ACTIVE

---

## HYPOTHESIS QUEUE

### H015-001: Earnings Volatility Crush
**Status:** Ready to test  
**Logic:** Sell straddle/iron condor 1 day before earnings, buy back next day  
**Expected:** IV collapse after earnings = profit from volatility contraction  
**Universe:** US stocks with high options volume (AAPL, TSLA, NVDA, etc.)  
**Data Needed:** Earnings dates, options IV  
**Status:** BLOCKED — Need options data (REQUEST_005 pending)

### H015-002: VIX Contango Roll
**Status:** Ready to test  
**Logic:** Short VIX futures when curve in contango, cover when VIX > 25  
**Expected:** Contango decay provides edge 80%+ of time  
**Universe:** VIX futures, VXX, UVXY  
**Data Needed:** VIX futures curves  
**Status:** READY — Can proxy with VXX price data

### H015-003: Commodity Crack Spread
**Status:** Ready to test  
**Logic:** Long oil refining spread (gasoline - crude - heat) when > historical avg  
**Expected:** Mean reversion in refining margins  
**Universe:** CL=F, RB=F, HO=F  
**Data Needed:** Futures prices  
**Status:** READY — Have CL=F, need RB=F and HO=F

### H015-004: Sector Rotation Momentum
**Status:** Ready to test  
**Logic:** Long outperforming sector ETF, short underperforming, rebalance monthly  
**Expected:** Momentum persists 1-3 months  
**Universe:** XLK, XLF, XLE, XLU, XLI, XLP, XLB, XLY  
**Data Needed:** Sector ETF prices  
**Status:** READY — Test with existing XLK, XLF, XLE, XLU

### H015-005: Bond Yield Curve Steepener/Flattener
**Status:** Ready to test  
**Logic:** Long 2Y/10Y spread when curve too flat, short when too steep  
**Expected:** Mean reversion to historical curve slope  
**Universe:** TLT (20Y), IEF (7Y), SHY (1-3Y)  
**Data Needed:** Treasury yields  
**Status:** PARTIAL — Have TLT, need IEF and SHY

### H015-006: High Short Interest Squeeze
**Status:** Ready to test  
**Logic:** Long stocks with >20% short interest when price breaks 20-day high  
**Expected:** Short covering accelerates breakout  
**Universe:** All US equities  
**Data Needed:** Short interest data  
**Status:** BLOCKED — Need short interest data

### H015-007: Dividend Capture with RSI Filter
**Status:** Ready to test  
**Logic:** Buy 2 days before ex-dividend if RSI < 50, sell on ex-date  
**Expected:** Dividend + mean reversion alpha  
**Universe:** High dividend yield stocks (XLE, XLU, REITs)  
**Data Needed:** Dividend calendar  
**Status:** BLOCKED — Need dividend dates

### H015-008: Gold/Silver Ratio Mean Reversion
**Status:** Ready to test  
**Logic:** Long gold/short silver when ratio > 85, reverse when < 65  
**Expected:** Ratio mean reverts to ~70-75  
**Universe:** GC=F (gold), SI=F (silver)  
**Data Needed:** Gold and silver futures  
**Status:** PARTIAL — Have GC=F, need SI=F

### H015-009: Currency Carry with Trend Filter
**Status:** Ready to test  
**Logic:** Long high-yield currencies (AUD, NZD) vs JPY when ADX > 25  
**Expected:** Carry + momentum  
**Universe:** AUDJPY, NZDJPY  
**Data Needed:** FX spot rates  
**Status:** READY — Have AUDJPY=X, can add NZDJPY=X

### H015-010: Insider Buying Momentum
**Status:** Ready to test  
**Logic:** Follow cluster of insider buys (>3 officers, >$100k each)  
**Expected:** Information edge  
**Universe:** US equities  
**Data Needed:** Insider trading filings (Form 4)  
**Status:** BLOCKED — Need insider data

### H015-011: Low Volatility Anomaly
**Status:** Ready to test  
**Logic:** Long lowest volatility quintile, short highest volatility quintile  
**Expected:** Low vol outperforms (Bali et al. 2011)  
**Universe:** S&P 500 constituents  
**Data Needed:** Full S&P 500 universe  
**Status:** PARTIAL — Can test with current universe

### H015-012: Pairs Trading (Cointegration)
**Status:** Ready to test  
**Logic:** Trade mean reversion between cointegrated pairs (KO/PEP, JPM/BAC)  
**Expected:** Spread convergence  
**Universe:** Sector pairs  
**Data Needed:** Full price histories  
**Status:** READY — Test with existing tickers

---

## PRIORITY ORDER (Next 2 Hours)

### IMMEDIATE (Can Test Now):
1. **H015-004** Sector Rotation Momentum — Have XLK, XLF, XLE, XLU
2. **H015-009** Currency Carry Trend — Have AUDJPY=X
3. **H015-011** Low Volatility Anomaly — Can test with existing universe
4. **H015-012** Pairs Trading — Can test with existing tickers

### NEED DATA (File Requests):
5. H015-001 — Options data (REQUEST_005)
6. H015-006 — Short interest data
7. H015-007 — Dividend calendar
8. H015-008 — Silver futures (SI=F)
9. H015-010 — Insider trading data

### PARTIAL DATA (Can Test with Proxies):
10. H015-002 — VIX Contango (proxy with VXX)
11. H015-003 — Crack Spread (have CL=F, need RB=F, HO=F)
12. H015-005 — Yield Curve (have TLT, need IEF, SHY)

---

## TESTING PIPELINE

```
Hour 1 (08:00-09:00 UTC):
├── H015-004 Sector Rotation Momentum
├── H015-009 Currency Carry Trend
└── H015-011 Low Volatility Anomaly

Hour 2 (09:00-10:00 UTC):
├── H015-012 Pairs Trading
├── Document results
└── Update KEY_INSIGHTS
```

---

## DATA REQUESTS TO FILE

**REQUEST_008: Options Data for Earnings Volatility Crush**
- Required for: H015-001
- Data: Options chain with IV, earnings dates
- Source: Polygon.io or similar
- Cost: $$ (budget approval)

**REQUEST_009: Short Interest Data**
- Required for: H015-006
- Data: Short interest % float for US equities
- Source: FINRA, exchange data
- Cost: $ (moderate)

**REQUEST_010: Dividend Calendar**
- Required for: H015-007
- Data: Ex-dividend dates, dividend amounts
- Source: FMP, Nasdaq
- Cost: Free tier available

**REQUEST_011: Additional Futures Data**
- Required for: H015-003, H015-008
- Data: RB=F (RBOB Gasoline), HO=F (Heating Oil), SI=F (Silver)
- Source: Yahoo Finance (free)
- Cost: Free

---

## SUCCESS METRICS (for next 2 hours)

Target: Test 4 hypotheses, find 1-2 VALIDATED strategies

| Metric | Target |
|--------|--------|
| Hypotheses tested | 4 |
| Strategies validated | 1-2 |
| Strategies rejected | 2-3 |
| New insights documented | 2-3 |
| Files created | 4+ |

---

## WORKING NOTES

**Start:** 08:00 UTC  
**Current:** -  
**End Target:** 10:00 UTC (18:00 HKT)

---

*Continuous testing in progress...*
