# Hypothesis Status Documentation

**Date:** 2026-02-20  
**Schema:** openclaw_researcher  
**Table:** hypothesis_registry

---

## 📊 HYPOTHESIS LIFECYCLE

```
┌──────────┐     ┌───────────┐     ┌────────────┐     ┌───────────┐     ┌──────────┐
│          │     │           │     │            │     │           │     │          │
│   IDEA   │────▶│  TESTING  │────▶│  VALIDATED │────▶│ PROMOTED  │     │ REJECTED │
│          │     │           │     │            │     │  (Golden) │     │          │
└──────────┘     └───────────┘     └────────────┘     └───────────┘     └──────────┘
     │                  │                  │                  │                ▲
     │                  │                  │                  │                │
     └──────────────────┴──────────────────┴──────────────────┘────────────────┘
                                          │
                                    (Any stage can
                                     go to REJECTED)
```

---

## 🏷️ STATUS CATEGORIES

### 1. 💡 IDEA (48 hypotheses)
**Description:** Initial concept, needs research and hypothesis file creation  
**Entry Criteria:** Academic paper identified or strategy concept formulated  
**Exit Criteria:** Hypothesis file created with signal construction rules  
**Next Stage:** TESTING

**Examples:**
- VIX Term Structure
- Options Gamma Gravity
- Commodity Crack Spread
- ETF Arbitrage strategies

---

### 2. 🧪 TESTING (35 hypotheses)
**Description:** In backtesting phase using historical data  
**Entry Criteria:** Hypothesis file complete, backtest plan defined  
**Exit Criteria:** 
- **Promote to VALIDATED:** Sharpe > 1.0, Win Rate > 55%, 3+ years positive returns
- **Move to REJECTED:** Sharpe < 0.7 or Win Rate < 50% after 2+ years of data

**Current Testing (13 new from academic research):**
| Hypothesis | Academic Source | Target Sharpe |
|------------|-----------------|---------------|
| PEAD NLP Enhanced | Ball/Brown + Lopez-Lira | 1.45 |
| Accruals Quality | Sloan (1996) | 1.35 |
| CMV Multi-Factor | Asness (2013) | 1.35 |
| Momentum Lifecycle | Jegadeesh/Titman (1993) | 1.25 |
| VRP | Coval/Shumway (2001) | 1.25 |
| QARP | Asness (2018) | 1.25 |
| Retail Order Flow | Barber/Odean (2023) | 1.25 |
| LLM NLP Sentiment | Lopez-Lira (2023) | 1.20 |
| Inflation Regime | Reis/Blanchard (2022-23) | 1.15 |
| Time-Series Momentum | Hurst (2017) | 1.15 |
| Limits to Arbitrage | Shleifer/Vishny (1997) | 1.15 |
| Supply Chain Reshoring | Baldwin (2022) | 1.05 |
| ESG Improvers | Berkeley Haas (2024) | 0.90 |

---

### 3. ✅ VALIDATED (6 hypotheses)
**Description:** Proven with backtest data, ready for paper trading  
**Entry Criteria:** 
- Sharpe > 1.0
- Win Rate > 55%
- Max DD < 15%
- 3+ years positive returns
- Reproducible across markets (for universal strategies)

**Current Validated:**
| Hypothesis | Sharpe | Win Rate | Status |
|------------|--------|----------|--------|
| Macro Scaling > Stops | N/A | N/A | Ready for promotion |
| PEAD Earnings Drift (synth) | 2.43 | TBD | Needs real data |
| Sector Rotation Tech/Util | 0.83 | 66% | Validated |
| RSI Mean Reversion | 1.42 | 60% | Validated |
| Bollinger Squeeze | 3.64 | 67% | Validated |
| Engulfing Pattern | 3.90 | 80% | Validated |

**Next Stage:** PROMOTED (to Golden Strategy)

---

### 4. 🏆 PROMOTED (1 hypothesis → Golden Strategy)
**Description:** Live production strategy on JT platform  
**Entry Criteria:** Validated + deployed to JT + performing as expected  
**Current Promoted:**
| Strategy | Original Hypothesis | Sharpe | Date |
|----------|-------------------|--------|------|
| Gold/Silver Ratio | Commodity Seasonality | 1.11 | 2026-02 |

---

### 5. ❌ REJECTED (10 hypotheses) ⭐ NEW CATEGORY

**Description:** Failed validation, documented for learning  
**Entry Criteria:** Failed to meet minimum thresholds after testing  
**Documentation Required:**
- Actual Sharpe and Win Rate achieved
- Reason for rejection
- Date rejected
- Lessons learned

**Rejection Criteria:**
| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Sharpe Ratio | < 0.7 after 2+ years | Reject |
| Win Rate | < 50% | Reject |
| Max Drawdown | > 25% | Reject |
| Data Availability | Cannot obtain | Reject |
| Practical Constraints | Cannot execute | Reject |

**Current Rejected (10):**

| # | Hypothesis | Actual Sharpe | Actual Win% | Rejection Reason |
|---|------------|---------------|-------------|------------------|
| 1 | MACD_Divergence | 0.65 | 46% | Win rate below 50% threshold |
| 2 | 3Day_Reversal_Generic | 0.72 | 48% | Not viable as universal strategy |
| 3 | Gap_Fade_Universal | 0.68 | 47% | Only HK variant viable |
| 4 | Peer_Firm_Lag_Simple | 0.45 | 52% | Zero lag found in cross-sector |
| 5 | VIX_Contango_VXX | N/A | N/A | VXX delisted 2024 |
| 6 | Asian_Session_FX_Daily_Proxy | 0.35 | 35.5% | Daily proxy failed, needs hourly |
| 7 | Crypto_Funding_Rate_Proxy | 0.60 | 50% | Proxy failed, needs real funding data |
| 8 | Random_Walk_Breakout | 0.42 | 48.5% | No edge, indistinguishable from random |
| 9 | Social_Media_Sentiment_Levels | 0.55 | 51% | Levels not predictive (momentum works) |
| 10 | IPO_First_Day_Momentum | N/A | N/A | Data unavailable, execution impossible |

**Common Rejection Reasons:**
1. **Low Win Rate** (40%) - Strategy underperforms random
2. **Proxy Inadequate** (20%) - Simplified data doesn't capture edge
3. **Data Unavailable** (20%) - Cannot obtain required data
4. **No Edge Found** (10%) - Academic paper doesn't replicate
5. **Practical Constraints** (10%) - Cannot execute at scale

---

## 📈 LIFECYCLE STATISTICS

| Status | Count | Avg Target Sharpe | Avg Actual Sharpe |
|--------|-------|-------------------|-------------------|
| **IDEA** | 48 | 1.15 | N/A |
| **TESTING** | 35 | 1.21 | TBD |
| **VALIDATED** | 6 | 1.85 | 1.87 |
| **PROMOTED** | 1 | 1.11 | 1.11 |
| **REJECTED** | 10 | 1.23 | 0.54 |
| **TOTAL** | **100** | **1.20** | - |

---

## 🔄 TRANSITION RULES

```
IDEA → TESTING:
  ✓ Hypothesis file created with signal rules
  ✓ Data sources identified
  ✓ Backtest plan defined

TESTING → VALIDATED:
  ✓ Sharpe > 1.0
  ✓ Win Rate > 55%
  ✓ Max DD < 15%
  ✓ 3+ years positive returns

TESTING → REJECTED:
  ✗ Sharpe < 0.7 after 2+ years
  ✗ Win Rate < 50%
  ✗ Max DD > 25%
  ✗ Cannot obtain data
  ✗ Cannot execute practically

VALIDATED → PROMOTED:
  ✓ Deployed to JT platform
  ✓ Paper trading successful
  ✓ Live performance matches backtest

ANY → REJECTED:
  ✗ Fundamental flaw discovered
  ✗ Market regime change invalidates
  ✗ Better alternative found
```

---

## 🗄️ DATABASE SCHEMA

### Table: hypothesis_registry

| Column | Type | Description |
|--------|------|-------------|
| hypothesis_name | VARCHAR(100) PK | Unique name |
| hypothesis_file | VARCHAR(200) | Path to markdown file |
| academic_basis | VARCHAR(200) | Source paper/author |
| asset_class | VARCHAR(50) | Equities/FX/Crypto/etc. |
| direction | VARCHAR(20) | Long/Short/Neutral |
| target_sharpe | DECIMAL(6,2) | Expected Sharpe |
| target_win_rate | DECIMAL(6,2) | Expected Win% |
| current_status | VARCHAR(20) | idea/testing/validated/promoted/rejected |
| backtest_count | INTEGER | Number of backtests run |
| best_sharpe | DECIMAL(8,4) | Best achieved Sharpe |
| last_backtest_date | DATE | Most recent backtest |
| **rejection_reason** | TEXT | Why rejected (NEW) |
| **rejected_date** | DATE | When rejected (NEW) |
| **backtest_sharpe_actual** | DECIMAL(8,4) | Actual Sharpe achieved (NEW) |
| **backtest_win_rate_actual** | DECIMAL(6,2) | Actual Win% achieved (NEW) |

### Views

**v_rejected_hypotheses**
```sql
SELECT * FROM openclaw_researcher.v_rejected_hypotheses;
-- Shows all rejected hypotheses with reasons
```

**v_hypothesis_lifecycle**
```sql
SELECT * FROM openclaw_researcher.v_hypothesis_lifecycle;
-- Summary count by status
```

**v_promotion_candidates**
```sql
SELECT * FROM openclaw_researcher.v_promotion_candidates;
-- Hypotheses with Sharpe > 1.0 ready for promotion
```

---

## 📝 REJECTION WORKFLOW

### Step 1: Identify Failure
After backtesting, if results are below thresholds:
```python
if sharpe < 0.7 or win_rate < 50:
    status = 'rejected'
```

### Step 2: Document Reason
```python
rejection_reason = {
    'MACD_Divergence': '46% win rate below 50% threshold',
    'VIX_Contango_VXX': 'VXX delisted in 2024',
    'Asian_Session_FX_Proxy': 'Daily proxy failed, needs hourly data'
}
```

### Step 3: Update Registry
```sql
UPDATE openclaw_researcher.hypothesis_registry
SET current_status = 'rejected',
    rejection_reason = 'Failed validation: 46% win rate',
    rejected_date = CURRENT_DATE,
    backtest_sharpe_actual = 0.65,
    backtest_win_rate_actual = 46.0
WHERE hypothesis_name = 'MACD_Divergence';
```

### Step 4: Archive Files
Move hypothesis file to:
```
hypotheses/rejected/{hypothesis_name}.md
```

### Step 5: Learn and Iterate
Document lessons learned:
- What didn't work?
- Why didn't it work?
- What could be modified?
- Pivot to new hypothesis?

---

## 🎓 LESSONS FROM REJECTED HYPOTHESES

### 1. Technical Patterns Need Context
**Rejected:** MACD Divergence (46% win rate)  
**Lesson:** Standalone technical patterns rarely work. Need:
- Volume confirmation
- Market regime filter
- Fundamental overlay

### 2. Proxies Are Dangerous
**Rejected:** Asian Session FX Daily Proxy (35.5% win rate)  
**Rejected:** Crypto Funding Rate Proxy (50% win rate)  
**Lesson:** Simplified proxies often fail. Must use actual data:
- TrueFX for hourly FX
- Binance API for funding rates

### 3. Data Availability Matters
**Rejected:** VXX Contango (delisted)  
**Rejected:** IPO First Day (execution impossible)  
**Lesson:** Validate data availability BEFORE hypothesis creation.

### 4. Academic Papers Don't Always Replicate
**Rejected:** Peer Firm Lag Simple (zero lag found)  
**Lesson:** Papers may have:
- Look-ahead bias
- Survivorship bias
- Different market conditions

Always test independently.

---

## 📊 REJECTION ANALYSIS

```sql
-- Get rejection statistics
SELECT * FROM openclaw_researcher.get_rejection_analysis();

-- Result:
-- total_rejected: 10
-- avg_target_sharpe: 1.23
-- avg_actual_sharpe: 0.54
-- common_reasons: Low Win Rate, Proxy Inadequate, Data Unavailable
```

**Key Insight:** Target Sharpe (1.23) vs Actual (0.54) = 56% overestimation

---

## 🔮 FUTURE IMPROVEMENTS

1. **Predictive Rejection Model**
   - Use hypothesis characteristics to predict failure
   - Save time on unlikely ideas

2. **Automatic Rejection Detection**
   - Trigger rejection after N failed backtests
   - Auto-archive and document

3. **Rejection Recovery**
   - Periodic re-testing of rejected hypotheses
   - Market conditions change

4. **Cross-Agent Learning**
   - Share rejections with JT Trading Agent
   - Avoid duplicate failures

---

**Last Updated:** 2026-02-20  
**Rejected Hypotheses:** 10  
**Validation Rate:** 6% (6 validated / 100 total)
