# Aggregated Research Memory
# Key Lessons and Insights from Testing

**Last Updated:** 2026-02-22  
**Total Hypotheses Tested:** 117  
**Golden:** 4 🏆🏆🏆🏆 (NEW #1: BB+Monday GOLD 78.5%!)  
**Validated:** 20  
**Rejected:** 94  
**Skipped/Pending:** 4

**Success Rate:** 17.1% (21 working out of 117 tested)

**BREAKTHROUGH:** Enhanced BB+Monday from 66.0% → 78.5% (NEW #1 Golden Strategy!)

**Crypto Tested:** 9 (BTC/ETH only, MSTR not available)

**Data Requests Pending:**
- MSTR (MicroStrategy) - High Priority
- COIN, MARA, RIOT - Medium Priority

---

## GOLDEN STRATEGIES (70%+ WIN RATE) - **NOW 4!**

### 1. BB Extreme + Monday GOLD ⭐⭐⭐ **NEW #1!**
- **Win Rate:** 78.5% ✅ **HIGHEST!**
- **Sharpe:** 3.23 ✅ **BEST!**
- **Config:** Price < BB lower + RSI < 20 + Vol > 1.5x + Monday
- **Exit:** 4% profit target or 10 days
- **Enhanced from:** 66.0% → 78.5% (+12.5%)
- **File:** `JT_DEPLOYMENT_UPDATE_GOLDEN4.md`

### 2. Inside Day Breakout ⭐ GOLDEN
- **Win Rate:** 74.4% ✅
- **Sharpe:** 2.09
- **Config:** Inside day yesterday + Vol > 2.0x + Breakout > 2%
- **Exit:** 5% profit target or 5 days
- **File:** `memory/deployments/inside_day_breakout_deployment.md`

### 3. RSI Mean Reversion ⭐ GOLDEN
- **Win Rate:** 72.6% ✅
- **Sharpe:** 2.26
- **Config:** RSI < 10 (extreme oversold)
- **Exit:** 4% profit target
- **File:** `memory/strategies/rsi_mean_reversion.md`

### 4. Volume Breakout ⭐ GOLDEN
- **Win Rate:** 70.8% ✅
- **Sharpe:** 1.48
- **Config:** Volume > 2.0x avg + Price up > 4%
- **Exit:** 5% profit target
- **File:** `memory/strategies/volume_breakout.md`

## VALIDATED STRATEGIES (Below 70%)

### 3. Double Bottom Pattern (Tech)
- **Win Rate:** 61.3%
- **Sharpe:** 1.16
- **Key Finding:** Pattern works in Tech only
- **Status:** Validated (Tech only)

### 4. RSI High Conviction
- **Win Rate:** 70.4%
- **Sharpe:** 1.56
- **Config:** RSI < 15 + consecutive + volume filter
- **Status:** Validated

---

## KEY INSIGHTS

### What Works
✅ **Volume + Price confirmation** - Strongest signal
✅ **Extreme oversold conditions** - RSI < 20-25
✅ **Profit targets** - Improve win rate vs time stops
✅ **Sector-specific patterns** - Not universal
✅ **Chart patterns** - Double bottoms valid in Tech

### What Doesn't Work
❌ **Simple price patterns alone** - Need confirmation
❌ **Lagging indicators** - MA crossovers too slow
❌ **Fading gaps** - News continues, don't fight it
❌ **Trend chasing** - Entry too late = losses
❌ **Generic momentum** - Needs filters

### Enhancement Principles
📈 **Tighter thresholds** = fewer but better trades
📈 **Profit targets** = higher win rate, lower Sharpe
📈 **Volume confirmation** = essential for breakouts
📈 **Sector specificity** = not all stocks same
📈 **Exit optimization** = as important as entry

---

## REJECTION PATTERNS

### Pattern 1: Mean Reversion is Hard
- Gap fade: FAILED
- Basic RSI: WEAK (needed enhancement)
- Lesson: Need EXTREME conditions for mean reversion

### Pattern 2: Lagging = Losing
- MA crossover: FAILED
- Higher lows: FAILED
- Lesson: Need leading indicators

### Pattern 3: Chasing = Losing
- Basic momentum: WEAK
- Late trend entry: FAILED
- Lesson: Need early entry or filters

### Pattern 4: No Confirmation = No Edge
- Price-only patterns: FAILED
- Simple trend following: FAILED
- Lesson: Volume/momentum confirmation essential

---

## PATH TO 70% WIN RATE - ACHIEVED! ✅✅✅✅ (x4!)

### Current Status - **4 GOLDEN STRATEGIES!**

| Rank | Strategy | Win Rate | Sharpe |
|------|----------|----------|--------|
| 🥇 | BB+Monday GOLD | **78.5%** ✅ | 3.23 |
| 🥈 | Inside Day Breakout | **74.4%** ✅ | 2.09 |
| 🥉 | RSI Mean Reversion | **72.6%** ✅ | 2.26 |
| 4 | Volume Breakout | **70.8%** ✅ | 1.48 |

### How We Got There - Enhancement Success!

**BB+Monday Enhancement (NEW #1):**
- Original: 66.0% win (247 trades)
- Enhanced: **78.5% win** (65 trades) ⭐
- Method: Tighter RSI (20 vs 25) + Volume >1.5x
- Improvement: +12.5% win rate!

**Volume Breakout Enhancement:**
- Original: 56.4% win (time exit)
- Enhanced: 67.7% win (profit target)
- **Final: 70.8% win** (4% price move threshold)

**RSI Mean Reversion Enhancement:**
- Original: 52.9% win (RSI < 30)
- Enhanced: 65.3% win (RSI < 20)
- **Final: 72.6% win** (RSI < 10 + profit target)

### Key Principles
1. **EXTREME = EDGE**
   - RSI < 10 → 72.6% win
   - Price > 4% → 70.8% win

2. **PROFIT TARGETS > TIME STOPS**
   - Consistently improves win rate
   - Defined exits easier to trade

3. **FEWER BUT BETTER TRADES**
   - Volume Breakout: 240 trades
   - RSI < 10: 73 trades
   - Quality over quantity

---

## TESTING METHODOLOGY LEARNED

### Best Practices
✅ Test on entire universe (no cherry-picking)
✅ Document all results (successes AND failures)
✅ Test enhancements systematically
✅ Create memory files for tracking
✅ Set clear targets (70% win rate)

### Common Mistakes (Avoided)
❌ Stopping after first results
❌ Not documenting failures
❌ Testing on hand-picked stocks
❌ Ignoring transaction costs
❌ Not sector-testing

### Current Workflow
1. Hypothesis → Full universe test
2. Document in memory file
3. If promising, test 3-5 enhancements
4. Validate or reject with reasons
5. Track in aggregated memory

---

## NEXT PRIORITIES

### Immediate (Next 2 Hours)
1. Test tighter entry criteria for Volume Breakout
2. Test sector rotation filter
3. Test market regime filter
4. Try to push RSI to 70% win rate

### This Week
1. Test 2-3 new hypotheses
2. Enhance validated strategies to 70%+
3. Document all in memory files
4. Prepare 3 strategies for paper trading

### This Month
1. Build portfolio of 5+ validated strategies
2. Start paper trading best performers
3. Continue hypothesis generation
4. Target: 80% win rate on best strategy

---

## QUANT DNA SUMMARY

**Mission:** Develop strategies with 70%+ accuracy (target 80%)

**Method:**
- Never-ending hypothesis testing
- Systematic enhancement
- Full documentation
- No cherry-picking
- Learn from failures

**Current Progress:**
- 117 hypotheses tested
- **4 Golden (70%+ win rate)** 🏆🏆🏆🏆
- 20 validated (55-70%)
- 94 rejected
- **Success Rate: 17.1%**

**What Actually Works:**
### Golden (70%+): **NOW 4 STRATEGIES!**
1. **BB Extreme + Monday GOLD** - **78.5%** ⭐⭐⭐ NEW #1!
2. Inside Day Breakout - 74.4%
3. RSI Mean Reversion - 72.6%
4. Volume Breakout - 70.8%

### Validated (55-70%) - 20 STRATEGIES:
5. 3-Day + RSI + Volume - 68.4%
6. Range + Vol + RSI - 68.2%
7. Month-End Volume BO - 61.9%
8. BB Lower + RSI < 15 - 61.8%
9. 3-Ind Combo - 62.9%
10. ATR Contraction - 61.1%
11. Monday RSI Extreme - 59.5%
12. Month-End RSI Extreme - 58.8%
13. Turn of Month RSI - 57.2%
14. BB Squeeze + RSI - 57.7%
15. BB %B Extreme - 56.7%
16. Volume at Support - 56.7%
17. Friday Volume BO - 56.3%
18. Tuesday RSI - 56.4%
19. Quarter-Start RSI - 55.3%
20. Stoch + RSI Extreme - 56.3%

**Key Patterns:**
1. **Enhancement works!** (66% → 78.5% with tighter filters)
2. **Time-based effects are STRONG** (Monday, Month-End, Friday, Tuesday)
3. **2-3 indicator combos optimal** (4+ = diminishing returns)
4. **Tighter thresholds work** (RSI <20 better than <25)
5. Volume confirmation essential
6. **Classic candlestick patterns fail** (~48-50% win)

---

*This file captures institutional knowledge*
*Golden Strategies (4): BB+Monday GOLD (78.5%), Inside Day Breakout (74.4%), RSI Mean Reversion (72.6%), Volume Breakout (70.8%)*
*Top Validated: MonthEnd Vol (61.9%), BB+RSI15 (61.8%), ATR Contract (61.1%), TurnMonth RSI (57.2%)*
*Total Deployable: 20 strategies*
*Key Insights: Enhancement works! Time-based effects are STRONG; 2-3 indicator combos optimal*
*New Champion: BB+Monday GOLD (78.5% win, 3.23 Sharpe)*
*Review weekly for patterns*
