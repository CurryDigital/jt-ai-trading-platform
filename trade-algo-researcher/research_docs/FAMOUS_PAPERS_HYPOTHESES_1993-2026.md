# New Hypotheses from Famous Academic Papers (1993-2026)

**Date:** 2026-02-19  
**Search Method:** Serper API (Google Scholar/SSRN)  
**Scope:** Classic famous papers + recent top research  
**New Hypotheses:** 8  

---

## Classic/Famous Papers Reviewed

### Momentum Literature
| Paper | Authors | Year | Key Finding |
|-------|---------|------|-------------|
| Returns to Buying Winners | Jegadeesh & Titman | 1993 | 12-month momentum works |
| Momentum (update) | Jegadeesh & Titman | 2001 | Profits persist beyond 1990s |
| Unified Theory of Underreaction | Hong & Stein | 1999 | Gradual info diffusion explains momentum |
| Time Series Momentum | Moskowitz, Ooi, Pedersen | 2012 | Trend following across assets |
| A Century of Trend Following | Hurst, Ooi, Pedersen | 2017 | 100+ years of positive returns |

### Factor Models
| Paper | Authors | Year | Key Finding |
|-------|---------|------|-------------|
| Common Risk Factors | Fama & French | 1993 | Value + Size factors |
| Five-Factor Model | Fama & French | 2015 | Added profitability + investment |
| Value and Momentum Everywhere | Asness et al. | 2013 | Both factors work across assets |
| Quality Minus Junk | Asness et al. | 2018 | Quality factor is distinct |
| The Other Side of Value | Novy-Marx | 2013 | Profitability predicts returns |

### Anomalies
| Paper | Authors | Year | Key Finding |
|-------|---------|------|-------------|
| Accruals Anomaly | Sloan | 1996 | High accruals → lower future returns |
| Post-Earnings Drift | Ball & Brown | 1968 | Earnings surprises drift |
| Limits to Arbitrage | Shleifer & Vishny | 1997 | Arbitrage constraints prevent correction |
| Carry Trades & Crashes | Brunnermeier et al. | 2008 | Carry works but has crash risk |
| Expected Option Returns | Coval & Shumway | 2001 | Selling volatility earns premium |

### Recent (2020-2026)
| Paper | Authors | Year | Key Finding |
|-------|---------|------|-------------|
| Interacting Anomalies | Various | 2024 | Multi-factor combinations have edge |
| ML Uncertainty in Asset Pricing | Various | 2025 | Uncertainty-weighted sizing improves Sharpe |
| KAMA Strategy | Various | 2025 | Adaptive indicators outperform static |
| ESG and Comovements | Various | 2024 | ESG improvers work better than levels |

---

## 8 New Hypotheses

### 1. Momentum Lifecycle Combo
**File:** `hypotheses/active/momentum_lifecycle_combo.md`  
**Academic Basis:** Jegadeesh & Titman (1993, 2001), Hong & Stein (1999)  
**Core Idea:** Combine short-term reversal (1m) + medium-term momentum (3-12m) + long-term reversal (3-5y)  
**Enhancement Target:** RSI Mean Reversion  
**Expected Sharpe:** 1.1-1.4

**Signal:**
```python
IF return_1m < -10% AND volume > 1.5x:  # Short-term reversal
    LONG

IF return_12m > 80th_percentile AND earnings_surprise > 0:  # Momentum
    LONG

IF return_5y < 20th_percentile AND P/E < median:  # Long-term reversal
    LONG
```

---

### 2. Accruals Quality + Mean Reversion
**File:** `hypotheses/active/accruals_quality_mean_reversion.md`  
**Academic Basis:** Sloan (1996), Shleifer & Vishny (1997)  
**Core Idea:** Add Sloan's accruals quality filter to RSI mean reversion  
**Enhancement Target:** RSI Mean Reversion  
**Expected Sharpe:** 1.2-1.5

**Signal:**
```python
accrual_ratio = (net_income - operating_cash_flow) / total_assets

IF RSI < 30:
    IF accrual_ratio < median:  # High quality
        position_size = base_size * 1.5
    ELIF accrual_ratio > 80th_percentile:  # Low quality
        position_size = base_size * 0.5
```

---

### 3. Time-Series Momentum Overlay
**File:** `hypotheses/active/time_series_momentum_overlay.md`  
**Academic Basis:** Hurst, Ooi & Pedersen (2017), Moskowitz et al. (2012)  
**Core Idea:** Add trend-following overlay to filter mean reversion signals  
**Enhancement Target:** Portfolio allocation + RSI filter  
**Expected Sharpe:** 1.0-1.3

**Signal:**
```python
IF RSI < 30:  # Oversold
    IF time_series_momentum > 0:  # But in uptrend
        position_size = base_size * 1.2
    ELIF time_series_momentum < -0.5:  # Strong downtrend
        SKIP or SHORT
```

---

### 4. Volatility Risk Premium Harvesting
**File:** `hypotheses/active/volatility_risk_premium.md`  
**Academic Basis:** Coval & Shumway (2001), Carr & Wu (2009)  
**Core Idea:** Capture VRP via proxies (low-vol equities, VIX contango)  
**Enhancement Target:** Options proxy + RSI volatility adjustment  
**Expected Sharpe:** 1.1-1.4

**Signal:**
```python
# Low-vol proxy
IF realized_vol_1m < percentile(10):
    AND RSI > 40:
    LONG

# Dynamic RSI thresholds
IF VIX < 15: rsi_threshold = 25
ELIF VIX > 30: rsi_threshold = 35
```

---

### 5. Quality at Reasonable Price (QARP)
**File:** `hypotheses/active/quality_value_qarp.md`  
**Academic Basis:** Asness (2018), Novy-Marx (2013)  
**Core Idea:** Combine Quality (profitability, stability) + Value  
**Enhancement Target:** AH Premium, SG REIT selection  
**Expected Sharpe:** 1.1-1.4

**Signal:**
```python
quality = z_score(profitability + stability + payout)
value = z_score(-P/E - P/B - P/S)
qarp_score = quality + value

IF qarp_score > 80th_percentile:
    AND quality > 60th_percentile:
    AND value > 60th_percentile:
    LONG
```

---

### 6. CMV Multi-Factor (Carry + Momentum + Value)
**File:** `hypotheses/active/cmv_multi_factor.md`  
**Academic Basis:** Asness (2013), Koijen et al. (2018)  
**Core Idea:** Combine three negatively correlated factors across asset classes  
**Enhancement Target:** Cross-asset allocation  
**Expected Sharpe:** 1.2-1.5

**Signal:**
```python
# FX example
IF interest_rate_diff > 0:  # Carry
    AND return_12m > 0:  # Momentum
    AND ppp_deviation < 0:  # Value
    LONG currency_pair
```

---

### 7. Limits to Arbitrage Exploit
**File:** `hypotheses/active/limits_to_arbitrage_exploit.md` *(can be created)*  
**Academic Basis:** Shleifer & Vishny (1997)  
**Core Idea:** Identify situations where arbitrage constraints prevent correction  
**Enhancement Target:** Short squeeze plays  
**Expected Sharpe:** 1.0-1.3

**Signal:**
```python
IF short_interest > 95th_percentile:
    AND borrow_cost > 50bps:
    AND market_cap < 10B:  # Hard to short
    # Short squeeze potential
    LONG
```

---

### 8. PEAD Enhanced with NLP
**File:** `hypotheses/active/pead_nlp_enhanced.md` *(can be created)*  
**Academic Basis:** Ball & Brown (1968) + Lopez-Lira (2023)  
**Core Idea:** Traditional PEAD + LLM sentiment analysis  
**Enhancement Target:** Earnings trades  
**Expected Sharpe:** 1.3-1.6

**Signal:**
```python
IF earnings_surprise > 0:
    AND llm_sentiment > +3:  # Positive transcript tone
    AND options_iv_spike > 30%:  # Vol crush opportunity
    LONG
```

---

## Enhancements to Existing Strategies

### RSI Mean Reversion v2.0 → v3.0
**Current:** RSI < 30 + Volume > 1.3x  
**Proposed v3.0:**
- RSI < 28 (tighter)
- Volume > 1.5x (stronger)
- **+** Accruals quality filter (Sloan 1996)
- **+** Time-series momentum trend filter (Hurst 2017)
- **+** Quality score position sizing (Asness 2018)
- **+** Momentum lifecycle timing (Jegadeesh 1993)

**Expected:** Sharpe 1.4 → 1.6-1.8

### AH Premium Arbitrage
**Current:** Premium > 30%  
**Proposed Enhancements:**
- **+** Quality filter: High-quality banks only (Asness 2018)
- **+** Carry enhancement: H-share dividend yield advantage
- **+** Time-series momentum: HKD/CNY trend filter

**Expected:** Win rate 72% → 75-78%

### ARASO Factor Model
**Current:** ML uncertainty weighting  
**Proposed:**
- **+** Quality factor integration (Fama-French 2015)
- **+** CMV multi-factor overlay

**Expected:** Sharpe 2.7 → 2.9-3.1

---

## Summary Table

| Hypothesis | Famous Paper | Enhancement Target | Expected Sharpe | Data Cost |
|------------|--------------|-------------------|-----------------|-----------|
| Momentum Lifecycle | Jegadeesh/Titman 1993 | RSI Mean Reversion | 1.1-1.4 | Low |
| Accruals Quality | Sloan 1996 | RSI Mean Reversion | 1.2-1.5 | Low |
| Time-Series Momentum | Hurst 2017 | Portfolio allocation | 1.0-1.3 | Low |
| Volatility Premium | Coval/Shumway 2001 | Options proxy | 1.1-1.4 | Medium |
| Quality Value QARP | Asness 2018 | AH Premium, SG REIT | 1.1-1.4 | Low |
| CMV Multi-Factor | Asness 2013 | Cross-asset | 1.2-1.5 | Medium |
| Limits to Arbitrage | Shleifer/Vishny 1997 | Short squeeze | 1.0-1.3 | Low |
| PEAD + NLP | Ball/Brown 1968 + 2023 | Earnings trades | 1.3-1.6 | Medium |

---

## Total Count
- Previous: 80
- New: 8
- **Total: 88 active hypotheses**

---

**Academic research synthesis complete. Classic papers (1993-2018) + recent research (2020-2026) integrated into enhancement roadmap.**
