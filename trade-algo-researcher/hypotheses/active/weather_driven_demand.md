# Hypothesis: Weather-Driven Demand (Agriculture/Energy)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Commodities  
**Direction:** Long/Short weather shocks  
**Horizon:** 1-4 weeks  
**Target Win Rate:** 60-65%

---

## Core Idea

Weather shocks create predictable demand/supply imbalances. Market underreacts to NOAA forecasts by 2-5 days (takes time to adjust positions).

**The Edge:**
- NOAA forecasts lead weather by 7-14 days
- Market prices in gradually
- Trading lag = alpha

---

## Weather → Commodity Links

| Weather Event | Commodity | Direction |
|--------------|-----------|-----------|
| Drought (Corn Belt) | Corn (ZC) | Long |
| Cold snap (Winter) | Natural Gas (NG) | Long |
| Heat wave (Summer) | Power/Coal | Long |
| Hurricane (Gulf) | Oil (CL) | Long |
| Early freeze (Brazil) | Coffee (KC) | Long |
| El Niño forecast | Ag complex | Long/Short mix |

---

## Signal Construction

**NOAA Forecast Signal:**
```
IF NOAA 14-day forecast shows:
   - Temperature >2σ from normal AND
   - Confidence >70% AND
   - Market hasn't moved >3%
THEN:
   - Long heating commodities if cold
   - Long cooling commodities if hot
   - Hold until forecast changes
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 5-10% per trade |
| Sharpe | 0.8-1.3 |
| Season | Best in summer/winter extremes |

---

## Data Requirements

- NOAA forecasts (free API)
- Degree day calculations
- Commodity futures prices
- Historical weather sensitivity

---

## Why It Works

1. **Predictable weather** — NOAA skill 7-14 days
2. **Slow institutional adjustment** — Large positions take time
3. **Forced demand** — People need AC/heat regardless of price
4. **Supply inelastic** — Can't quickly grow more corn/gas

---

## Risk

- Forecast errors (weather unpredictable)
- Position limits in futures
- Storage capacity surprises

---

*Trade the forecast before the storm.*
