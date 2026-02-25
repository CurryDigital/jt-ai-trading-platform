# Key Insights — Curated Wisdom
**Research findings that generalize across strategies**  
**Last Updated:** 2026-02-25

---

## 🧠 Universal Principles

### 1. Mean Reversion Works Best in Strong Trends
**Finding:** Extreme RSI + Strong Uptrend = highest win rates  
**Evidence:**
- COIN: 85.7% → 93.3% (+7.6%) with Strong Uptrend filter
- MSTR: 63.2% → 81.2% (+18%) with SPY filter

**Application:** Always check trend strength before entering mean reversion  
**Avoid:** Weak trends (ADX < 25) — low conviction, poor results

---

### 2. Time-Based Filters Add Significant Alpha
**Finding:** Monday effect adds 10-20% win rate for mean reversion  
**Evidence:**
- BB+Monday: 78.5% → 88.9% (+10.4% in HK)
- 3-Day+Monday: 68.4% → 70.5% (+2.1%)
- BB+RSI15+Monday: 61.8% → 72.7% (+10.9%)

**Application:** Use day-of-week filters systematically  
**Mechanism:** Weekend news creates Monday volatility → mean reversion Tuesday+

---

### 3. Asset-Specific Optimization Beats Universal Rules
**Finding:** Same strategy performs differently by market  
**Evidence:**
- Gap Fade: 88.9% in HK vs -0.37 Sharpe universal → REJECTED universal
- RSI MR: 72.6% HK vs 51.3% China → Avoid China A-shares
- BB+Monday: 88.9% HK vs 78.5% universal → Deploy HK-only version

**Application:** Test all strategies on each market; reject universal deployment

---

### 4. SPY Regime Filter is Asset-Specific
**Finding:** Not all assets benefit from market regime filters  
**Evidence:**

| Asset | SPY Filter Impact |
|-------|-------------------|
| MSTR | +18% ✅ |
| RIOT | +9% ⚠️ |
| COIN | 0% ❌ |
| QQQ | 0% ❌ |

**Rule:** Test filter on each asset individually; don't assume universal benefit

---

### 5. Profit Targets Beat Trailing Stops
**Finding:** Exit strategy matters more than entry refinement  
**Evidence:**
- +3% Profit Target: +9.9% win rate boost
- Trailing Stop: -11.2% win rate destruction

**Application:** Use profit targets for mean reversion; avoid trailing stops

---

### 6. Small Sample Sizes Are Dangerous
**Finding:** 100% win rates with <20 trades are statistical flukes  
**Evidence:**
- COIN "100%" with 10 trades → True rate 70-85% (95% CI: [72%, 100%])
- Need 30+ trades for reliable estimates

**Rule:** Always check sample size; 95% confidence interval for win rates

---

### 7. Correlated Assets Limit Diversification
**Finding:** Crypto portfolio (MSTR+COIN) has limited diversification benefit  
**Evidence:**
- Individual Sharpe: 4.5-5.0
- Portfolio Sharpe: 4.65 (minimal improvement)
- Correlation: High (both BTC proxies)

**Application:** Diversify across uncorrelated asset classes, not just tickers

---

### 8. Walk-Forward Validation Reveals True Performance
**Finding:** Train/test splits expose overfitting invisible in full-period backtests  
**Evidence:**
- NVDA AI Theme: Full period 73% → Train 71% → **Test 45%** (failed validation)
- QQQ Lead-Lag: Claimed 79% → Train 68% → **Test 61%** (realistic)
- COIN: Claimed 93% → Train 62% → **Test 86%** (improved out-of-sample!)

**Rule:** Always use walk-forward validation (train 2021-2022 / test 2023-2024)  
**Red Flag:** Decay >15% between train and test = overfitting  
**Green Flag:** Negative decay (test > train) = strategy improving

---

### 9. Momentum Strategies Are Validated (Not Just Mean Reversion)
**Finding:** Long-term momentum (12-month) has strong edge — "trend is your friend" confirmed  
**Evidence:**
- 12M Momentum (>20%): **75.8%** win rate, 227 signals
- 3M Momentum (>10%): **57.3%** win rate, 178 signals
- Price > 200d MA: **68.5%** win rate, 292 signals
- ADX > 25 (trend strength): **65.4%** win rate, 471 signals

**Application:** Deploy momentum overlay in addition to mean reversion  
**Best Use:** Use momentum for trend continuation, mean reversion for pullbacks

---

### 10. Volatility Compression Predicts Explosive Moves
**Finding:** Low volatility periods reliably predict high volatility breakouts  
**Evidence:**
- ATR Compression: **85.7%** win rate (7 signals)
- BB Squeeze (width < 80% avg): **66.7%** win rate, 147 signals

**Application:** Monitor volatility metrics; size up when compression detected  
**Mechanism:** Coiled spring effect — low vol → explosive move

---

### 11. Classic Candlestick Patterns Have Edge
**Finding:** Traditional patterns validated with walk-forward testing  
**Evidence:**
- Hammer Pattern: **66.7%** win rate, 12 signals
- Bullish Engulfing: **65.9%** win rate, 41 signals

**Application:** Include pattern recognition in signal stack  
**Note:** Patterns work best when combined with oversold conditions (RSI)

---

### 12. RSI Divergence = High-Quality Signal
**Finding:** Bullish RSI divergence (price lower low, RSI higher low) = trend exhaustion  
**Evidence:**
- RSI Bullish Divergence: **80.0%** win rate
- Only 10 signals but very high quality

**Application:** Use divergence as high-conviction filter  
**Best Use:** Combine with oversold (RSI < 40) for best results

---

### 12. RSI Divergence = High-Quality Signal
**Finding:** Bullish RSI divergence (price lower low, RSI higher low) = trend exhaustion  
**Evidence:**
- RSI Bullish Divergence: **80.0%** win rate
- Only 10 signals but very high quality

**Application:** Use divergence as high-conviction filter  
**Best Use:** Combine with oversold (RSI < 40) for best results

---

### 13. Fundamental Filters Enhance Technical Signals (CMV Breakthrough)
**Finding:** Adding Carry/Momentum/Value (CMV) filters to RSI mean reversion significantly improves performance

**Evidence (Batch 14 Testing):**
- Base RSI (<25): 52.4% WR, 0.64% expectancy
- **CMV Enhanced:** **60.1%** WR, **+2.24%** expectancy
- **Improvement:** +7.7% win rate, +250% expectancy boost

**Best Performers with CMV:**
- 3988.HK (Bank of China): 57% → 83% WR (+26%)
- 3328.HK (Bank of Comm): 50% → 60% WR (+10%)

**Application:** Apply CMV filter to all mean reversion strategies
- **Carry:** Dividend yield percentile
- **Momentum:** 12-month return
- **Value:** Position within 52-week range

**Trade-off:** 37% fewer trades but 250% better returns (quality > quantity)

---

### 14. Cross-Market Arbitrage Fails for Swing Trading
**Finding:** ADR-Local arbitrage (HK vs US listings) produces no edge at swing trading timeframes

**Evidence (Batch 14 Testing):**
- 9988.HK/BABA: 50.8% WR, -0.12% avg P&L
- 0700.HK/TCEHY: 53.4% WR, -0.00% avg P&L  
- **Overall: 48.9% WR** — no edge after costs

**Why It Fails:**
- Currency noise (HKD/USD) dominates signals
- 3-day hold too short for convergence
- Transaction costs make it unprofitable
- Requires HFT infrastructure (sub-minute execution)

**Application:** Avoid cross-market arbitrage for swing trading
**Exception:** Only viable with real-time execution and sub-1-hour holds

---

### 15. Tech Pack Format Standard (User Requirement)
**Lesson:** Vague specifications cause confusion. Explicit, structured format required for deployment.

**Required Format for All Tech Packs:**

1. **Explicit Universe (Ticker List)**
   - List ALL tickers in table format
   - Include company name and sector
   - State total count explicitly

2. **Clear Buy Signal**
   - Pseudocode with exact conditions
   - Position sizing percentage
   - Max concurrent positions

3. **Clear Sell Signal**
   - All exit conditions listed
   - Each condition explained in [brackets]
   - No vague terms like "technical break"

4. **KPI/Metrics Table**
   | Metric | Calculation | Exit Threshold |
   |--------|-------------|----------------|
   | SMA50 | 50-day moving average | Close < SMA50 |
   | ADX | EMA(DX, 14) | < 20 |
   | Profit | (Current-Entry)/Entry*100 | ≥ +10% |

5. **Estimated Performance**
   - Win rate with 95% confidence interval
   - Historical trade count
   - Expected signals/year
   - Expected return per trade

6. **Description**
   - What the strategy does
   - Why it works (the edge)
   - Market conditions where it excels

**Example of Good vs Bad:**

❌ **Bad:** "Exit on technical break or 15 days"
✅ **Good:** "Exit at FIRST of: 1. ADX(14) < 20 [trend weakened], 2. -DI > +DI [bearish crossover], 3. Close < SMA(50) [support broken], 4. 15 days elapsed"

---

### 17. Latest 3-Month P&L Reveals Strategy Decay
**Finding:** Historical performance can hide recent strategy degradation. Latest quarterly performance is critical for deployment decisions.

**Evidence (Demo Analysis):**
| Scenario | Historical Return | Latest 3M Return | Feasibility |
|----------|-------------------|------------------|-------------|
| **A (Hot)** | +21% | **+15.6%** | 🟢 Deploy now |
| **B (Cold)** | +24% | **-1.7%** | 🔴 Avoid — decay detected |
| **C (Warm)** | +21% | **+7.6%** | 🟡 Safe to deploy |

**Key Insight:** Scenario B looked great historically (+24%) but recent performance was negative (-1.7%) — strategy has decayed or regime changed.

**New Testing Standard:**

| Feasibility | Latest 3M Return | Latest 3M WR | Action |
|-------------|------------------|--------------|--------|
| 🟢 **HOT** | > +5% | >= 60% | Deploy immediately |
| 🟡 **WARM** | > 0% | >= 50% | Safe to deploy |
| 🔴 **COLD** | < 0% | < 50% | Avoid — possible decay |
| ⚪ **UNKNOWN** | N/A | < 5 trades | Wait for more data |

**Application:** Always check latest 3-month P&L before deployment. A strategy with 70% historical WR but negative recent performance should NOT be deployed.

**Implementation:** All backtests now report `latest_3m_return`, `latest_3m_wr`, and `latest_3m_expectancy` via `backtest_analytics.py`

---

## ⚠️ Common Pitfalls

### Pitfall 1: Overfitting to Specific Conditions
**Symptom:** Strategy works only in one market/regime  
**Example:** Gap Fade worked on 6 hand-picked tickers (2.10 Sharpe) but failed on all 50 (-0.37 Sharpe)

**Prevention:** Test on entire universe, not cherry-picked examples

---

### Pitfall 2: Assuming Filter Universality
**Symptom:** Applying SPY filter to all assets  
**Example:** COIN showed no benefit from SPY filter; MSTR showed +18%

**Prevention:** Test "with filter" vs "without filter" for EACH asset

---

### Pitfall 3: Ignoring Transaction Costs
**Symptom:** Backtests show 60%+ win rates but live results disappoint  
**Example:** 0.1% cost per trade reduces win rate by ~2-3%

**Prevention:** Always include realistic transaction costs in backtests

---

### Pitfall 4: Data Look-Ahead Bias
**Symptom:** Impossibly high win rates  
**Example:** Using future SMA values, calculating indicators with future data

**Prevention:** Use rolling calculations with proper lookback; validate manually

---

### Pitfall 5: Reporting Inflated Win Rates Without Validation
**Symptom:** Claiming 90%+ win rates from full-period backtests  
**Example:**
- COIN claimed 93% (full period) → Validated 86% (test period)
- NVDA claimed 73% (full period) → Validated 45% (test period) — **REJECTED**

**Prevention:**
1. Always use train/test splits
2. Report test-period win rates as primary metric
3. Flag strategies with <20 trades in test period as "insufficient data"

**Validation Threshold:**
- Deploy: Test ≥60% with ≥15 trades
- Monitor: Test 55-60% with ≥10 trades
- Reject: Test <55% or <10 trades

---

## ✅ Best Practices

### Practice 1: Three-Layer Architecture
**Structure:** NEWS → HYPOTHESES → STRATEGIES  
**Flow:**
1. News triggers hypothesis
2. Hypothesis validates with evidence
3. Validated hypothesis → Golden Strategy

**Benefit:** Clear lineage from idea to deployment

---

### Practice 2: Immediate Documentation
**Rule:** Document within 5 minutes of discovery  
**Format:**
- One-line summary in research_log
- Detailed notes in strategy file
- Update master index

**Benefit:** Prevents forgetting context; enables reproduction

---

### Practice 3: Weekly Consolidation
**Schedule:** Every Monday 09:00 HKT  
**Tasks:**
1. Archive daily logs > 7 days
2. Update strategy statuses
3. Verify paper trading vs backtest
4. Promote validated strategies to Golden

**Benefit:** Prevents memory bloat; maintains accuracy

---

### Practice 4: Tag Everything
**Tags:** #breakthrough #correction #exploration #refinement #expansion #rejected  
**Usage:** Enables filtering by type; identifies patterns

**Example:** 60% of #exploration experiments succeed vs 80% of #refinement

---

## 📊 Performance Patterns

### By Strategy Type
| Type | Win Rate Range | Sharpe Range | Best For |
|------|----------------|--------------|----------|
| Mean Reversion | 65-93% | 1.5-3.0 | Crypto, HK |
| Breakout | 68-74% | 1.2-2.0 | Tech, Volume |
| Momentum | 55-60% | 1.0-1.5 | US Large Cap |

### By Asset Class
| Asset | Best Strategy Type | Typical Win% |
|-------|-------------------|--------------|
| Crypto (MSTR/COIN) | Mean Reversion + Regime | 80-93% |
| HK Stocks | Mean Reversion + Monday | 85-89% |
| US Tech | Breakout + Volume | 70-74% |
| Small Caps (IWM) | Mean Reversion + Trend | 80-90% |
| China A-Shares | — | <55% (avoid) |

### By Filter Type
| Filter | Win Rate Boost | Best For |
|--------|----------------|----------|
| Monday Effect | +10-20% | Mean Reversion |
| SPY Strong Uptrend | +7-18% | High-Beta Crypto |
| +3% Profit Target | +10% | All Mean Reversion |
| Volume > 1.5x | +5-10% | Breakout Entries |

---

### 14. Win Rate Alone Is Misleading — Expectancy Rules
**Finding:** High win rate ≠ profitable strategy. Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)

**Evidence:**
- **Strategy A:** 70% WR, +1% avg win, -3% avg loss = **-0.2% expectancy** ❌
- **Strategy B:** 55% WR, +3% avg win, -2% avg loss = **+0.75% expectancy** ✅

**Application:** Always evaluate strategies on:
1. **Expectancy** (must be positive)
2. **Profit Factor** (gross profits / gross losses, target > 1.5)
3. **Win/Loss Ratio** (avg win / avg loss, target > 1.0)
4. **Total Return** (sum of all trade P&Ls)
5. **Max Drawdown** (largest peak-to-trough decline)

**New Testing Standard:**
| Metric | Target | Minimum |
|--------|--------|---------|
| Win Rate | 60%+ | 55% |
| Expectancy | +0.5% | > 0% |
| Profit Factor | > 2.0 | > 1.2 |
| Win/Loss Ratio | > 1.5 | > 1.0 |
| Max Drawdown | < 15% | < 25% |
| Sharpe Ratio | > 1.5 | > 0.8 |

**Rule:** A strategy with 70% WR but negative expectancy is WORSE than 50% WR with positive expectancy

**Implementation:** All backtests now report comprehensive P&L analytics via `backtest_analytics.py`

---

## 🔗 Cross-References

**Related Strategy Files:**
- [COIN_Strong_Uptrend_GOLD](strategies/COIN_Strong_Uptrend_GOLD.md) — Insight #1 example
- [BB_Monday_GOLD](strategies/BB_Monday_GOLD.md) — Insight #2 example  
- [Crypto_SPY_Regime](strategies/Crypto_SPY_Regime.md) — Insight #4 data
- [BATCH_14_RESULTS](../rigorous_retest/BATCH_14_FINAL_RESULTS.md) — Insight #13 (CMV Filter)

**Source Research:**
- [RESEARCH_LOG_OPTIMIZED](RESEARCH_LOG_OPTIMIZED.md) — All experiments
- [STRATEGY_INDEX](STRATEGY_INDEX.md) — Strategy performance table
- [backtest_analytics.py](../rigorous_retest/backtest_analytics.py) — P&L analytics engine

---

### 18. Monte Carlo Simulation Reveals Strategy Robustness
**Finding:** Historical backtest is just ONE path. Monte Carlo tests 1,000+ scenarios by reshuffling trade returns.

**Implementation:**
```python
mc_metrics = BacktestAnalytics.monte_carlo_simulation(trades_df, n_simulations=1000)
```

**Key Metrics:**
| Metric | Interpretation |
|--------|----------------|
| Prob of Profit | % of scenarios with positive return |
| Worst Case (5%) | VaR — 5% worst outcomes |
| Robustness Score | % of profitable paths |

**Verdict Scale:**
- **>= 80%** — ✅ ROBUST: Works in most market conditions
- **50-80%** — ⚠️ MARGINAL: Sensitive to path
- **< 50%** — ❌ FRAGILE: Lucky historical path

**Example:** Strategy with 70% WR but only 40% MC robustness = historical luck, not skill

---

### 19. Transaction Cost Sensitivity is Critical
**Finding:** Strategies that work at 0.1% cost may fail at 0.2%. Testing multiple cost levels prevents surprises.

**Implementation:**
```python
cost_metrics = BacktestAnalytics.transaction_cost_sensitivity(trades_df)
```

**Test Levels:** 0.05%, 0.10%, 0.20%, 0.50% (round-trip)

**Verdict Scale:**
| Robustness | Pass Rate | Assessment |
|------------|-----------|------------|
| 4/4 (100%) | ✅ Cost robust | Works at all levels |
| 3/4 (75%) | ⚠️ Sensitive | Break-even ~0.15% |
| ≤2/4 (50%) | ❌ Fragile | Fails at modest costs |

**Application:** 
- **Crypto strategies:** Must pass at 0.2%+ (higher slippage)
- **HK stocks:** Can tolerate 0.1% (liquid, low slippage)
- **Small caps:** Require 0.15%+ margin

**Example:** Strategy with 60% WR but break-even at 0.08% = fails in live trading

---

*Curated from 19+ universal principles*  
*Updated when new generalizable insights emerge*