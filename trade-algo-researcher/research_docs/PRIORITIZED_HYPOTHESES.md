# Prioritized Hypotheses: YFinance/IBKR Feasible

**Date:** 2026-02-18  
**Criteria:** Can be backtested with yfinance or IBKR data only  
**Priority:** Data availability > Sharpe target > Implementation complexity

---

## TIER 1: Ready to Backtest (YFinance Only)

### 1. Peer Firm Information Lag (Oil)
**Asset:** Equities  
**Data:** yfinance (XOM, CVX, SNP, PTR prices)  
**Status:** Ready  
**Action:** Cross-correlation analysis

### 2. ADR-Local Share Arbitrage
**Asset:** Equities  
**Data:** yfinance (BABA, TSM, JD + local prices)  
**Status:** Ready  
**Action:** Calculate deviation time series

### 3. Time Series Momentum (Trend Following)
**Asset:** Multi-asset  
**Data:** yfinance (SPY, TLT, GLD, USO)  
**Status:** Ready  
**Action:** 12-month momentum backtest

### 4. VIX Contango Roll Yield
**Asset:** Volatility  
**Data:** yfinance (VIX futures via ^VIX, VXX)  
**Status:** Ready  
**Action:** Short VXX when contango >5%

### 5. Precious Metals Ratio Rotation
**Asset:** Commodities  
**Data:** yfinance (GLD, SLV)  
**Status:** Ready  
**Action:** Gold/Silver ratio mean reversion

---

## TIER 2: IBKR Data Required

### 6. FX Carry + Momentum
**Asset:** FX  
**Data:** IBKR forex (AUD/JPY, NZD/JPY, USD/CHF)  
**Status:** Needs IBKR connection  
**Action:** Interest rate differential + trend

### 7. Asian Session Liquidity Gaps
**Asset:** FX  
**Data:** IBKR (hourly USD/JPY, AUD/USD)  
**Status:** Needs IBKR connection  
**Action:** Fade Tokyo session gaps

### 8. Credit-Equity Lag (HYG/SPY)
**Asset:** Cross-asset  
**Data:** yfinance (HYG, JNK, SPY)  
**Status:** Ready  
**Action:** HYG lead → SPY lag trade

### 9. Crypto Halving HMM
**Asset:** Crypto  
**Data:** yfinance (BTC-USD)  
**Status:** Ready  
**Action:** Regime detection on 4-year cycle

### 10. Yield Curve Rotation
**Asset:** Bonds  
**Data:** yfinance (TLT, IEF, SHY, SPTL)  
**Status:** Ready  
**Action:** Steepener/fattenner sector rotation

---

## TIER 3: Special Data Required (Park for Now)

| Hypothesis | Missing Data | Blocker |
|------------|--------------|---------|
| PEAD Earnings | Earnings calendar + EPS | Waiting for FMP |
| Miner Capitulation | Hash rate, miner flows | Glassnode API |
| CB NLP | Speech transcripts | Web scraping |
| Stablecoin Depeg | Stablecoin prices | Crypto exchange API |
| Index Inclusion | MSCI/S&P announcement dates | Manual tracking |

---

## Immediate Action Plan

### This Week (Tier 1)
1. **Peer Firm Lag:** Run correlation XOM vs SNP, CVX vs EC
2. **Precious Metals Ratio:** Backtest GLD/SLV rotation
3. **Trend Following:** 12-month momentum on SPY, TLT, GLD

### Next Week (Tier 2)
4. **Credit-Equity Lag:** HYG/SPY lead-lag analysis
5. **VIX Contango:** VXX roll yield strategy

### Blocked (Tier 3)
- PEAD → Your FMP signup
- Others → Special data sources

---

## YFinance Tickers Ready

```python
import yfinance as yf

# Oil peers
peers = ['XOM', 'CVX', 'SNP', 'PTR', 'EC', 'SLB', 'HAL']

# ADR dual-listed
adr = ['BABA', 'JD', 'TSM', 'SONY']

# Trend following universe
trend = ['SPY', 'QQQ', 'TLT', 'GLD', 'USO', 'UUP']

# Precious metals
metals = ['GLD', 'SLV', 'PPLT', 'PALL']

# Credit-equity
credit = ['HYG', 'JNK', 'LQD', 'SPY']

# VIX
vix = ['^VIX', 'VXX', 'UVXY', 'SVXY']

# All available via yfinance
```

---

## Files to Create This Week

1. `strategies/peer_firm_lag_backtest.py` — Oil majors vs nationals
2. `strategies/gold_silver_ratio_backtest.py` — Metals rotation
3. `strategies/trend_following_backtest.py` — Time series momentum
4. `strategies/credit_equity_lag_backtest.py` — HYG/SPY
5. `strategies/vix_contango_backtest.py` — Roll yield

All use yfinance only. No external APIs needed.
