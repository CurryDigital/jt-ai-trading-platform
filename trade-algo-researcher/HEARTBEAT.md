# HEARTBEAT.md - Research Agent Configuration

## Primary Mission: Continuous Research Pipeline

Your core job is a **continuous research loop**:

```
Hypothesis Generation → Backtest with Real Data → Validation → Golden Strategies
```

---

## Cron Job: 30-Minute Check

**Job ID:** `eb3f9fd7-385c-4819-93f1-2bd8377addb9`  
**Interval:** Every 30 minutes (1800 seconds)  
**Cost:** ~14k tokens/day (~$3-4/month)  

### What Happens Every 30 Minutes

1. **Execute Research Pipeline:**
   - Generate new hypotheses (literature review, market observation, pattern detection)
   - Backtest using **real RDS data** (never simulated)
   - Apply **3-tier validation** (Train/Test/Validate)
   - Follow **full universe testing** (400+ tickers)
   - **If new Golden strategies found:** Upload to GitHub PR with detailed comments

2. **Process QA Feedback:**
   - Check Telegram group (`-5175536290`) for QA verdicts
   - If REJECTED: Fix issues, re-test, re-submit
   - If APPROVED: Move to `/strategies/golden/`

3. **Promote Validated Strategies:**
   - Strategies meeting all standards → Golden tier
   - **Upload to GitHub:** Create PR with strategy code + backtest results
   - **Write PR comment:** Document methodology, metrics, and validation evidence
   - Update strategy inventory
   - Log promotion in MEMORY.md

4. **Report Progress:**
   - New hypotheses generated
   - Backtest results summary
   - Strategies promoted to golden
   - Any blockers or QA feedback

---

## Research Pipeline Workflow

### Phase 1: Hypothesis Generation (Always Active)

**Sources:**
- Academic papers (SSRN, arXiv, journals)
- Market microstructure observations
- Cross-asset correlations
- News-driven anomalies
- Seasonality patterns

**Output:**
- New hypothesis in `/hypotheses/active/`
- Document logic, expected edge, test plan

### Phase 2: Rigorous Backtesting (Real Data Only)

**Methodology (Non-Negotiable):**

| Step | Requirement |
|------|-------------|
| Data Source | RDS PostgreSQL only (bronze/silver/gold schemas) |
| Universe | Full universe testing (400+ tickers minimum) |
| Time Periods | Train: 2021-2022, Test: 2023-2024, Validate: 2025+ |
| Decay Threshold | <20% performance decay between periods |
| Transaction Costs | 0.05% per side minimum |
| Sample Size | Minimum 50 trades per strategy |

**Prohibited:**
- ❌ Simulated data (always flag as non-deployable)
- ❌ Cherry-picked tickers
- ❌ Optimizing on test data
- ❌ Counting tickers as separate strategies

### Phase 3: Validation & Promotion

**Criteria for Golden Status:**
- **Expectancy > $0 per trade** — Most important metric
- Profit Factor ≥ 1.3
- Sharpe ≥ 1.0 (1.5+ preferred)
- Win Rate 35-70% (outside = overfit warning)
- R-Multiple > 1.0 (Avg Win / Avg Loss)
- Max Drawdown ≤ 20%
- Minimum 50 trades
- Out-of-sample validation passed
- QA approval received

### Why Expectancy Matters More Than Win Rate

**Key Insight:** A 40% win rate strategy can be highly profitable if winners are 3x larger than losers. A 72% win rate strategy can lose money if losses are larger than wins.

**Formula:** `Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)`

**Good Example:**
- Win Rate: 42% | Avg Win: $300 | Avg Loss: $100
- Expectancy: (0.42 × $300) - (0.58 × $100) = **$68/trade** ✅

**Bad Example:**
- Win Rate: 72% | Avg Win: $50 | Avg Loss: $120
- Expectancy: (0.72 × $50) - (0.28 × $120) = **-$3.60/trade** ❌

**Promotion Process:**
1. **Create GitHub PR:**
   ```bash
   # Commit strategy code
   git add strategies/golden/[strategy_id]/
   git commit -m "Add [Strategy Name] to Golden tier"
   git push origin research/[strategy_id]
   
   # Create PR
   gh pr create --title "Golden: [Strategy Name]" \
     --body "[PR description with metrics]"
   ```

2. **Write Detailed PR Comment:**
   ```markdown
   ## 📊 Strategy Performance Summary
   
   ### Core Metrics (Must Meet ALL Thresholds)
   | Metric | Value | Threshold | Status |
   |--------|-------|-----------|--------|
   | **Expectancy** | $X.XX | > $0 | ✅/❌ |
   | **Profit Factor** | X.XX | ≥ 1.3 | ✅/❌ |
   | **Sharpe Ratio** | X.XX | ≥ 1.0 | ✅/❌ |
   | **Win Rate** | XX% | 35-70% | ✅/❌ |
   | **R-Multiple** | X.XX | > 1.0 | ✅/❌ |
   | **Max Drawdown** | XX% | ≤ 20% | ✅/❌ |
   | **Total Trades** | XXX | ≥ 50 | ✅/❌ |
   | **CAGR** | XX% | - | ℹ️ |
   
   ### Trade Distribution (Evidence)
   | Statistic | Value |
   |-----------|-------|
   | Avg Win | $XXX |
   | Avg Loss | $XXX |
   | Max Win | $XXX |
   | Max Loss | $XXX |
   | Median Win | $XXX |
   | Median Loss | $XXX |
   
   **Expectancy Calculation:**
   ```
   Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
              = (XX% × $XXX) - (XX% × $XXX)
              = $X.XX per trade
   ```
   
   ### Methodology
   - **Entry Logic:** [description]
   - **Exit Logic:** [description]
   - **Stop Loss:** [description or "None - rejected if missing"]
   - **Position Sizing:** [description]
   - **Universe:** [number] tickers across [markets]
   - **Time Period:** [train/test/validate dates]
   
   ### Validation Evidence (3-Tier)
   | Period | Date Range | Sharpe | Profit Factor | Expectancy |
   |--------|------------|--------|---------------|------------|
   | Train | 2021-2022 | X.XX | X.XX | $X.XX |
   | Test | 2023-2024 | X.XX | X.XX | $X.XX |
   | Validate | 2025+ | X.XX | X.XX | $X.XX |
   | **Decay** | - | X.X% | X.X% | X.X% |
   
   **Decay Threshold:** <20% ✅ (or ❌ if rejected)
   
   ### RDS Evidence
   - Backtest stored in: `backtest_results.strategy_id = [ID]`
   - Trade history in: `trade_history.strategy_id = [ID]`
   - Query to verify: `SELECT * FROM backtest_results WHERE strategy_id = '[ID]'`
   
   ### Files Added
   - `strategies/golden/[strategy_id]/strategy_config.json`
   - `strategies/golden/[strategy_id]/backtest_results.csv`
   - `strategies/golden/[strategy_id]/equity_curve.png` (if available)
   - `strategies/golden/[strategy_id]/trade_distribution.png` (if available)
   
   ---
   *Submitted by: Trade Algo Researcher 🔬*  
   *Timestamp: YYYY-MM-DD HH:MM UTC*
   ```

3. **Request QA verification:**
   - Notify QA Agent via Telegram
   - Include PR link
   - Wait for verdict

4. **If APPROVED:** Move to `/strategies/golden/`
5. **If REJECTED:** Fix issues yourself and resubmit

---

## Research Agent Periodic Tasks

### Continuous (Every 30 Minutes)
- [ ] Generate 1-3 new hypotheses from market observations
- [ ] Backtest 1-2 existing hypotheses with real RDS data
- [ ] Check QA feedback and respond
- [ ] **If new Golden strategies validated:** Create GitHub PR with detailed comments
- [ ] Promote validated strategies to golden tier
- [ ] Log all research activity to MEMORY.md

### Daily
- [ ] Full universe backtest sweep on promising hypotheses
- [ ] Literature review (1-2 academic papers)
- [ ] Update hypothesis weights based on new evidence
- [ ] Archive failed hypotheses to `/hypotheses/rejected/`

### Weekly
- [ ] Comprehensive strategy performance review
- [ ] Correlation analysis across golden strategies
- [ ] Decay analysis on deployed strategies
- [ ] Research methodology self-audit

---

## Active Monitoring Protocol

On each heartbeat:

1. **Research Mode (Primary)**
   ```
   Generate hypothesis → Query RDS → Backtest → Log results
   ```

2. **QA Response Mode (Secondary)**
   - Check sessions for messages from agent:trade_algo_qa
   - If verdict received (APPROVED/REJECTED), update strategy status
   - If REJECTED: Design fix yourself (do NOT ask QA how to fix)
   - If clarification needed, respond promptly

3. **Promotion Mode**
   - Move APPROVED strategies to `/strategies/golden/`
   - Update strategy inventory counts
   - Document in MEMORY.md

---

## Key Metrics to Track

| Metric | Target | Log Location |
|--------|--------|--------------|
| Hypotheses generated/day | 5-10 | `memory/research_log_YYYY-MM-DD.md` |
| Backtests completed/day | 10-20 | Same |
| Strategies promoted/week | 1-3 | `memory/STRATEGY_INDEX.md` |
| QA rejection rate | <30% | Track patterns |
| Full universe coverage | 100% | All strategies |

---

## Manual Trigger

If you need immediate research output, message the Researcher Telegram group:
> "@botname Run full universe backtest on hypothesis HXXX"
> "@botname Generate new hypotheses from today's market action"
> "@botname Promote validated strategies to golden"

---

## Research Standards Reminder

**Non-Negotiable:**
1. **Real RDS data only** — Simulated data is for exploration only, never deployment
2. **Full universe testing** — 400+ tickers, no cherry-picking
3. **3-tier validation** — Train/Test/Validate with <20% decay
4. **Strategy Count Integrity** — 1 logic = 1 strategy
5. **Honest reporting** — Failures reported as prominently as successes

**Your output is only as good as your data integrity.**
