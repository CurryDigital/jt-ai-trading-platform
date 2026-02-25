# RESEARCH BATCH 14: Next Hypotheses for Testing
## Systematic Testing Pipeline — Created 2026-02-25

---

## STATUS SUMMARY

| Category | Count |
|----------|-------|
| **Golden Strategies** | 6 (deployed to paper trading) |
| **Active Hypotheses** | 40+ in `/hypotheses/active/` |
| **Data Requests Pending** | 5 (Accruals, ESG, FX Hourly, Crypto Funding, Options) |
| **Ready to Test** | 12 (data available) |

---

## BATCH 14: READY TO TEST NOW (Data Available)

### H014-001: Bollinger Squeeze Breakout
**Status:** idea → testing  
**Logic:** BB Width < 5% (20-day) + Volume > 2x → Breakout  
**Universe:** All 204 tickers  
**Expected:** 65%+ win rate on volatile tickers  
**Data:** RSI/BB already calculated in `gold.technical_indicators_calculated`  

**Test Plan:**
```python
entry: BB_Width < 0.05 AND Volume > 2 * Volume_SMA20
hold: 5 days
universe: full 204 tickers
```

---

### H014-002: CMV Multi-Factor Filter (RSI Enhancement)
**Status:** idea → testing  
**Logic:** Add Carry/Momentum/Value filter to existing RSI signals  
**Base:** S001 strategies  
**Enhancement:** Score stocks on CMV, increase size if >0.6, skip if <0.4  
**Data:** Dividend yields available, PE/PB in fundamentals

**Test Plan:**
```python
existing: RSI < 25
enhancement:
  carry_score = dividend_yield_percentile
  momentum_score = return_12m
  value_score = inverse(pe_ratio)
  
  IF cmv_score > 0.6: position *= 1.3
  ELIF cmv_score < 0.4: skip trade
```

---

### H014-003: ADR-Local Arbitrage (US-HK)
**Status:** idea → testing  
**Logic:** Price divergence between ADR and local HK shares  
**Universe:** 9988.HK/BABA, 0700.HK/TCEHY, etc.  
**Expected:** 60%+ win rate on >2% divergence  
**Data:** Both prices available in unified_prices

**Test Plan:**
```python
adr_local_ratio = price_adr / price_hk
z_score = (ratio - mean_20d) / std_20d

entry: abs(z_score) > 2.0
hold: 3 days
```

---

### H014-004: Buyback Yield Premium
**Status:** idea → testing  
**Logic:** High buyback yield stocks outperform  
**Universe:** US tickers with buyback data  
**Expected:** 62%+ win rate on top decile  
**Data:** Buyback yields in `gold.fundamental_signals`

**Test Plan:**
```python
buyback_yield = buyback_amount / market_cap
entry: buyback_yield > percentile(90) AND price > sma50
hold: 20 days
```

---

### H014-005: Crypto Miner Capitulation
**Status:** idea → testing  
**Logic:** Miner selling exhaustion → BTC bottom  
**Universe:** BTC-USD, MSTR  
**Expected:** 70%+ win rate on extreme signals  
**Data:** BTC price available, miner flows via API

**Test Plan:**
```python
hash_rate_change = (hash_rate - hash_rate_30d_ago) / hash_rate_30d_ago
entry: hash_rate_change < -10% AND RSI < 30
hold: 10 days
```

---

### H014-006: China Policy Announcement Drift
**Status:** idea → testing  
**Logic:** CN equities drift after policy announcements  
**Universe:** 0700.HK, 9988.HK, 0001.HK, CN ETFs  
**Expected:** 58%+ win rate on monetary policy days  
**Data:** Policy dates from news, prices available

**Test Plan:**
```python
policy_dates = ['2024-03-15', '2024-06-20', ...]  # PBOC cuts
entry: date in policy_dates AND sector = 'CN_Tech'
hold: 5 days
```

---

### H014-007: Cross-Asset Credit-Equity Lag
**Status:** idea → testing  
**Logic:** Credit spreads lead equity moves by 1-3 days  
**Universe:** HYG (high yield) → SPY, QQQ  
**Expected:** 60%+ win rate on extreme spread moves  
**Data:** HYG, SPY, QQQ prices available

**Test Plan:**
```python
credit_change = HYG_return[t-3:t]
equity_signal = SPY_return[t+1:t+3]

entry: credit_change < -2% (credit selling)
hold: 3 days
exit: equity bounce
```

---

### H014-008: Commodity Term Structure
**Status:** idea → testing  
**Logic:** Backwardation → long, Contango → short/avoid  
**Universe:** CL=F, GC=F, HG=F, NG=F  
**Expected:** 65%+ win rate on extreme curves  
**Data:** Futures curves needed — check availability

**Test Plan:**
```python
roll_yield = (front_month - back_month) / back_month
entry: roll_yield > 0.05 (backwardation)
hold: 10 days
```

---

### H014-009: Dispersion Trading (Index vs Components)
**Status:** idea → testing  
**Logic:** Sell index vol, buy component vol when correlation spikes  
**Universe:** QQQ vs top 10 components  
**Expected:** Market neutral, 55%+ win rate  
**Data:** Need options data — REQUEST_005 pending

**Status:** BLOCKED — Options data not available

---

### H014-010: Earnings Surprise Momentum
**Status:** idea → testing  
**Logic:** Post-earnings drift for positive surprises  
**Universe:** US tickers with earnings data  
**Expected:** 62%+ win rate on >10% EPS beat  
**Data:** Earnings calendar needed

**Test Plan:**
```python
earnings_beat = (actual_eps - expected_eps) / expected_eps
entry: earnings_beat > 0.10 AND gap_up < 5%
hold: 5 days
```

---

## DATA REQUIREMENTS CHECK

### Available (Can Test Now):
| Hypothesis | Data Source | Status |
|------------|-------------|--------|
| H014-001 Bollinger Squeeze | gold.technical_indicators_calculated | ✅ READY |
| H014-002 CMV Filter | gold.fundamental_signals + prices | ✅ READY |
| H014-003 ADR Arbitrage | unified_prices | ✅ READY |
| H014-004 Buyback Yield | gold.fundamental_signals | ✅ READY |
| H014-005 Crypto Capitulation | unified_prices + API | ✅ READY |
| H014-006 CN Policy Drift | News dates + prices | ✅ READY |
| H014-007 Credit-Equity Lag | unified_prices | ✅ READY |

### Blocked (Need Data):
| Hypothesis | Missing Data | Request ID |
|------------|--------------|------------|
| H014-008 Commodity Term | Futures curves | NEW |
| H014-009 Dispersion | Options chains | REQUEST_005 |
| H014-010 Earnings | Earnings calendar | NEW |

---

## TESTING PRIORITY

### High Priority (Test This Week):
1. **H014-001** — Bollinger Squeeze (technical, easy to test)
2. **H014-002** — CMV Filter (enhances existing GOLD strategies)
3. **H014-003** — ADR Arbitrage (information arbitrage framework)

### Medium Priority (Test Next Week):
4. **H014-004** — Buyback Yield
5. **H014-005** — Crypto Capitulation
6. **H014-007** — Credit-Equity Lag

### Lower Priority (Need Data):
7. H014-006 — CN Policy Drift (requires news parsing)
8. H014-008, 009, 010 — Blocked on data

---

## NEXT ACTIONS

### Immediate (Today):
- [ ] Create backtest script for H014-001 (Bollinger Squeeze)
- [ ] Query `gold.technical_indicators_calculated` for BB_Width
- [ ] Run 3-tier validation on full 204 ticker universe

### Script Created:
✅ `H014_001_backtest.py` — Ready to run with DB connection
**Run command:** `python3 rigorous_retest/H014_001_backtest.py`

### This Week:
- [ ] Test H014-002 (CMV Filter on S001-HK-Banks)
- [ ] Test H014-003 (ADR Arbitrage on 9988/BABA, 0700/TCEHY)
- [ ] Document results in `memory/2026-02-25.md`

### File New Data Requests:
- [ ] REQUEST_006: Commodity futures curves (CL, GC, HG, NG)
- [ ] REQUEST_007: Earnings calendar with surprise data

---

**Research cycle continuing — 7 hypotheses ready for immediate testing.**
