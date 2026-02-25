# Hypothesis: Doji at Support/Resistance

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities / FX  
**Direction:** Breakout direction  
**Horizon:** 1-3 days  
**Target Win Rate:** 55-60%

---

## Core Idea

Doji (open = close, small body) at support/resistance indicates indecision. Breakout from doji predicts direction of next move.

**The Setup:**
- Price approaches key S/R level
- Forms doji (indecision)
- Next candle breaks doji high/low
- Trade breakout direction

---

## Signal Construction

**Long Breakout:**
```
Price at support (20-day low, round number, prior low)
Doji forms (body < 10% of range)
Next candle closes above doji high
Volume > 1.2x average on breakout
Long, stop below doji low
```

**Short Breakout:**
```
Price at resistance (20-day high, round number, prior high)
Doji forms
Next candle closes below doji low
Volume > 1.2x average
Short, stop above doji high
```

**Doji Types (strongest to weakest):**
1. Dragonfly Doji (long lower shadow) — bullish
2. Gravestone Doji (long upper shadow) — bearish
3. Long-Legged Doji — high indecision
4. Standard Doji — neutral

---

## Expected Performance

| Metric | Doji Alone | At S/R | + Volume |
|--------|-----------|--------|----------|
| Win Rate | 51% | 56% | 60% |
| Sharpe | 0.4 | 0.7 | 0.9 |

---

## Universe

Any liquid market with clear S/R

---

## Data Requirements

- OHLC prices
- Doji detection (body/range ratio)
- Support/resistance levels
- Volume

---

## Why It Works

1. **Indecision resolution** — Doji = battleground, breakout = winner
2. **S/R significance** — Key levels attract attention
3. **Risk-defined** — Stop at doji extreme
4. **Universal pattern** — Works across all markets

---

## Best Conditions

- Clear trend (doji = pause)
- At key S/R (psychological levels)
- Low volatility before (calm before storm)
- Volume expansion on breakout

---

## Risk

- False breakout (whipsaw)
- Doji in middle of range (no edge)
- Requires next-day confirmation

---

*Indecision at key levels resolves with explosive moves.*
