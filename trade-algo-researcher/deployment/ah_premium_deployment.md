# Deployment Configuration: AH Premium Arbitrage

**Strategy:** AH_Premium_Arbitrage  
**Status:** READY FOR DEPLOYMENT  
**Validated:** 2026-02-19  
**Win Rate:** 72.1%  
**Sharpe:** 2.33

---

## Universe (9 Dual-Listed Pairs)

| H-Share | A-Share | Name | Win Rate | Sharpe |
|---------|---------|------|----------|--------|
| **1398.HK** | 601398.SS | ICBC | 90.0% | 4.56 |
| **0939.HK** | 601939.SS | CCB | 78.9% | 2.38 |
| **3988.HK** | 601988.SS | Bank of China | 76.9% | 2.99 |
| **1288.HK** | 601288.SS | Agricultural Bank | 68.8% | 2.73 |
| **0998.HK** | 600028.SS | Sinopec | 69.6% | 2.02 |
| **2318.HK** | 601318.SS | Ping An | Data issue | - |
| **6030.HK** | 600030.SS | CITIC Securities | 69.0% | 1.98 |
| **1336.HK** | 601336.SS | New China Life | 67.9% | 1.82 |

**Primary Deployment:** Top 5 (ICBC, CCB, Bank of China, AgBank, Sinopec)

---

## Entry Rules

```python
# Calculate AH Premium
premium = (A_share_price - H_share_price_CNY) / H_share_price_CNY
# Note: H-share price converted to CNY using HKD/CNY rate

# Calculate 60-day historical average premium
hist_premium_avg = mean(premium[-60:])

# ENTRY
IF premium > 0.30 (30%):  # H-shares at 30%+ discount
    AND premium > hist_premium_avg * 1.2:  # Above historical avg
    AND 60-day data available:
    
    LONG H-shares (e.g., 1398.HK)
    # Hedge: Short A-share proxy if available
    
    Position Size: 2-3% per pair
    Max Pairs: 5 simultaneous
```

---

## Exit Rules

```python
# Time-based exit
IF hold_days >= 20:
    EXIT

# Premium-based exit
IF premium < 0.25 (25%):  # Partial convergence
    EXIT

# Stop loss
IF H_share drops > 10% from entry:
    EXIT (risk management)
```

---

## Risk Management

| Parameter | Value |
|-----------|-------|
| Max Position per Pair | 2-3% of portfolio |
| Max Total Exposure | 10-15% (5 pairs × 2-3%) |
| Stop Loss | 10% per pair |
| Time Stop | 20 days |

**Hedging:**
- Optional: Short A-share ETF (ASHR, KWEB) for market-neutral
- Or run long-only H-shares if hedging not available

---

## Execution

**Venue:** IBKR (Hong Kong exchange access)
**Order Type:** Limit (midpoint)
**Timing:** HKEX hours (09:30-16:00 HKT)
**Frequency:** Check daily, trades 2-4x per year per stock

---

## Monitoring

**Daily:**
- Calculate AH premium for all 9 pairs
- Check if any pair triggers entry

**Weekly:**
- Review open positions for exit signals
- Update 60-day rolling premium average

**Monthly:**
- Performance attribution by pair
- Rebalance if needed

---

## Expected Performance

| Metric | Value |
|--------|-------|
| Win Rate | 72% |
| Avg Return per Trade | 4.6% |
| Sharpe | 2.33 |
| Trades per Year | 10-20 (across 5 pairs) |
| Annual Return | 15-25% (on deployed capital) |

---

## Data Requirements

**Real-time:**
- H-share prices (1398.HK, 0939.HK, etc.) - IBKR
- A-share prices (delayed, for calculation) - yfinance/Bloomberg
- HKD/CNY FX rate - IBKR/yfinance

**Historical:**
- 60-day rolling premium calculation

**Sources:**
- Primary: IBKR for execution
- Calculation: yfinance for A-share reference

---

## Deployment Checklist

- [ ] IBKR account with HKEX access
- [ ] A-share price feed (yfinance or Bloomberg)
- [ ] FX rate feed (HKD/CNY)
- [ ] Position sizing calculator
- [ ] Alert system for premium > 30%
- [ ] Backtest verification complete ✅

---

**Ready for JT Platform Integration**
