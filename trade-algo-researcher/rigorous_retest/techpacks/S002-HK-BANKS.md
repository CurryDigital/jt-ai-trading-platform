# TECH PACK: S002-HK-BANKS
## 3-Day Panic Reversal Strategy — Hong Kong Banking Sector

**Strategy ID:** S002-HK-BANKS  
**Version:** 1.0  
**Created:** 2026-02-25  
**Status:** READY FOR PAPER TRADING

---

## STRATEGY OVERVIEW

| Attribute | Value |
|-----------|-------|
| **Logic** | 3 consecutive down days → buy Day 3 close |
| **Hold Period** | 5 trading days |
| **Sector** | Hong Kong Banking |
| **Universe Size** | 4 tickers |
| **Sector Win Rate** | 61.3% (Test) / 74.5% (Validate) |
| **Est. Annual Trades** | ~20-30 across universe |
| **Confidence** | ⭐⭐⭐⭐ VALIDATED |

---

## UNIVERSE — ALL 4 TICKERS

| # | Ticker | Name | Exchange | Test WR | Val WR | Trades | Priority |
|---|--------|------|----------|---------|--------|--------|----------|
| 1 | **0005.HK** | HSBC Holdings | HKEX | 67.6% | 73.7% | 34 | ✅ TIER 1 |
| 2 | **3328.HK** | Bank of Communications | HKEX | 62.5% | 81.8% | 40 | ✅ TIER 1 |
| 3 | **3988.HK** | Bank of China | HKEX | 58.8% | 52.9% | 34 | ✅ TIER 2 |
| 4 | **0939.HK** | CCB | HKEX | 56.1% | 90.0% | 41 | ✅ TIER 2 |

---

## BUY SIGNAL

### Entry Condition
**TRIGGER:** 3 consecutive down days

### Calculation
```
Day 1: Close[t-2] > Close[t-1] (down day)
Day 2: Close[t-1] > Close[t] (down day)
Day 3: Close[t] > Close[t+1 expected] (current day down)

Signal confirmed at: Close[t] (end of Day 3)
```

### Entry Execution Table

| Condition | Check |
|-----------|-------|
| Close[t-2] > Close[t-1] | ✓ |
| Close[t-1] > Close[t] | ✓ |
| Today is Day 3 down | ✓ |
| Entry at close | ✓ |

### Entry Order
- **Type:** Market Order (MKT)
- **Timing:** Market close on Day 3
- **Close time:** 16:00 HKT

### Example
```
Date: 2024-03-15 (Friday)
1398.HK Price History:
  Mar 12: $4.50
  Mar 13: $4.40 ↓ (down)
  Mar 14: $4.30 ↓ (down)
  Mar 15: $4.20 ↓ (down) ← 3rd consecutive down day ✓
  
ACTION: Place BUY MKT order at 2024-03-15 16:00 HKT
```

---

## SELL SIGNAL

### Exit Condition
**TRIGGER:** 5 trading days after entry

### Exit Execution
- **Type:** Market Order (MKT)
- **Timing:** Market close on day 5

### Example
```
Entry: 2024-03-15 (Friday)
Exit: 2024-03-22 (Friday, 5 trading days)
Action: SELL at 16:00 HKT on exit day
```

---

## POSITION SIZING

### Equal Weight Allocation
| Ticker | Allocation |
|--------|------------|
| 0005.HK | 25% |
| 3328.HK | 25% |
| 3988.HK | 25% |
| 0939.HK | 25% |

### Capital per Position (100k HKD example)
- **Each ticker:** 25,000 HKD

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
| Max sector exposure | 50% of capital |

### No Stop Loss
- Time-based exit only
- Accept drawdown during hold period

---

## PERFORMANCE METRICS

| Period | Win Rate | Trades | Sharpe |
|--------|----------|--------|--------|
| Test (2023-24) | 61.3% | 149 | 0.95 |
| Validate (2025+) | 74.5% | 76 | 1.42 |

### Key Statistics
- **Avg Win:** +2.8%
- **Avg Loss:** -1.9%
- **Profit Factor:** 2.1

---

## MONITORING CHECKLIST

### Daily (Before HK Close)
- [ ] Check for 3 consecutive down days in each ticker
- [ ] Count down days: Close[t-2] > Close[t-1] > Close[t]
- [ ] Prepare MKT buy orders at close
- [ ] Check existing positions for day 5 exits

---

## PAPER TRADING SETUP

### Broker: Interactive Brokers
- **Exchange:** SEHK
- **Currency:** HKD
- **Order Type:** MKT
- **TIF:** DAY

---

**Ready for paper trading. Complements S001-HK-BANKS well.**
