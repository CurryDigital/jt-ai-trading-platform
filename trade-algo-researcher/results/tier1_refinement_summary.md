# Tier 1 Refinement Results

**Date:** 2026-02-18  

---

## Summary

| Strategy | Original | Refined | Status |
|----------|----------|---------|--------|
| **Gold/Silver** | Sharpe 1.11 | - | ✅ KEEP |
| Trend Following | Sharpe 0.36 | Sharpe 0.37 | ❌ REJECT |
| Peer Firm Lag | Data issue | Sharpe -0.58 | ❌ REJECT |
| ADR Arbitrage | 12-85% dev | Needs FX | ⏸️ PARK |
| VIX Contango | VXX delisted | - | ❌ REJECT |

---

## What Worked

**Gold/Silver Ratio (ONLY ONE)**
- Sharpe 1.11 exceeds 0.8 target
- 65% win rate
- Real mean reversion signal

---

## What Failed & Why

### Trend Following (0.37 Sharpe)
**Problem:** Momentum faded in 2022-2024 choppy markets  
**Tried:** 63/126/189/252d lookbacks, volatility scaling  
**Result:** Still below 1.0 target  
**Verdict:** Not viable in current regime

### Peer Firm Lag (-0.58 Sharpe)
**Problem:** High correlation (0.7-0.8) but ZERO lag  
**Tried:** US E&Ps (COP→DVN, XOM→OXY)  
**Result:** Simultaneous moves, no alpha  
**Verdict:** Market too efficient for simple lag

### ADR Arbitrage
**Problem:** 12-85% deviations likely data artifacts (ADR ratios)  
**Need:** Real-time FX adjustment + intraday data  
**Verdict:** Interesting but requires significant infra

### VIX Contango
**Problem:** VXX delisted 2024  
**Need:** VIX futures directly (IBKR)  
**Verdict:** Doable with Tier 2 data

---

## Recommendation

**ACCEPT:** Gold/Silver only  
**REJECT:** Trend, Peer Lag (for now)  
**PARK:** ADR, VIX (need more work)

---

## Next Steps

1. **Promote Gold/Silver** → Already done ✅
2. **Develop Tier 2** with IBKR (FX, VIX futures)
3. **New hypotheses** with stronger academic backing
4. **Alternative data** (sentiment, options flow)

---

## Lesson

Simple price-based strategies struggle in efficient markets.  
Need either:
- Alternative data edge
- Execution/speed advantage  
- Structural mispricing (like funding rates)

Gold/Silver works because it's fundamental (ratio economics) + behavioral (investor overreaction).
