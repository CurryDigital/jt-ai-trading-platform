# Strategy: Bollinger Bands Mean Reversion

## Current Status
- **Status:** 🧪 TESTING
- **Sharpe:** 0.98 (Tech), 0.68 (Equity)
- **Win Rate:** 67.0% (Tech), 64.3% (Equity)
- **Last Tested:** 2026-02-21
- **Target:** Sharpe >= 1.0, reduce drawdown

## Base Strategy
### Signal
- **Entry:** Price < Lower Band (20-day, 2.0σ)
- **Exit:** When price returns to SMA
- **Stop Loss:** Not implemented

### Parameters
```python
{
    'period': 20,
    'std_dev': 2.0
}
```

## Test History

### Test 1: 2026-02-21 - Tech Sector
- Universe: 28 Tech tickers
- Period: 2022-2024
- Trades: 882
- Results: Sharpe 0.98, Win 67.0%, MaxDD -90%
- Conclusion: 🧪 STRONG win rate, but catastrophic drawdown

### Test 2: 2026-02-21 - Equity Sector
- Universe: 30 Equity tickers
- Period: 2022-2024
- Trades: 1,106
- Results: Sharpe 0.68, Win 64.3%, MaxDD -98%
- Conclusion: 🧪 High win rate, but R:R poor

## Key Problem: R:R Ratio
- Avg Winner: ~6-7%
- Avg Loser: ~-8%
- **Problem:** Losers bigger than winners!

## Enhancement Ideas (Prioritized)

### HIGH PRIORITY
- [ ] **Add stop loss at -5%** - Cap drawdown from -90% to manageable
  - Expected: Sharpe may drop but risk-adjusted return improves
  
- [ ] **Trailing profit target** - Take profit at +5% instead of waiting for SMA
  - Expected: Improve R:R ratio
  
- [ ] **Tighter bands (1.5σ)** - More trades, earlier entry
  - Expected: Better entry timing

### MEDIUM PRIORITY
- [ ] **Wider bands (2.5σ)** - Only extreme oversold
  - Expected: Higher quality but fewer trades
  
- [ ] **Longer period (30-day)** - Slower but more reliable
  - Expected: Reduce false signals

### LOW PRIORITY
- [ ] **Volume filter** - Only trade on above-average volume
- [ ] **Trend filter** - Only trade in direction of 50-day MA

## Enhancement Tests to Run

### Test 3: Stop Loss at -5%
```python
# Add stop loss:
if (entry_price - current_price) / entry_price > 0.05:
    exit = stop_loss
```
- Expected: Sharpe ~0.8, but MaxDD ~-20% (acceptable)

### Test 4: Profit Target at +5%
```python
# Instead of waiting for SMA:
if (current_price - entry_price) / entry_price > 0.05:
    exit = take_profit
```
- Expected: Better R:R ratio

### Test 5: Tighter Bands (1.5σ)
```python
params = {'period': 20, 'std_dev': 1.5}
```
- Expected: More trades, earlier entry

## Known Limitations
1. **Catastrophic drawdown** (-90%) - NO STOP LOSS
2. **Poor R:R** - Losers (-8%) bigger than winners (7%)
3. **Exit timing** - Waiting for SMA takes too long
4. **Exit arbitrary** - May miss optimal exit

## Critical Fix Needed
**MUST ADD STOP LOSS** - Current -90% drawdown unacceptable for deployment

## Next Steps (In Order)
1. 🔄 **TEST: Add -5% stop loss** (CRITICAL)
2. 🔄 **TEST: Add +5% profit target**
3. 🔄 **TEST: Tighter bands (1.5σ)**
4. 🔄 **TEST: Combined parameters**

## If Validated After Enhancements
- Position Size: 2% of portfolio
- Stop Loss: -5% (mandatory)
- Profit Target: +5% (optional)
- Max Drawdown Target: < 25%

---

*Created: 2026-02-21*  
*Critical Issue: Add stop loss before any deployment*
