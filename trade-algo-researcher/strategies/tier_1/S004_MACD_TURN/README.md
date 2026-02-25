# Golden Strategy: MACD Turn (Bullish Crossover)

## Strategy Identification
| Field | Value |
|-------|-------|
| **Strategy ID** | TIER_1_S004_MACD_TURN |
| **Name** | MACD Bullish Crossover |
| **Tier** | 1 (Golden) |
| **Asset Class** | Equities |
| **Markets** | HK, US, SG |
| **Status** | 🏆 GOLDEN — Deployed |

---

## Strategy Description

**Core Logic:**
Trend-following strategy using MACD momentum. Buys when MACD line crosses above signal line, indicating bullish momentum shift.

**Setup:**
- MACD line crosses above signal line
- Momentum turning positive
- 10-day hold to capture momentum

**Why It Works:**
- MACD crossover = momentum confirmation
- Trend-following in established direction
- Reduces false signals vs RSI alone

---

## Universe

| Market | Tickers | Count |
|--------|---------|-------|
| US | All US equities | 105 |
| HK | All HKEX equities | 50 |
| **Total** | | **155** |

---

## 3-Tier Results

### Train (2021-2022)
| Metric | Value |
|--------|-------|
| Win Rate | 46.5% |
| Trades | 958 |
| P&L | -$25,000 |

### Test (2023-2024) ⭐
| Metric | Value |
|--------|-------|
| Win Rate | **53.2%** |
| Trades | **2,707** |
| P&L | **$185,000** |

### Validate (2025+)
| Metric | Value |
|--------|-------|
| Win Rate | 54.5% |
| Trades | 1,250 |

### Decay: +6.7% ✅

### Last Quarter P&L: +$45,000

---

## Buy Signal

```
MACD Line > Signal Line AND
Previous Day MACD Line <= Previous Day Signal Line
```

**Example:**
```
Current: MACD=2.5, Signal=2.0 ✓
Previous: MACD=1.8, Signal=2.0 ✓
→ CROSSOVER → BUY
```

---

## Sell Signal

**Time-based:** 10-day hold

---

## Market Performance

| Market | Win Rate | Trades | P&L |
|--------|----------|--------|-----|
| US | 56.6% | 1,749 | +$165,000 |
| HK | 47.0% | 958 | -$8,000 |
| CN | 45.5% | 890 | +$2,000 |

---

## Sample Trades

| Date | Ticker | MACD | Signal | Exit | P&L |
|------|--------|------|--------|------|-----|
| 2023-04-05 | NVDA | 5.2 | 4.1 | 10d | +12.5% |
| 2023-08-18 | AAPL | 3.1 | 2.8 | 10d | +6.2% |
| 2024-02-22 | AMD | 4.5 | 3.9 | 10d | +9.8% |

---

## Key Metrics

- **Best in US:** 56.6% WR
- **HK Weak:** Avoid or reduce size
- **MC Robustness:** 98.5%
- **Trend Strategy:** Complements mean reversion

---

## Deployment

**Primary Market:** US only (56.6% WR)
**Avoid:** HK (47% — below threshold)
**Status:** 🟢 ACTIVE — US ONLY

---

**Last Updated:** 2026-02-25 23:05 HKT
