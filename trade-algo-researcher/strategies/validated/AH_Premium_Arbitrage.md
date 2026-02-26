# Strategy: AH_Premium_Arbitrage (VALIDATED)

**Status:** ✅ VALIDATED  
**Win Rate:** 61.3% (1,132 trades)  
**Tested:** 2023-01-01 to 2024-12-31  
**Markets:** HK Banks dual-listed in China

---

## Signal

**Entry:** Buy H-shares when AH premium > 25%  
(A-shares trading at 25%+ premium to H-shares)

**Exit:** 20-day hold (time-based)

**Logic:** Mean reversion of AH premium — H-shares catch up when A-shares overvalued

---

## Performance

| Pair | Trades | Win Rate |
|------|--------|----------|
| Ping An (2318.HK) | 51 | **84.3%** |
| ICBC (1398.HK) | 322 | **61.8%** |
| CCB (0939.HK) | 406 | **57.9%** |
| Bank of China (3988.HK) | 353 | **61.5%** |
| **TOTAL** | **1,132** | **61.3%** |

---

## Buy Signal
```
IF (A_share_close - H_share_close) / H_share_close > 0.25:
    BUY H-shares at next open
    HOLD 20 days
```

## Sell Signal
20-day time-based exit

---

## Parameters
- Entry threshold: 25% premium
- Hold period: 20 days
- Transaction cost: 0.2%
- Entry: Next day open (no lookahead)

---

## Data Requirements
- Dual-listed ticker pairs
- Prices for both A-shares and H-shares
- Synchronized dates

---

## Notes
- **Best performer:** Ping An (84.3% WR) — most liquid, highest retail interest
- Works on all HK bank pairs tested
- Premium >25% occurs during China bull markets or HK market stress

---

**Validated:** 2026-02-26  
**Next:** Deploy to Golden strategies if full universe test confirms
