# Hypothesis: Earnings Whisper Drift (Guidance vs Consensus)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short on whisper surprise  
**Horizon:** 1-5 days  
**Target Win Rate:** 65-70%

---

## Core Idea

Official "consensus" is stale. "Whisper numbers" (what sophisticated investors really expect) are higher. When company beats whisper → big rally. When beats consensus but misses whisper → sell-off despite "beat".

**The Edge:**
- Whisper numbers on EarningsWhispers.com
- Institutional estimates > street consensus
- Market prices to whisper, not consensus
- Standard "earnings surprise" is wrong metric

---

## Signal Construction

**Whisper Surprise Calculation:**
```
Actual EPS: $2.50
Consensus: $2.30 (street)
Whisper: $2.45 (smart money)

Street surprise: +8.7% ✅
Whisper surprise: +2.0% ❌ (stock drops)
```

**Trade:**
- Actual > Whisper + 5% → Long
- Actual < Whisper - 2% → Short
- Ignore street consensus

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 65-70% |
| Avg Return | 3-6% per trade |
| Sharpe | 1.5-2.0 |

---

## Data Sources

- EarningsWhispers.com (whisper numbers)
- Estimize (crowd-sourced estimates)
- Buy-side estimates (if accessible)
- Management guidance changes

---

## Why It Works

1. **Smart money knows more** — Analysts talk to management
2. **Consensus is anchoring** — Retail uses stale numbers
3. **Post-announcement drift** — Price adjusts to reality over 2-3 days
4. **Predictable errors** — Consensus systematically wrong on certain names

---

## Risk

- Whisper accuracy varies by company
- Requires real-time data
- Can be gamed by management

---

*Don't follow the crowd. Follow the smart money.*
