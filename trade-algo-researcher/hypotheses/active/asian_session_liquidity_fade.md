# Hypothesis: Asian Session Liquidity Fade (FX)

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** FX  
**Direction:** Mean reversion  
**Horizon:** 4-8 hours (intraday)  
**Target Win Rate:** 58-62%

---

## Core Idea

Large moves during illiquid Asian session (Tokyo 00:00-09:00 GMT) often reverse during London/NY open as liquidity returns. Fade exaggerated Asian moves.

**The Edge:**
- Asian session = 20% of daily FX volume (illiquid)
- London open = 40% volume (liquid)
- Large moves in thin market = overshooting
- Mean reversion as London hedgers arrive

---

## Signal Construction

**Entry (London Open 08:00 GMT):**
```python
# Calculate Asian session range (00:00-08:00 GMT)
asian_high = max(price[00:00 to 08:00])
asian_low = min(price[00:00 to 08:00])
asian_range = asian_high - asian_low

# Calculate move from Asian open
asian_move = (price_at_08:00 - price_at_00:00) / price_at_00:00

IF abs(asian_move) > 0.5% (large Asian move):
    AND asian_range > 1.5 * ATR(20):
    
    IF asian_move > 0:
        # Large up move in Asia - fade it
        Short at London open
    ELSE:
        # Large down move in Asia - fade it
        Long at London open
        
    Exit: 4-8 hours later or when move retraces 50%
```

**Pairs:**
- USDJPY (most liquid Asian pair)
- AUDUSD (Australia/Asia correlation)
- NZDUSD (illiquid, more noise)
- EURJPY, GBPJPY (crosses)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Avg Return | 0.3-0.5% per trade |
| Sharpe | 1.0-1.3 |
| Trades/Month | 15-20 |

---

## Data Requirements

- **Intraday prices:** 15-min or 1-hour bars
- **Asian session data:** Tokyo hours
- **ATR:** For volatility normalization
- **Sources:** IBKR, Forex data providers

---

## Implementation

**Schedule:**
- Monitor: 00:00-08:00 GMT (Asian session)
- Entry: 08:00 GMT (London open)
- Exit: 12:00-16:00 GMT (NY morning)

**Risk:**
- Stop: 0.5% adverse move
- Size: 1-2% risk per trade
- Avoid: Major announcements during Asian session

---

## Academic Support

- Ito & Hashimoto (2006): Intraday seasonality in FX markets
- Breedon & Ranaldo (2013): Intraday patterns in FX returns
- Covrig & Melvin (2005): Tokyo insularity

---

*Fade the Tokyo drift.*
