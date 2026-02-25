# EXIT STRATEGY RECOMMENDATIONS - OFFICIAL
**Date:** 2026-02-23  
**Based on:** Exit optimization testing across all strategies

---

## 🎯 KEY FINDINGS FROM EXIT TESTING

### Profit Target vs Time Exit Trade-Off

| Exit Method | Win Rate Impact | Sharpe Impact | Best For |
|-------------|-----------------|---------------|----------|
| **Profit Target 3%** | **+9.9%** | -0.50 to -1.00 | Pushing to 55%/70% threshold |
| Profit Target 5% | +4.3% | -0.20 to -0.50 | Balanced approach |
| **Time Exit (10d)** | Baseline | **Best** | Preserving Sharpe |
| Trailing Stop -3% | **-11.2%** | -0.20 | ❌ **NEVER USE** |
| Stop Loss -10% | -0.3% to -3% | Mixed | Risk capping (test first) |

### Key Insight
**Profit targets increase win rate BUT hurt Sharpe** (cap upside on winners)

---

## ✅ OFFICIAL EXIT STRATEGY BY TIER

### TIER 1: Golden Strategies (70%+) - KEEP TIME EXITS
**Rationale:** Already successful, preserve high Sharpe

| # | Strategy | Win% | Recommended Exit | Hold | Notes |
|---|----------|------|------------------|------|-------|
| 1 | **BB+Monday GOLD** | 78.5% | **Time 10d OR +4% PT** | 10d | Already Golden - don't change |
| 2 | Inside Day Breakout | 74.4% | **+5% PT or 5d** | 5d | Original config works |
| 3 | RSI Mean Reversion | 72.6% | **+4% PT or 10d** | 10d | Best Sharpe (2.26) |
| 4 | Volume Breakout | 70.8% | **+5% PT or 10d** | 10d | Original config works |

---

### TIER 2: Near-Golden (60-70%) - USE PROFIT TARGET 3%
**Rationale:** Push over 70% threshold, accept lower Sharpe

| # | Strategy | Win% | Recommended Exit | Expected Win% | Notes |
|---|----------|------|------------------|---------------|-------|
| 5 | 3-Day + RSI + Volume | 68.4% | **+3% PT or 10d** | ~78% | Push to Golden |
| 6 | Range + Vol + RSI | 68.2% | **+3% PT or 10d** | ~78% | Push to Golden |
| 7 | BB Lower + RSI<15 | 61.8% | **+3% PT or 10d** | ~72% | Push to Golden |
| 8 | 3-Ind Combo | 62.9% | **+3% PT or 10d** | ~73% | Push to Golden |
| 9 | ATR Contraction | 61.1% | **+3% PT or 10d** | ~71% | Push to Golden |

---

### TIER 3: Validated (55-60%) - KEEP AS-IS OR PT 5%
**Rationale:** Already at threshold, minor optimization only

| # | Strategy | Win% | Recommended Exit | Notes |
|---|----------|------|------------------|-------|
| 10 | Monday RSI Extreme | 59.5% | **Time 10d OR +4% PT** | Already good |
| 11 | Month-End RSI | 58.8% | **Time 10d OR +4% PT** | Already good |
| 12 | Turn of Month RSI | 57.2% | **Time 10d OR +4% PT** | Already good |
| 13 | BB Squeeze + RSI | 57.7% | **Time 10d OR +4% PT** | Already good |
| 14 | BB %B Extreme | 56.7% | **Time 10d OR +4% PT** | Already good |
| 15 | Volume at Support | 56.7% | **Time 10d OR +4% PT** | Already good |
| 16 | Friday Volume BO | 56.3% | **+5% PT or 5d** | Breakout style |
| 17 | Tuesday RSI | 56.4% | **Time 10d OR +4% PT** | Mean reversion |
| 18 | Quarter-Start RSI | 55.3% | **Time 10d OR +4% PT** | Already good |
| 19 | Month-End Volume BO | 61.9% | **+5% PT or 5d** | Breakout style |
| 20 | Stoch + RSI Extreme | 56.3% | **Time 10d OR +4% PT** | Already good |

---

## 🚨 UNIVERSAL RULES

### ❌ NEVER USE
- **Trailing stops** - destroy win rate (-11.2%)
- **Tight stops (-3% to -5%)** - exit on noise

### ⚠️ TEST FIRST (Paper Trading)
- **10% stop loss** - 7-17% hit rate, mixed results
- Use position sizing (2% max) instead of stops

### ✅ ALWAYS USE
- **Profit targets** for strategies needing +5-10% win rate boost
- **Time exits** for already-successful strategies (preserve Sharpe)
- **Sector-specific deployment** (HK for BB+Monday = 88.9% win)

---

## 📊 SECTOR-SPECIFIC EXIT ADJUSTMENTS

### Hong Kong (HK) - BEST PERFORMANCE
- **BB+Monday**: 88.9% win - **DON'T change exit**
- **RSI MR**: 59.8% win - Use **+3% PT** to push to 70%+

### US Tech
- **Volume Breakout**: 70.8% win - Keep as-is
- **Inside Day**: 74.4% win - Keep as-is

### China A-Shares
- **RSI MR**: 51.3% win - **Avoid this sector** for mean reversion

---

## 🎯 QUICK REFERENCE: EXIT BY STRATEGY TYPE

| Strategy Type | Recommended Exit | Rationale |
|---------------|------------------|-----------|
| **Mean Reversion (RSI-based)** | +3-4% PT or 10d | Quick bounce, capture mean reversion |
| **Breakout (Volume-based)** | +5% PT or 5-10d | Momentum continuation |
| **Time-based (Monday/Month-End)** | Time 10d OR +4% PT | Time edge is key, don't cap too early |
| **Golden (70%+)** | Time exit preferred | Preserve Sharpe, already successful |
| **Near-Golden (60-70%)** | +3% PT | Push to Golden status |

---

## 🔧 SQL EXIT IMPLEMENTATION

### Profit Target 3% Exit
```sql
-- Calculate target exit price
SELECT 
    date,
    ticker,
    close as entry_price,
    close * 1.03 as profit_target_3pct,
    close * 0.90 as stop_loss_10pct  -- Optional
FROM signals
WHERE strategy = 'RSI_MR';
```

### Time-Based Exit
```sql
-- Calculate exit date (10 days later)
SELECT 
    entry_date,
    ticker,
    entry_date + INTERVAL '10 days' as exit_date
FROM signals;
```

---

## 📋 DEPLOYMENT CHECKLIST

### Before Deploying Each Strategy:
- [ ] Confirm exit method matches tier recommendation
- [ ] Set profit target level (+3%, +4%, or +5%)
- [ ] Set max hold period (5d or 10d)
- [ ] Configure sector filters (HK only for BB+Monday)
- [ ] Test in paper trading for 2-4 weeks

### Monitor in Production:
- [ ] Actual win rate vs backtest
- [ ] Profit target hit rate (% of trades)
- [ ] Time exit hit rate (% of trades)
- [ ] Average hold time
- [ ] Sharpe ratio

---

*Document: EXIT_STRATEGY_RECOMMENDATIONS.md*  
*Updated: 2026-02-23*  
*Applies to: All 20 validated strategies*