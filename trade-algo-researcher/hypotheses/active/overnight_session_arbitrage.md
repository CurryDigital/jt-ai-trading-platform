# Hypothesis: Overnight Session Arbitrage (Tokyo → London → NY)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** FX / Crypto  
**Direction:** Momentum continuation or mean reversion  
**Horizon:** 4-12 hours  
**Target Win Rate:** 60-65%

---

## Core Idea

Price moves in one session predict the next session's direction due to:
- Information diffusion across time zones
- Liquidity differences (Tokyo thin, London thick, NY thickest)
- Market structure differences (retail vs institutional dominance)

**The Edge:**
- Tokyo move >1% → London continues direction 65% of time
- But if Tokyo move >2% → London reverses (profit taking)
- Critical thresholds vary by pair

---

## Session Characteristics

| Session | Hours ET | Liquidity | Dominant Flow |
|---------|----------|-----------|---------------|
| Tokyo | 19:00-04:00 | Low | Japanese retail, exporters |
| London | 03:00-12:00 | High | European banks, real money |
| NY | 08:00-17:00 | Highest | US institutions, hedge funds |

---

## Signal Construction

**Tokyo → London Continuation:**
```
IF Tokyo_return > 0.8% AND < 2.0% AND
   No London macro news AND
   VIX < 20
THEN long into London open
```

**Tokyo → London Reversal:**
```
IF Tokyo_return > 2.5% OR < -2.5% AND
   Move > 2*ATR
THEN fade the move (reverse)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 0.5-1.0% per trade |
| Sharpe | 1.2-1.8 |
| Best Pairs | USDJPY, EURUSD, GBPUSD |

---

## Data Requirements

- Hourly FX prices by session
- Session volume profiles
- ATR (average true range)
- Economic calendar (macro news filter)

---

## Why It Works

1. **Liquidity cascade** — Tokyo sets direction, London confirms, NY amplifies
2. **Information asymmetry** — News breaks in Asia, fully digested by NY
3. **Flow patterns** — Japanese exporters hedge, Europeans position, US reacts
4. **Retail vs institutional** — Retail active Tokyo, institutions NY

---

## Risk

- Macro surprises in London/NY sessions
- Thin liquidity in Tokyo (whipsaws)
- Requires 24-hour monitoring

---

*Trade the sun — follow daylight around the globe.*
