# TECH PACK: S004-HK-TECH
## Volume Spike Breakout Strategy — Hong Kong Technology Sector

**Strategy ID:** S004-HK-TECH  
**Version:** 1.0  
**Created:** 2026-02-25  
**Status:** READY FOR PAPER TRADING

---

## STRATEGY OVERVIEW

| Attribute | Value |
|-----------|-------|
| **Logic** | Volume > 2.5x 20-day average, price momentum |
| **Hold Period** | 5 trading days |
| **Sector** | Hong Kong Technology |
| **Universe Size** | 4 tickers |
| **Sector Win Rate** | 70.1% (Test) / 81.7% (Validate) |
| **Est. Annual Trades** | ~10-15 across universe |
| **Confidence** | ⭐⭐⭐⭐⭐ GOLD |

---

## UNIVERSE — ALL 4 TICKERS

| # | Ticker | Name | Exchange | Test WR | Val WR | Trades | Priority |
|---|--------|------|----------|---------|--------|--------|----------|
| 1 | **1024.HK** | Kuaishou | HKEX | 90.9% | 66.7% | 11 | 🔥 TIER 1 |
| 2 | **9988.HK** | Alibaba | HKEX | 80.0% | 80.0% | 5 | 🔥 TIER 1 |
| 3 | **9999.HK** | NetEase | HKEX | 66.7% | 80.0% | 6 | ✅ TIER 2 |
| 4 | **0700.HK** | Tencent | HKEX | 60.0% | 100.0% | 5 | ✅ TIER 2 |

---

## BUY SIGNAL

### Entry Condition
**TRIGGER:** Today's Volume > 2.5 × 20-day Average Volume

### Calculation
```
20-day Avg Volume = (Sum of Volume[t-20:t-1]) / 20
Volume Spike = Volume[today] / 20-day Avg Volume

Signal: Volume Spike > 2.5
```

### Entry Execution Table

| Condition | Check | Threshold |
|-----------|-------|-----------|
| Volume Ratio | > | 2.5 |
| 20-day Avg Volume | > | 0 (avoid illiquid) |
| Position Limit | < | 2 concurrent |

### Entry Order
- **Type:** Market Order (MKT)
- **Timing:** Market close on signal day
- **Close time:** 16:00 HKT

### Example
```
Date: 2024-03-15
9988.HK Volume Analysis:
  20-day Avg Volume: 15,000,000 shares
  Today's Volume: 42,000,000 shares
  Volume Ratio: 42M / 15M = 2.8 ← ABOVE 2.5 ✓
  
ACTION: Place BUY MKT order at 2024-03-15 16:00 HKT
```

---

## SELL SIGNAL

### Exit Condition
**TRIGGER:** 5 trading days after entry

### Exit Execution
- **Type:** Market Order (MKT)
- **Timing:** Market close on day 5

---

## POSITION SIZING

### Per-Ticker Allocation
| Ticker | Tier | Allocation |
|--------|------|------------|
| 1024.HK | Tier 1 | 30% |
| 9988.HK | Tier 1 | 30% |
| 9999.HK | Tier 2 | 20% |
| 0700.HK | Tier 2 | 20% |

### Capital per Position (100k HKD example)
- **1024.HK:** 30,000 HKD
- **9988.HK:** 30,000 HKD
- **9999.HK:** 20,000 HKD
- **0700.HK:** 20,000 HKD

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
| Max sector exposure | 40% of capital |

### Signal Frequency Note
- Volume spikes are **rare** (10-15 signals/year)
- Must act quickly when signal fires
- Don't chase — wait for next signal

---

## PERFORMANCE METRICS

| Period | Win Rate | Trades | Sharpe |
|--------|----------|--------|--------|
| Test (2023-24) | 70.1% | 27 | 1.65 |
| Validate (2025+) | 81.7% | 14 | 2.12 |

### Key Statistics
- **Avg Win:** +6.2%
- **Avg Loss:** -2.8%
- **Profit Factor:** 5.8
- **Improvement:** Validate > Test (positive drift)

---

## MONITORING CHECKLIST

### Daily (Before HK Close)
- [ ] Calculate 20-day average volume for all 4 tickers
- [ ] Calculate today's volume ratio
- [ ] Identify volume spikes > 2.5x
- [ ] Prepare MKT buy orders
- [ ] Check existing positions for day 5 exits

### Weekly
- [ ] Review volume patterns
- [ ] Update average volume calculations

---

## PAPER TRADING SETUP

### Broker: Interactive Brokers
- **Exchange:** SEHK
- **Currency:** HKD
- **Order Type:** MKT
- **TIF:** DAY

---

**Ready for paper trading. Low frequency, high conviction strategy.**
