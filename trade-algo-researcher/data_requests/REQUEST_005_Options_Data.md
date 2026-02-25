## DATA REQUEST - Options Chain Data

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** 2026-02-20  
**Priority:** LOW (multiple hypotheses affected)

---

### Data Required

**Table/Schema:** `gold.options_chain` (new table)  
**Columns:**
- `date` (DATE)
- `ticker` (VARCHAR)
- `expiration` (DATE)
- `strike` (NUMERIC)
- `option_type` (VARCHAR) - 'CALL' or 'PUT'
- `bid` (NUMERIC)
- `ask` (NUMERIC)
- `volume` (INTEGER)
- `open_interest` (INTEGER)
- `implied_volatility` (NUMERIC)
- `delta` (NUMERIC)
- `gamma` (NUMERIC)
- `theta` (NUMERIC)
- `vega` (NUMERIC)

**Time Period:** 2020-01-01 to 2024-12-31  
**Frequency:** End-of-day  
**Universe:** S&P 500, high-volume ETFs (SPY, QQQ, IWM)

---

### Purpose

**Multiple hypotheses require options data:**

1. **Volatility Risk Premium** (Coval/Shumway 2001)
   - Sell options vs realized volatility
   - Need IV and realized vol

2. **Options Gamma Gravity** (new hypothesis)
   - Max pain / pin risk near expiration
   - Need OI and gamma by strike

3. **Post-Earnings Vol Crush** (new hypothesis)
   - IV collapse after earnings
   - Need pre/post earnings IV

---

### Blocking Status

☑️ **BLOCKING** - 3 hypotheses affected

No acceptable proxy for options data.

---

### Suggested Source

**Option 1:** Polygon.io
- Cost: $200-500/month
- Quality: Good for research
- History: 3+ years
- API: RESTful

**Option 2:** Cboe DataShop
- Cost: $500-2000/month
- Quality: Best
- History: 10+ years
- Format: CSV delivery

**Option 3:** ORATS (Option Research & Technology Services)
- Cost: $300-1000/month
- Quality: Excellent
- History: 10+ years
- Features: Backtesting ready

**Option 4:** Delta Neutral (free tiers)
- Cost: FREE (limited)
- Quality: Basic
- History: 1 year
- Limitation: Limited history

---

### Acceptance Criteria

- [ ] EOD options chains for 3+ years
- [ ] Greeks calculated (delta, gamma, theta, vega)
- [ ] IV surface by strike and expiration
- [ ] Volume and OI data

---

### Cost-Benefit

**Cost:** $2,400-24,000/year  
**Benefit:** Validate 3 hypotheses (VRP, Gamma, Vol Crush)  
**Combined Target Sharpe:** 1.2-1.5 average  
**Decision:** User approval required

---

### Recommendation

**Start with Polygon.io** ($200-500/month) for initial validation.
Upgrade to ORATS if strategies prove viable.

---

**Status:** AWAITING BUDGET APPROVAL
