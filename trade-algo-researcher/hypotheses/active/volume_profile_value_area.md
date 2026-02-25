# Hypothesis: Volume Profile Value Area Fade

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Futures / Equities  
**Direction:** Mean reversion  
**Horizon:** 1-3 days  
**Target Win Rate:** 58-62%

---

## Core Idea

Volume Profile shows where most trading occurred (Value Area High/Low). Price tends to revert to Value Area after tagging VAH/VAL extremes.

**Key Levels:**
- **POC (Point of Control):** Most volume traded (magnet)
- **VAH (Value Area High):** 70th percentile — resistance
- **VAL (Value Area Low):** 30th percentile — support
- **Extremes:** Tags of VAH/VAL predict reversion to POC

---

## Signal Construction

**Short Setup (VAH Rejection):**
```
Price touches or exceeds VAH
Volume declines on approach (no conviction)
Rejection candle (long wick at VAH)
Short, target POC
Stop above VAH + buffer
```

**Long Setup (VAL Bounce):**
```
Price touches or breaks below VAL
Volume declines on approach
Bounce candle (long wick at VAL)
Long, target POC
Stop below VAL - buffer
```

**Volume Profile Calculation:**
- 30-day lookback
- 1% price buckets
- 70% of volume = Value Area

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Avg Return | 1.5-3% per trade |
| Risk/Reward | 1:2 |
| Sharpe | 1.1-1.5 |

---

## Universe

Futures: /ES, /NQ, /CL, /GC
Stocks: High volume large-caps

---

## Data Requirements

- Tick data or 1-minute OHLC
- Volume at price calculation
- 30-day rolling volume profile
- Real-time VAH/VAL/POC levels

---

## Why It Works

1. **Market memory** — Traders remember where they transacted
2. **Fair value** — POC = perceived fair price
3. **Extremes are rare** — 30% of time outside VA
4. **Institutional reference** — Institutions use VP for entries

---

## Best Timeframes

- Intraday: 30-min to 4H charts
- Swing: Daily with monthly VP
- Works on all liquid markets

---

## Risk

- Trend days break through VAH/VAL
- POC shifts (volume migration)
- Requires real-time VP calculation

---

*Price returns to where the most business was done.*
