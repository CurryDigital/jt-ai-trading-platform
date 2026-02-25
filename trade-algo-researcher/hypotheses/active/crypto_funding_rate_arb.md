# Hypothesis: Crypto Funding Rate Arbitrage

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** Crypto  
**Direction:** Neutral (yield)  
**Horizon:** 1-7 days  
**Target Win Rate:** 70-80%

---

## Core Idea

Perpetual futures funding rates adjust to keep perp price aligned with spot. When funding is positive (longs pay shorts), shorts collect yield. Mean reversion of funding rates creates systematic income.

**The Edge:**
- Funding rates mean revert to ~0.01% per 8 hours (baseline)
- Positive funding 60-70% of time (bull markets)
- Can hedge delta-neutral (short perp + long spot)
- Exchanges pay funding every 8 hours

---

## Signal Construction

**Entry:**
```python
IF funding_rate_8h > 0.03% (10 bps above baseline):
    # Longs paying high premium - collect as short
    Short perp futures
    Long spot (delta neutral)
    
    Collect funding every 8 hours
    Exit when funding < 0.01%
```

**Enhanced Filter:**
```python
# Higher conviction when:
- Funding elevated >3 consecutive periods
- Perp premium to spot >0.5%
- Open interest elevated (crowded long)
- Funding rate > 90th percentile (30-day)
```

**Risk Management:**
- Close if funding turns negative (start paying)
- Funding can spike during squeeze (unlimited loss on short)
- Use stop if funding < -0.05% (paying too much)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Yield | 15-25% |
| Win Rate | 70-80% (funding collection) |
| Max DD | -10% (squeeze risk) |
| Sharpe | 1.5-2.5 |

---

## Data Requirements

- **Funding rates:** Binance, Bybit, OKX APIs (real-time)
- **Spot prices:** Coinbase, Binance
- **Perp prices:** Exchange APIs
- **OI data:** For crowdedness detection

---

## Implementation

**Execution:**
- Short perp on Binance (highest volume)
- Long spot on Coinbase (regulated, insured)
- Size: 10-20% of capital (leverage <2x)
- Rebalance if delta drifts >5%

**Exchanges:**
- Binance (best liquidity)
- Bybit (competitive funding)
- dYdX (decentralized option)

---

## Academic Support

- Makarov & Schoar (2020): Trading and arbitrage in cryptocurrency markets
- Lehar & Parlour (2020): Miner collusion
- Auer (2022): DEXs and CEXs

---

*Harvest the perpetual premium.*
