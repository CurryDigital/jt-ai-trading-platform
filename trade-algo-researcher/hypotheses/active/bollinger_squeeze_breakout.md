# Hypothesis: Bollinger Bands Squeeze + Breakout

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities / Crypto  
**Direction:** Long/Short (breakout direction)  
**Horizon:** 1-2 weeks  
**Target Win Rate:** 55-60%

---

## Core Idea

Low volatility periods (Bollinger Bands squeeze) predict high volatility expansion. Trade the breakout direction.

**The Setup:**
1. Bollinger Bands width < 6% (squeeze)
2. Price consolidates for 10+ days
3. Volume dries up
4. Breakout with volume expansion

**The Edge:**
- Volatility mean reverts
- Squeeze periods resolve with large moves
- Directional breakout captures expansion

---

## Signal Construction

**Squeeze Detection:**
```
BandWidth = (Upper - Lower) / Middle < 0.06
SqueezeCount = consecutive days of BandWidth < 0.06
```

**Entry (Long Breakout):**
```
IF BandWidth < 0.06 for 10+ days AND
   price closes above upper band AND
   volume > 1.5x average AND
   ADX > 25 (trend strength)
THEN long, stop below lower band
```

**Entry (Short Breakout):**
```
IF BandWidth < 0.06 for 10+ days AND
   price closes below lower band AND
   volume > 1.5x average AND
   ADX > 25
THEN short, stop above upper band
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 55-60% |
| Avg Win | 8-12% |
| Avg Loss | 4-6% |
| Sharpe | 1.0-1.4 |
| Success Rate | 40-50% hit profit target |

---

## Universe

Stocks with history of volatility expansion: Crypto, biotech, tech

---

## Data Requirements

- OHLC prices
- Bollinger Bands (20, 2)
- Bandwidth calculation
- ADX for trend confirmation
- Volume

---

## Why It Works

1. **Volatility clustering** — Low vol → high vol
2. **Coiled spring** — Consolidation builds energy
3. **Breakout psychology** — FOMO after breakout
4. **Risk-defined** — Stop at opposite band

---

## Famous Examples

- **TSLA:** Multiple 20%+ moves after squeezes
- **BTC:** Breakouts after weeks of consolidation
- **Meme stocks:** GME squeeze pattern

---

## Risk

- False breakout (whipsaw)
- Breaks opposite direction first
- Requires patience (squeezes can extend)

---

*The squeeze always resolves. Position before the explosion.*
