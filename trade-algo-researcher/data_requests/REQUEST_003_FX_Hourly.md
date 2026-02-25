## DATA REQUEST - Hourly FX Data

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** 2026-02-20  
**Priority:** MEDIUM

---

### Data Required

**Table/Schema:** `gold.fx_hourly` or `silver.fx_hourly`  
**Columns:**
- `timestamp` (TIMESTAMP)
- `pair` (VARCHAR) - e.g., 'USDJPY', 'EURUSD'
- `bid` (NUMERIC)
- `ask` (NUMERIC)
- `volume` (NUMERIC) - if available

**Time Period:** 2020-01-01 to 2024-12-31  
**Frequency:** Hourly (Tokyo, London, NY sessions)  
**Pairs:** USDJPY, EURUSD, GBPUSD, USDCNH, AUDUSD

---

### Purpose

Testing **Asian Session Liquidity Fade hypothesis**:
- Tokyo session liquidity patterns
- Fade the Asian session moves
- Need intraday data - daily insufficient

Previous attempt with **daily overnight gaps FAILED** (35.5% win rate) - proxy rejected.

---

### Blocking Status

☑️ **BLOCKING** - Previous proxy failed validation

Daily data cannot capture Asian Session dynamics.

---

### Suggested Source

**Option 1:** TrueFX (free)
- Cost: FREE
- Quality: Good for research
- History: 10+ years
- Format: Tick/bid-ask

**Option 2:** IBKR Historical Data
- Cost: FREE (for account holders)
- Quality: Good
- History: 2+ years
- Limitation: Need API access

**Option 3:** Dukascopy
- Cost: FREE
- Quality: Good
- History: 10+ years
- Limitation: Download limits

**Option 4:** Bloomberg/Refinitiv
- Cost: $$$ (expensive)
- Quality: Best
- History: 20+ years

---

### Acceptance Criteria

- [ ] Hourly bars for 4+ years
- [ ] Asian session coverage (00:00-08:00 UTC)
- [ ] Major pairs: USDJPY, EURJPY, AUDJPY
- [ ] Bid-ask spreads or mid prices

---

### Recommendation

**TrueFX** is sufficient for research validation.
Alternative: **IBKR** if account already exists.

---

**Status:** RECOMMEND TRUEFX (FREE)
