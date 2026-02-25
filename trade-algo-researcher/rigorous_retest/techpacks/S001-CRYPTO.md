# TECH PACK: S001-CRYPTO
## RSI Mean Reversion Strategy — Cryptocurrency Sector

**Strategy ID:** S001-CRYPTO  
**Version:** 1.0  
**Created:** 2026-02-25  
**Status:** READY FOR PAPER TRADING

---

## STRATEGY OVERVIEW

| Attribute | Value |
|-----------|-------|
| **Logic** | RSI(14) < 25 (extreme oversold), mean reversion |
| **Hold Period** | 10 trading days |
| **Sector** | Cryptocurrency |
| **Universe Size** | 4 tickers |
| **Sector Win Rate** | 74.3% (Test) / 58.9% (Validate) |
| **Est. Annual Trades** | ~25-40 across universe |
| **Confidence** | ⭐⭐⭐⭐ VALIDATED |
| **Decay Note** | Higher decay (Validate < Test) — monitor closely |

---

## UNIVERSE — ALL 4 TICKERS

| # | Ticker | Name | Exchange | Test WR | Val WR | Trades | Priority |
|---|--------|------|----------|---------|--------|--------|----------|
| 1 | **SOL-USD** | Solana | Crypto | 84.6% | 50.0% | 26 | ✅ TIER 1 |
| 2 | **ADA-USD** | Cardano | Crypto | 74.5% | 69.7% | 47 | ✅ TIER 1 |
| 3 | **MSTR** | MicroStrategy | NASDAQ | 66.7% | 52.6% | 21 | ✅ TIER 2 |
| 4 | **DOT-USD** | Polkadot | Crypto | 62.7% | 51.0% | 59 | ✅ TIER 2 |

---

## BUY SIGNAL

### Entry Condition
**TRIGGER:** RSI(14) < 25.0

### Entry Execution Table

| Condition | Check | Threshold |
|-----------|-------|-----------|
| RSI(14) | < | 25.0 |
| Market Status | = | Open |
| Position Limit | < | 2 concurrent |

### Entry Order
- **Crypto (SOL, ADA, DOT):** Market Order via crypto exchange
- **MSTR (stock proxy):** Market Order via IBKR
- **Timing:** Next market open after signal

### Example
```
Date: 2024-03-15
Ticker: SOL-USD
Price: $145.20
RSI(14): 21.5 ← BELOW 25 ✓
ACTION: Place BUY MKT order at next open
```

---

## SELL SIGNAL

### Exit Condition
**TRIGGER:** 10 trading days after entry

### Exit Execution
- **Type:** Market Order (MKT)
- **Timing:** Market close on day 10

---

## POSITION SIZING

### Per-Ticker Allocation
| Ticker | Tier | Allocation |
|--------|------|------------|
| SOL-USD | Tier 1 | 30% |
| ADA-USD | Tier 1 | 30% |
| MSTR | Tier 2 | 20% |
| DOT-USD | Tier 2 | 20% |

### Capital per Position (100k HKD example)
- **SOL-USD:** 30,000 HKD (~3,800 USD)
- **ADA-USD:** 30,000 HKD (~3,800 USD)
- **MSTR:** 20,000 HKD (~2,500 USD)
- **DOT-USD:** 20,000 HKD (~2,500 USD)

### Maximum Concurrent Positions
- **Per Strategy:** 2 positions maximum
- **Per Ticker:** 1 position only

---

## RISK MANAGEMENT

### Position Limits
| Limit | Value |
|-------|-------|
| Max positions | 2 concurrent |
| Max per ticker | 1 position |
| Max sector exposure | 30% of capital |
| **Decay Alert** | Validate (59%) < Test (74%) |

### High Volatility Warning
- Crypto sector has 2-3x volatility of equities
- Wider daily swings expected
- Position size accordingly (smaller than equities)

---

## PERFORMANCE METRICS

| Period | Win Rate | Trades | Sharpe |
|--------|----------|--------|--------|
| Test (2023-24) | 74.3% | 153 | 1.12 |
| Validate (2025+) | 58.9% | 78 | 0.68 |

### Decay Analysis
- **Test → Validate:** -15.4% decay
- **Status:** ⚠️ HIGH DECAY — reduce position sizes
- **Action:** Monitor first 20 paper trades closely

---

## MONITORING CHECKLIST

### Daily
- [ ] Calculate RSI(14) for all 4 tickers
- [ ] Check for RSI < 25 signals
- [ ] Monitor existing positions

### Weekly
- [ ] Review decay metrics
- [ ] Compare live vs backtest performance

---

## PAPER TRADING SETUP

### Crypto Exchanges
- **SOL, ADA, DOT:** Binance / Coinbase Pro
- **Order Type:** Market

### Stock Proxy
- **MSTR:** IBKR (NASDAQ)

---

**⚠️ HIGH DECAY WARNING: Reduce position sizes 25% vs other sectors.**
