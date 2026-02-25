# Hypothesis: Index Rebalancing Pressure (Forced Buying/Selling)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Pre-rebalance momentum, post-rebalance reversal  
**Horizon:** 1-4 weeks  
**Target Win Rate:** 70-75%

---

## Core Idea

Index funds (SPY, QQQ, IWM) MUST buy/sell at rebalance. $10T+ in passive flows creates predictable price pressure around rebalance dates.

**The Edge:**
- Index additions = forced buying (price up before rebalance)
- Index deletions = forced selling (price down before rebalance)
- Post-rebalance reversal (arbs unwind)

---

## Rebalance Calendar (Predictable)

| Index | Frequency | AUM | Impact |
|-------|-----------|-----|--------|
| S&P 500 | Quarterly | $5T+ | Highest |
| Russell 2000 | Annual (June) | $1T+ | High |
| MSCI EM | Quarterly | $2T+ | Medium |
| Nasdaq 100 | Annual (Dec) | $1T+ | High |

---

## Signal Construction

**Addition Play (1 week before rebalance):**
```
Stock added to S&P 500
Announcement T-5 days
Rebalance T+0 (Friday close)

Trade: Long from announcement to rebalance
Exit: Rebalance day (forced buying peaks)
```

**Deletion Play:**
```
Stock deleted from index
Short from announcement to rebalance
Exit: Rebalance day
```

**Reversal Play (Post-rebalance):**
```
Day after rebalance: Fade the move
Index funds done buying → arbs sell
Mean reversion over next week
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 70-75% |
| Addition pop | +3-5% pre-rebalance |
| Deletion drop | -4-7% pre-rebalance |
| Reversal | +2% next week |
| Sharpe | 1.5-2.5 |

---

## Data Requirements

- Index rebalance announcements (5 days prior)
- Effective dates (predictable)
- Historical rebalance impacts

---

## Why It Works

1. **Forced flows** — Passive MUST trade, no choice
2. **Predictable timing** — Announced in advance
3. **Huge size** — Billions in flow
4. **Temporary dislocation** — Price pressure, not fundamental

---

## Academic Support

- Petajisto (2011): Index premium
- Chen et al.: S&P 500 inclusion effects
- $10T+ passive AUM creates structural alpha

---

## Risk

- Market impact changes over time (arbs learn)
- Works best on smaller additions/deletions
- Requires precision timing

---

*Trade the indexers, not the stock.*
