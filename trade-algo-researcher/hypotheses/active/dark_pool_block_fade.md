# Hypothesis: Dark Pool Block Trade Fade (Institutional Flow Reversal)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Contrarian to block trades  
**Horizon:** 2-5 days  
**Target Win Rate:** 60-65%

---

## Core Idea

Large block trades on dark pools (whales) often mark local extremes. Institutional "urgency" execution = desperation. When whales dump, retail panics, creating dip. When whales buy at any price, top is near.

**The Edge:**
- Block trades >1% ADV = urgency
- Dark pool activity reveals desperation
- Fade the whale (they're wrong at extremes)

---

## Signal Construction

**Block Detection:**
- Trade size >50,000 shares
- Off-exchange (dark pool prints)
- Price impact >0.5%

**Short Setup (Desperate Buying):**
```
IF dark_pool_buy_ratio > 80% AND
   block_count > 10 AND
   price_up_1d > 5% AND
   block_avg_premium > 1% (paying up)
THEN short (whale exhaustion)
```

**Long Setup (Capitulation Selling):**
```
IF dark_pool_sell_ratio > 80% AND
   block_count > 10 AND
   price_down_1d > 5% AND
   block_avg_discount > 1% (dumping)
THEN long (whale capitulation)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 2-4% per trade |
| Sharpe | 1.2-1.8 |

---

## Data Requirements

- Dark pool prints (SqueezeMetrics, Cboe)
- Block trade database
- Premium/discount to VWAP
- Whale positioning (COT reports)

---

## Why It Works

1. **Urgency = alpha** — If they could wait for better price, they would
2. **Market impact** — Blocks move price temporarily
3. **Reversion** — Desperation marks extremes
4. **Information asymmetry** — Whales may know something, but timing is wrong

---

## Risk

- Requires dark pool data (expensive)
- Whales sometimes know (insider info)
- False signals in trending markets

---

*When the whale surfaces, the tide is about to turn.*
