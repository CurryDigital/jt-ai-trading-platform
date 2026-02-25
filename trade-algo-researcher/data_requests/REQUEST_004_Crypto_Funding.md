## DATA REQUEST - Crypto Funding Rates

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** 2026-02-20  
**Priority:** MEDIUM

---

### Data Required

**Table/Schema:** `gold.crypto_funding` (new table)  
**Columns:**
- `timestamp` (TIMESTAMP)
- `exchange` (VARCHAR) - 'Binance', 'Bybit', etc.
- `symbol` (VARCHAR) - 'BTCUSDT', 'ETHUSDT'
- `funding_rate` (NUMERIC) - 8-hour rate
- `predicted_rate` (NUMERIC) - next period prediction
- `mark_price` (NUMERIC)
- `index_price` (NUMERIC)

**Time Period:** 2020-01-01 to 2024-12-31  
**Frequency:** 8-hour (00:00, 08:00, 16:00 UTC)  
**Symbols:** BTC, ETH, major altcoins

---

### Purpose

Testing **Crypto Funding Rate Arbitrage hypothesis**:
- High funding = longs pay shorts = potential short signal
- Low/negative funding = shorts pay longs = potential long signal
- Capture funding rate yield

Previous attempt with **3-day price move proxy FAILED** (50% win rate) - proxy rejected.

---

### Blocking Status

☑️ **BLOCKING** - Proxy failed validation

Price moves do NOT capture funding rate pressure.

---

### Suggested Source

**Option 1:** Binance API (free)
- Endpoint: GET /fapi/v1/fundingRate
- Cost: FREE
- History: 2+ years
- Limitation: Need API key

**Option 2:** Bybit API (free)
- Endpoint: GET /v2/public/funding-rate
- Cost: FREE
- History: 2+ years

**Option 3:** CoinGlass (paid)
- Cost: $100-500/month
- Quality: Aggregated across exchanges
- History: 3+ years

**Option 4:** CryptoQuant (paid)
- Cost: $200-1000/month
- Quality: Good analytics
- History: 4+ years

---

### Acceptance Criteria

- [ ] 8-hour funding rates for 3+ years
- [ ] Major exchanges: Binance, Bybit, OKX
- [ ] BTC and ETH minimum
- [ ] Mark price and index price for calculations

---

### Recommendation

**Binance API** (FREE) - sufficient for validation.
- Register API key
- Historical funding data available
- Rate limits manageable

---

**Status:** AWAITING API KEY SETUP
