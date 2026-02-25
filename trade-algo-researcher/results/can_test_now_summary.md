# "Can Test Now" Hypotheses - Backtest Results

**Date:** 2026-02-19  
**Tested:** 3 hypotheses with free data proxies  
**Status:** Complete

---

## Summary

| Hypothesis | Proxy Used | Result | Real Data Needed |
|------------|-----------|--------|------------------|
| **Asian Session Liquidity Fade** | Overnight gaps | ❌ FAILED | ✅ Intraday FX data |
| **Crypto Funding Rate** | 3-day moves | ❌ FAILED | ✅ Exchange funding rates |
| **VIX Term Structure** | Not tested | ⏳ PENDING | ✅ VIX futures prices |

**Finding:** Simplified proxies don't capture the true edge. Real data required.

---

## 1. Asian Session Liquidity Fade ❌

**Proxy:** Used overnight gaps instead of Asian session hourly data

### Results

| FX Pair | Win Rate | Sharpe | Status |
|---------|----------|--------|--------|
| USD/JPY | 24.6% | 1.04 | ❌ Failed |
| EUR/USD | 21.3% | -0.20 | ❌ Failed |
| GBP/USD | 46.8% | 0.40 | ❌ Failed |
| AUD/USD | 26.5% | 0.55 | ❌ Failed |

**Problem:** Daily overnight gaps don't capture Asian session dynamics
**Solution:** Need hourly FX data (TrueFX, Dukascopy, or IBKR)

---

## 2. Crypto Funding Rate ❌

**Proxy:** Used 3-day price moves instead of actual funding rates

### Results

| Crypto | Win Rate | Sharpe | Status |
|--------|----------|--------|--------|
| Bitcoin | 47.9% | -0.47 | ❌ Failed |
| Ethereum | 49.1% | -0.45 | ❌ Failed |
| Solana | 49.6% | -0.63 | ❌ Failed |
| All others | 50-52% | ~0 | ❌ Failed |

**Problem:** Price momentum ≠ funding rate pressure
**Solution:** Need actual funding rate data from Binance/Bybit APIs

---

## 3. VIX Term Structure ⏳

**Status:** Not tested (no VIX futures on yfinance)

**Requirement:** VIX futures prices (M1, M2, M3)
**Source:** CBOE (free delayed), IBKR (real-time), Quandl
**Difficulty:** Easy to get, just not via yfinance

---

## What Actually Works (From Prior Testing)

The strategies that validated with real data:

| Strategy | Data Used | Win Rate | Sharpe |
|----------|-----------|----------|--------|
| **AH Premium Arbitrage** | Dual-listed prices (yfinance) | 72% | 2.33 |
| **SG REIT Dividend** | Daily prices (yfinance) | 73% | 0.73 |
| **RSI Mean Reversion** | OHLC (yfinance) | 60% | 1.2 |
| **Gap Fade (HK)** | OHLC (yfinance) | 62% | 3.45 |

---

## Revised "Can Test Now" List

### ✅ Actually Testable (Worked)

1. **AH Premium Arbitrage** ✅ VALIDATED
   - Data: Dual-listed H-shares + A-shares (yfinance)
   - Status: 72% win, deploy immediately

2. **SG REIT Dividend Capture** ✅ VALIDATED
   - Data: Daily REIT prices (yfinance)
   - Status: 73% win, deploy quarterly

3. **Technical Indicators on Asian Stocks** ✅ PARTIALLY VALIDATED
   - RSI, 3-Day Reversal, Momentum on HK/CN/SG stocks
   - Already tested, results in strategy_region_definitions

### ❌ Not Testable Without Real Data

4. **Asian Session FX** 
   - Needs: Hourly FX data (TrueFX, IBKR)
   - Cost: Free (TrueFX), or IBKR subscription

5. **Crypto Funding Rate**
   - Needs: Binance/Bybit API for funding rates
   - Cost: Free (API access)

6. **VIX Term Structure**
   - Needs: VIX futures prices (CBOE, Quandl)
   - Cost: Free (delayed), $ (real-time)

7. **Options Gamma Gravity**
   - Needs: Options chain + OI data
   - Cost: $50-150/mo (Polygon, Cboe)

8. **Post-Earnings Vol Crush**
   - Needs: Options prices + earnings calendar
   - Cost: $ (earnings data)

9. **Commodity Crack Spread**
   - Needs: CL, RB, HO futures
   - Cost: Free (yfinance has ETFs), real futures need IBKR

10. **ETF Premium/Discount**
    - Needs: Real-time NAV + ETF prices
    - Cost: Free (ETF websites), but needs scraping

---

## Recommendation

**Immediate Deployment (Free Data):**
1. AH Premium Arbitrage (ICBC, CCB, Bank of China)
2. SG REIT Dividend (EWS quarterly)
3. RSI Mean Reversion (all 4 markets)

**Next Priority (Easy Data):**
1. VIX Term Structure - Get CBOE data (free delayed)
2. Crypto Funding - Set up Binance API (free)

**Lower Priority (Paid Data):**
1. Options strategies - Need Polygon subscription
2. Asian FX - Need TrueFX or IBKR

---

## Files

- results/asian_session_fade_backtest.csv
- results/crypto_funding_proxy_backtest.csv
- strategies/asian_session_fade_backtest.py
- strategies/crypto_funding_proxy_backtest.py

---

**Bottom Line: Only 2-3 strategies truly "testable now" with free data. The rest need specific data sources.**
