# Strategy: Gap Fade (REJECTED - Try Inverse)

## Current Status
- **Status:** ❌ REJECTED
- **Sharpe:** -0.07 (Tech), 0.13 (Equity)
- **Win Rate:** 50.5% (Tech), 51.7% (Equity)
- **Last Tested:** 2026-02-21
- **Note:** Try INVERSE strategy (follow gaps, not fade)

## Base Strategy (FAILED)
### Signal
- **Entry:** Gap > 2% (fade the gap)
- **Exit:** End of day
- **Result:** No edge, ~50% win rate (random)

### Parameters
```python
{'gap_threshold': 0.02}  # 2%
```

## Test History

### Test 1: 2026-02-21 - Tech Sector
- Universe: 28 Tech tickers
- Period: 2022-2024
- Trades: 2,648
- Results: Sharpe -0.07, Win 50.5%, MaxDD -98%
- Conclusion: ❌ FAILED - No edge, essentially random

### Test 2: 2026-02-21 - Equity Sector
- Universe: 30 Equity tickers
- Period: 2022-2024
- Trades: 2,051
- Results: Sharpe 0.13, Win 51.7%, MaxDD -90%
- Conclusion: ❌ FAILED - No edge

## Key Finding: Gaps TREND, Not Mean Revert
- Average gap: 3.5%
- Win rate fading: ~51% (coin flip)
- **Hypothesis:** Gaps continue in direction (follow momentum)

## INVERSE STRATEGY TO TEST (Gap Follow)

### New Hypothesis: Gap Follow (Opposite of Fade)
```python
if gap > 2%:  # Gap up
    # FOLLOW (go long) instead of fade (go short)
    direction = LONG
    
if gap < -2%:  # Gap down
    # FOLLOW (go short) instead of fade (go long)
    direction = SHORT
```

### Why This Might Work
1. Gaps often indicate news/earnings
2. News continues to drive price (momentum)
3. 3.5% avg gap suggests significant information
4. Fading = betting against information (losing)
5. Following = betting with information (winning)

## Enhancement Test: Gap Follow

### Test 3: Gap Follow (INVERSE)
```python
def gap_follow_signal(ticker_df, gap_threshold=0.02):
    for each day:
        gap = (open - prev_close) / prev_close
        
        if gap > gap_threshold:
            # Go LONG (follow the gap up)
            entry = open
            exit = close
            return = (exit - entry) / entry
            
        elif gap < -gap_threshold:
            # Go SHORT (follow the gap down)
            entry = open
            exit = close
            return = (entry - exit) / entry
```

### Expected Results
- If gaps trend: Win rate > 55%, Sharpe > 0.8
- If still random: Strategy truly has no edge

### Additional Filters to Try
- [ ] **Volume spike** - Only follow gaps with volume > 2x
- [ ] **Earnings gap** - Only trade earnings-related gaps
- [ ] **Gap size tier** - Test 1%, 2%, 3% thresholds
- [ ] **Hold period** - Test holding 2-5 days instead of 1

## Alternative: Gap Fade with Filters (Last Resort)
If Gap Follow also fails, try fading ONLY when:
- [ ] **Small gaps** (< 1%) - Less news-driven
- [ ] **No earnings** - Avoid news gaps
- [ ] **Overextended** - RSI > 70 before gap up
- [ ] **Volume not extreme** - Volume < 3x average

## Next Steps
1. 🔄 **TEST: Inverse strategy (Gap Follow)** - HIGH PRIORITY
2. 🔄 **TEST: Gap Follow + Volume filter**
3. 🔄 **TEST: Different gap thresholds (1%, 3%)**

## If Gap Follow Works
- Rename strategy to "Gap Momentum"
- Position Size: 1% (intraday risk)
- Hold: 1-3 days
- Stop Loss: -2%

## If Gap Follow Also Fails
- **Conclusion:** Gap-based strategies have no edge
- **Action:** Abandon gap strategies entirely
- **Reason:** Markets too efficient at pricing overnight info

---

*Created: 2026-02-21*  
*Status: REJECTED - Testing inverse hypothesis*  
*Next Action: Test Gap Follow strategy*
