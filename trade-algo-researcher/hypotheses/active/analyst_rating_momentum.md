# Hypothesis: Analyst Upgrade/Downgrade Momentum

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-5 days  
**Target Win Rate:** 55-60%

---

## Core Idea

Sell-side analyst rating changes (upgrade/downgrade) create 1-3 day drift. Market underreacts to new information. Top-rated analysts (Goldman, Morgan Stanley) have more impact.

**The Edge:**
- Analysts have information advantage (management access)
- Price target changes = new valuation anchor
- Underreaction lasts 24-48 hours

---

## Signal Construction

**Analyst Tier (Impact Weighting):**
```python
tier_1 = ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America"]
tier_2 = ["Deutsche Bank", "Barclays", "Citi", "Wells Fargo"]
tier_3 = ["Regional firms", " boutiques"]

weight = {"tier_1": 1.5, "tier_2": 1.0, "tier_3": 0.5}
```

**Rating Change Scoring:**
```python
# Upgrade intensity
upgrade_score = {
    "Sell → Hold": 1,
    "Hold → Buy": 2,
    "Sell → Buy": 3,  # Rare, strong signal
    "Price target ↑ >20%": 2
}

# Downgrade intensity
downgrade_score = {
    "Buy → Hold": -1,
    "Hold → Sell": -2,
    "Buy → Sell": -3,
    "Price target ↓ >20%": -2
}
```

**Signal Threshold:**
```python
IF upgrade_score >= 2 AND analyst_tier <= 2:
    → Long stock, 2-3 day hold
    
IF downgrade_score <= -2 AND analyst_tier <= 2:
    → Short stock, 2-3 day hold
```

---

## Expected Performance

| Change Type | Win Rate | Avg Return | Sharpe |
|-------------|----------|------------|--------|
| Tier 1 upgrade | 62% | 2-4% | 1.1 |
| Tier 1 downgrade | 58% | 3-5% | 1.0 |
| Price target ↑>30% | 55% | 4-6% | 1.2 |
| Initiation (Buy) | 52% | 1-2% | 0.6 |

**Decay:** Alpha strongest in first 24 hours, gone by day 5.

---

## Data Requirements

- **Analyst feeds:** Bloomberg, FactSet, Capital IQ
- **Real-time:** Benzinga, Briefing.com (retail)
- **Historical:** TipRanks (analyst track record)
- **Latency:** <15 minutes from announcement

**Key Fields:**
- Firm name (for tier weighting)
- Old rating → New rating
- Price target (old vs new)
- Stock ticker

---

## Academic Support

- Womack (1996): Do brokerage analysts' recommendations have investment value?
- Barber et al. (2001): Reassessing the returns to analyst stock recommendations
- Jegadeesh & Kim (2006): Value of analyst recommendations
- Loh & Stulz (2011): When are analyst recommendation changes influential?

---

## Risk Factors

1. **Conflicted research** — Investment banking relationships bias ratings
2. **Late to party** — Upgrade after 50% run = top-tick
3. **Crowding** — Consensus upgrades = crowded long
4. **Earnings proximity** — Pre-earnings upgrades = setup for disappointment

---

## Best Practices

**Avoid:**
- Upgrades after 20%+ recent move
- Small-cap stocks (<$1B market cap)
- Pre-earnings changes
- Downgrades on already hated stocks (contrarian)

**Prefer:**
- Rating reversals (Sell→Buy, not Hold→Buy)
- Price target >20% increase
- Post-earnings guidance raises
- Sectors in favor (momentum)

---

## Execution

**Entry:** Within 1 hour of announcement
**Sizing:** 1-2% per signal
**Stop:** 2.5% adverse
**Exit:** 48 hours or momentum exhaustion

---

*Wall Street research — priced slowly, not instantly.*
