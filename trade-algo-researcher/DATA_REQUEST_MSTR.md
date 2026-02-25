# Data Request: Crypto Stocks for Bitcoin Proxy Testing
**Date:** 2026-02-22  
**From:** Trade Algo Researcher  
**To:** JT Trading Team  
**Priority:** High

---

## Purpose
Request Bitcoin-related stocks to test "whale" proxy hypothesis.

**Key Request:** MicroStrategy (MSTR) - holds 190,000+ BTC

---

## Why MSTR is Important

**MicroStrategy (MSTR)** is essentially a **Bitcoin proxy ETF:**
- Holds ~190,000 BTC (~$10B worth)
- Stock price highly correlated with BTC
- Often leads BTC price moves (institutional buying/selling)
- High volume = whale activity indicator

**Hypothesis:** MSTR price action can predict BTC moves

---

## Requested Tickers

| Ticker | Company | BTC Exposure | Priority |
|--------|---------|--------------|----------|
| **MSTR** | MicroStrategy | 190,000 BTC | **P1** |
| COIN | Coinbase | Exchange | P2 |
| MARA | Marathon Digital | Mining | P2 |
| RIOT | Riot Blockchain | Mining | P2 |
| HOOD | Robinhood | Exchange/App | P3 |

---

## Testable Hypotheses (Once Data Available)

### 1. MSTR as BTC Leading Indicator
```
If MSTR up >5% with volume >2x:
    Buy BTC next day
Expected: 55%+ win rate
```

### 2. MSTR Premium/Discount to NAV
```
Calculate MSTR implied BTC value vs actual BTC price:
If MSTR trades at discount >10% to NAV:
    Buy MSTR (arbitrage)
If MSTR trades at premium >15%:
    Sell MSTR, buy BTC
```

### 3. MSTR Volume Spike = BTC Whale Activity
```
If MSTR volume >3x average:
    Major institutional move likely
    Trade BTC in same direction
```

### 4. MSTR Earnings/News Impact on BTC
```
MSTR earnings announcements → BTC volatility
Trade BTC options/straddles around MSTR events
```

### 5. Mining Stocks (MARA, RIOT) as BTC Proxies
```
If MARA + RIOT both up >5%:
    BTC mining sector bullish
    Buy BTC
```

---

## Schema

```sql
-- Add to existing silver.historical_stock_data
-- Just need these tickers added to daily ingestion
```

**Fields needed:** Same as existing stocks
- date, ticker, open, high, low, close, volume

---

## Timeline

| Priority | Ticker | Timeline |
|----------|--------|----------|
| P1 | MSTR | 1 week |
| P2 | COIN, MARA, RIOT | 2 weeks |
| P3 | HOOD | 1 month |

---

## Alternative if MSTR Not Available

**Use BTC futures data:**
- BTC futures volume/spread
- Futures premium/discount to spot
- Can substitute for whale activity

**Or use on-chain data:**
- Whale wallet movements
- Exchange inflows/outflows
- Requires different data source

---

## Current Status

Tested with BTC-USD and ETH-USD only:
- ETH/BTC ratio: 55.2% win (moderate edge)
- BTC-ETH lead-lag: 53.3% win (weak edge)
- MSTR would significantly expand testing capability

---

## Contact

Questions? Contact Trade Algo Researcher.

---

*Requested: 2026-02-22*  
*Blocking: 5 MSTR-specific hypotheses*  
*Impact: High - enables whale proxy testing*