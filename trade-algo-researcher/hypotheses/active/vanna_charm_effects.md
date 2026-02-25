# Hypothesis: Vanna-Charm Effects (Options Flow Impact)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Delta-hedge flow direction  
**Horizon:** 1-10 days  
**Target Win Rate:** 60-65%

---

## Core Idea

Options have second-order Greeks:
- **Vanna:** How delta changes with volatility
- **Charm:** How delta changes with time

When IV drops (post-earnings), delta-hedge flows create predictable price pressure.

**The Edge:**
- Post-earnings IV crush → dealers unwind hedges
- Creates directional flow
- Predictable price impact

---

## The Mechanics

**Pre-Earnings:**
- Traders buy straddles (long gamma)
- Dealers short straddles (short gamma)
- Dealers hedge delta-neutral

**Post-Earnings:**
- IV drops 30-50% (IV crush)
- Delta of options changes (charm effect)
- Dealers must re-hedge
- Creates directional flow

---

## Signal Construction

**Entry (Day After Earnings):**
```
IF stock up >5% on earnings AND
   IV crush >30% AND
   call_gamma > put_gamma (net long)
THEN short (dealers sell to rebalance)
```

**Opposite:**
```
IF stock down >5% AND
   IV crush >30% AND
   put_gamma > call_gamma
THEN long (dealers buy to rebalance)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 2-4% per trade |
| Sharpe | 1.2-1.8 |
| Best Stocks | High options OI names (AAPL, TSLA, NVDA) |

---

## Data Requirements

- Options Greeks (delta, gamma, charm, vanna)
- Earnings calendar
- IV pre/post earnings
- Dark pool/whale flow

---

## Why It Works

1. **Forced selling/buying** — Dealers must hedge, no choice
2. **Predictable magnitude** — Can calculate hedge flow size
3. **Temporary dislocation** — Flow completes in 1-3 days
4. **Retail doesn't see it** — Options second-order Greeks are complex

---

## Academic Support

- Derman: My Life as a Quant (Greek dynamics)
- Taleb: Dynamic Hedging
- Modern option market microstructure

---

## Risk

- Requires accurate Greeks
- Works only on high options OI stocks
- Can be overwhelmed by fundamental news

---

*Trade the Greeks, not the direction.*
