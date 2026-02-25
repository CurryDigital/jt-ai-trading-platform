# Hypothesis: Commodity Crack Spread (Oil Refining)

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** Commodities (Energy)  
**Direction:** Long/Short (spread)  
**Horizon:** 1-3 months  
**Target Win Rate:** 55-65%

---

## Core Idea

Crack spread = difference between crude oil price and refined products (gasoline, heating oil). Represents refiner profit margin. Mean reverts around historical averages (~$10-15/bbl).

**The Edge:**
- Crack spreads mean revert seasonally
- Refinery maintenance creates supply squeezes
- Demand seasonal: gasoline (summer), heating oil (winter)
- Supply shocks (hurricanes, outages) create temporary dislocations

---

## Signal Construction

**3-2-1 Crack Spread:**
```python
# 3 barrels crude → 2 barrels gasoline + 1 barrel heating oil
crack_3_2_1 = (2 * gasoline_price + 1 * heating_oil_price) - 3 * crude_price
```

**Entry (Long Crack = Long margins):**
```python
IF crack_spread < historical_10th_percentile:
    # Margins compressed - expect recovery
    Long crack spread
    (Long products, short crude)
    
IF crack_spread > historical_90th_percentile:
    # Margins elevated - expect compression
    Short crack spread
    (Short products, long crude)
```

**Seasonal Boost:**
```python
# Summer: Gasoline demand peaks (driving season)
# Winter: Heating oil demand peaks
# Enter seasonal trades 4-6 weeks before peak
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 10-15% |
| Sharpe | 0.7-1.0 |
| Win Rate | 55-65% |
| Max DD | -20% |

---

## Data Requirements

- **Crude:** CL (WTI) or BZ (Brent) futures
- **Gasoline:** RB (RBOB) futures
- **Heating Oil:** HO futures
- **Natural Gas:** NG (for power generation correlation)

---

## Implementation

**Instruments:**
- Futures: CL, RB, HO (direct)
- ETFs: USO, UGA, UHN (simplified)
- Note: Roll yield important in contango/backwardation

**Sizing:**
- Equal dollar value crude vs products
- Margin requirements lower for spreads

---

## Academic Support

- Girma & Paulson (1999): Risk arbitrage opportunities in petroleum spreads
- Chng (2009): Economic linkages across commodity futures
- Maslyuk & Smyth (2009): Cointegration between oil and product prices

---

*Capture the refiner's margin cycle.*
