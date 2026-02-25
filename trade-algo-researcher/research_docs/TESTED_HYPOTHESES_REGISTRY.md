

---

## Multi-Market Test Results Matrix

**Last Updated:** 2026-02-18

### Technical Analysis Stack

| Hypothesis | US | HK | CN | Classification | Deploy On |
|------------|----|----|----|----------------|-----------|
| **RSI Mean Reversion** | ✅ (GOOGL: 60%) | ✅ (QQQ: 57%) | ⏳ | **UNIVERSAL** | All tested |
| **MACD Divergence** | ❌ (46%) | ⚠️ (0700: 57%) | ⏳ | **SECTOR-SPECIFIC** | Tech only |
| **Bollinger Squeeze** | ✅ (IWM: 67%) | ⏳ | ⏳ | **MARKET-SPECIFIC (US)** | US IWM only |
| **Engulfing Pattern** | ✅ (SPY: 80%) | ⚠️ (low sample) | ⏳ | **MARKET-SPECIFIC (US)** | US only |
| **3-Day Reversal** | ❌ (48%) | ✅ (0005: 76%, 1299: 70%) | ⏳ | **MARKET-SPECIFIC (HK)** | HK: 0005, 1299, 9988 |
| **Gap Fade** | ❌ (47%) | ✅ (0001: 58%, 1299: 56%) | ⏳ | **MARKET-SPECIFIC (HK)** | HK: 0001, 1299 |
| **20-Day Momentum** | ✅ (META: 57%) | ⏳ | ⏳ | **MARKET-SPECIFIC (US)** | US META only |

### Market/Allocation Strategies

| Hypothesis | US | HK | CN | Classification | Deploy On |
|------------|----|----|----|----------------|-----------|
| **VIX Proxy** | ❌ (44%) | — | — | **REJECTED** | None |
| **Sector Rotation (Tech/Util)** | ✅ (66%, 599 trades) | ⏳ | ⏳ | **UNIVERSAL?** | Need Asia validation |
| **Gold/Silver Pairs** | ❌ (51%) | — | — | **REJECTED** | Use Gold/Silver Ratio instead |
| **Yield Curve Proxy** | ⚠️ (53%, low sample) | — | — | **NEEDS MORE DATA** | Not validated |

### Pairs/Arbitrage

| Hypothesis | US | HK | CN | Classification | Deploy On |
|------------|----|----|----|----------------|-----------|
| **Peer Firm Lag** | ❌ (0 lag) | ❌ (0 lag, 0.04 corr) | ❌ (delisted) | **REJECTED** | None |
| **ADR-Local Arbitrage** | ⚠️ (data issues) | — | — | **TESTING** | Incomplete |

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Tested, meets criteria |
| ⚠️ | Tested, marginal/needs more data |
| ❌ | Tested, failed |
| ⏳ | Not tested yet |
| — | Not applicable |

---

## Market-Specific Deployment Guide

### Hong Kong (HK) Validated Tickers

**3-Day Reversal Strategy:**
- 0005.HK (HSBC) - 76% win, 1.91 Sharpe
- 1299.HK - 70% win, 3.01 Sharpe
- 9988.HK (BABA HK) - 59% win, 3.21 Sharpe

**Gap Fade Strategy:**
- 0001.HK (CKH) - 58% win, 2.86 Sharpe
- 1299.HK - 56% win, 2.28 Sharpe

**MACD Divergence:**
- 0700.HK (Tencent) - 57% win, 0.51 Sharpe

### US Validated Tickers

**RSI Mean Reversion:**
- GOOGL - 60% win, 1.42 Sharpe
- QQQ - 57% win, 0.91 Sharpe

**Bollinger Squeeze:**
- IWM - 67% win, 3.64 Sharpe

**Engulfing Pattern:**
- SPY - 80% win, 3.90 Sharpe (low sample)

**20-Day Momentum:**
- META - 57% win, 0.80 Sharpe

---

## Summary Statistics

| Classification | Count | Examples |
|----------------|-------|----------|
| **UNIVERSAL** | 1 | RSI Mean Reversion |
| **MARKET-SPECIFIC** | 5 | 3-Day Reversal (HK), Gap Fade (HK), etc. |
| **SECTOR-SPECIFIC** | 1 | MACD Divergence (Tech only) |
| **REJECTED** | 3 | Peer Firm Lag, VIX Proxy, Gold/Silver Pairs |
| **TESTING** | 45+ | Awaiting multi-market validation |

---

*See MULTI_MARKET_TESTING_FRAMEWORK.md for testing protocol*
