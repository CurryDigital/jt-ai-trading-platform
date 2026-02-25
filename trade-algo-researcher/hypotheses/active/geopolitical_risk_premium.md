# Hypothesis: Geopolitical Risk Premium Spike

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Gold / Oil / USD / VIX  
**Direction:** Long (safe havens)  
**Horizon:** 1-7 days  
**Target Win Rate:** 65-75%

---

## Core Idea

Geopolitical events (wars, sanctions, terrorism) create predictable flight-to-safety flows. Gold, USD, oil spike; equities drop. Mean reversion trade after initial shock.

**The Edge:**
- Initial spike = emotional overreaction
- 24-48 hours = drift as funds reposition
- 3-7 days = partial mean reversion

---

## Signal Construction

**Event Detection:**
```python
# News headline keywords
conflict_keywords = [
    "missile strike", "invasion", "war declared", 
    "terrorist attack", "embassy bombing", "assassination"
]

sanction_keywords = [
    "sanctions on", "export ban", "freeze assets",
    "swift ban", "oil embargo"
]

# Geopolitical Risk Index (GPR)
# Caldara & Iacoviello (2022) methodology
```

**Asset Mapping:**
| Event Type | Immediate Spike | 3-Day Drift |
|------------|-----------------|-------------|
| Middle East conflict | Oil +5%, Gold +2% | Oil fades, Gold holds |
| Russia/Ukraine escalation | Wheat +8%, Gas +10% | Partial mean reversion |
| China-Taiwan tension | Semis -5%, Gold +3% | Semis recover 50% |
| Terrorism (West) | VIX +20%, Gold +2% | VIX mean reverts |
| US-Iran tension | Oil +4%, Defense +3% | Oil fades in 48h |

**Trade Setup:**
```python
IF geopolitical event detected:
    # Phase 1: Immediate (0-6 hours)
    Long Gold (GLD)
    Long Oil (USO) if Middle East
    Short QQQ (risk-off)
    
    # Phase 2: Mean reversion (24-72 hours)
    If Oil/Gold up >3%:
        Short Oil (fade the spike)
        Keep Gold (sustained bid)
    If VIX up >20%:
        Short VIX (vol crush)
```

---

## Expected Performance

| Phase | Win Rate | Avg Return | Sharpe |
|-------|----------|------------|--------|
| Initial spike (0-6h) | 70% | 2-4% | 2.0 |
| Drift (6-24h) | 60% | 1-2% | 1.2 |
| Mean reversion (24-72h) | 55% | 2-3% | 1.0 |

---

## Data Requirements

- **Breaking news:** Bloomberg, Reuters, Dow Jones
- **Geopolitical Risk Index:** Fed data, Caldara-Iacoviello
- **Twitter/X:** Real-time conflict monitoring
- **Latency:** <30 minutes event to signal

**Sources:**
- Liveuamap (conflict tracking)
- BNO News (breaking)
- Twitter lists (war correspondents)

---

## Academic Support

- Caldara & Iacoviello (2022): Geopolitical Risk Index
- Glick & Taylor (2010): Trade war effects
- Datta & Mukhopadhyay (2021): War and commodity prices
- Balcilar et al. (2017): Geopolitical risk and gold

---

## Risk Factors

1. **Escalation** — Event worsens, positions underwater
2. **False alarms** — Headlines overstate severity
3. **Intervention** — Central banks coordinate response
4. **Sanctions complexity** — Unexpected winners/losers

---

## Execution

**Immediate (0-30 min):**
- Auto-buy GLD, SLV on confirmed event
- Size: 3-5% (high conviction)

**24-hour review:**
- Assess escalation vs de-escalation
- Trim winners, cut losers

**72-hour exit:**
- Mean reversion complete
- Flat or small core gold position

---

*Fear is temporary — position for the fade.*
