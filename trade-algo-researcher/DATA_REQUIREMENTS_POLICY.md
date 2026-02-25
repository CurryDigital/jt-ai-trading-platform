# Data Requirements Policy

**Date:** 2026-02-20  
**Status:** Active  
**Applies to:** All hypothesis testing and backtesting

---

## 🛑 CORE PRINCIPLE

**NO COMPROMISE ON DATA QUALITY**

When required data is missing or incomplete:
1. ❌ DO NOT use synthetic/proxy data
2. ❌ DO NOT find workarounds  
3. ❌ DO NOT skip the test
4. ✅ PAUSE the backtest
5. ✅ SEND REQUEST to Jacky
6. ✅ WAIT for JT Trading Agent to backfill

---

## 📋 ESCALATION WORKFLOW

### Step 1: Identify Data Gap
During backtest preparation:
```python
# Check data availability
if data_unavailable or insufficient_history:
    status = "BLOCKED - DATA REQUEST NEEDED"
```

### Step 2: Pause and Document
Stop the backtest. Document:
- What data is needed
- Why it's needed
- Time period required
- Schema/table location

### Step 3: Send Request to Jacky
Format:
```
DATA REQUEST - [Hypothesis Name]

Required Data: [specific table/columns]
Schema: [gold/silver/consumption]
Time Period: [start date] to [end date]
Purpose: [why needed for hypothesis]
Blocking: [yes/no - can test proceed without it?]

Request sent to: JT Trading Agent
```

### Step 4: Wait for Backfill
JT Trading Agent will:
- Source the data
- Backfill to RDS
- Notify when complete

### Step 5: Resume Testing
Only after confirmation of data availability.

---

## 🚫 PROHIBITED PRACTICES

### NEVER DO:

1. **Proxy Substitution**
   - ❌ Use overnight gaps as proxy for Asian Session FX
   - ❌ Use 3-day price moves as proxy for funding rates
   - ❌ Use ETF holdings as proxy for ESG ratings

2. **Synthetic Data**
   - ❌ Generate fake RSI values
   - ❌ Interpolate missing price data
   - ❌ Create simulated earnings surprises

3. **Workarounds**
   - ❌ Skip data quality checks
   - ❌ Reduce sample size to avoid missing data
   - ❌ Use alternative data sources without approval

4. **Partial Testing**
   - ❌ Test on subset when full data available
   - ❌ Reduce time period to avoid gaps

---

## ✅ APPROVED APPROACH

### When Data is Missing:

**Example: Accruals Quality Hypothesis**

**Problem:** Gold schema only has Feb 2026 data, need 2020-2024 for backtest.

**❌ WRONG:**
```python
# DON'T DO THIS
# Use proxy: (Net Income - OCF) / Assets from available data
# Or calculate from limited data
# Or skip the test
```

**✅ RIGHT:**
```python
# PAUSE AND REQUEST
print("DATA REQUEST NEEDED")
print("Hypothesis: Accruals Quality (Sloan 1996)")
print("Required: gold.stock_metrics or equivalent with accruals data")
print("Period: 2020-01-01 to 2024-12-31")
print("Purpose: Calculate accruals ratio for quality filter")
print("Action: Sending request to JT Trading Agent for backfill")

# STOP - DO NOT PROCEED
status = "BLOCKED_PENDING_DATA"
```

---

## 📊 CURRENT DATA GAPS

### 1. Accruals Quality
**Gap:** Historical accruals data (2020-2024)  
**Status:** BLOCKED  
**Action Required:** JT Trading Agent to backfill or provide calculation method

### 2. ESG Ratings History
**Gap:** MSCI/Sustainalytics historical ratings  
**Status:** BLOCKED (if hypothesis moves to testing)  
**Action Required:** Data subscription or alternative source

### 3. Hourly FX Data
**Gap:** TrueFX or IBKR hourly for Asian Session strategy  
**Status:** BLOCKED  
**Action Required:** JT Trading Agent to configure data feed

### 4. Options Chain Data
**Gap:** VRP, Gamma Gravity, Vol Crush strategies  
**Status:** BLOCKED  
**Action Required:** Polygon or Cboe subscription

---

## 📧 REQUEST TEMPLATE

```markdown
## DATA REQUEST - [Hypothesis Name]

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** [YYYY-MM-DD]  
**Priority:** [High/Medium/Low]

### Data Required
- **Table/Schema:** [e.g., gold.stock_metrics]
- **Columns:** [e.g., accruals_ratio, total_accruals]
- **Time Period:** [start] to [end]
- **Frequency:** [daily/weekly/monthly]
- **Universe:** [e.g., S&P 500 constituents]

### Purpose
[Explain why this data is needed for the hypothesis test]

### Blocking Status
- [ ] Blocking - Cannot proceed without this data
- [ ] Non-blocking - Can test with limitations

### Suggested Source
- [ ] Internal DB (backfill)
- [ ] External API (Bloomberg, FactSet)
- [ ] Alternative provider (Quandl, FRED)
- [ ] Calculation from existing data

### Acceptance Criteria
- [ ] Data completeness > 95%
- [ ] No look-ahead bias
- [ ] Backtest period fully covered
- [ ] Documentation provided

---

**Do not proceed with backtest until this request is fulfilled.**
```

---

## 🎯 DECISION TREE

```
Data Available?
├── YES → Proceed with backtest
└── NO 
    ├── Can use alternative? 
    │   ├── YES → Request approval from Jacky
    │   └── NO → STOP
    └── Is proxy acceptable?
        ├── YES → Request approval from Jacky
        └── NO → STOP
```

**Default: STOP when in doubt.**

---

## 📋 ACTIVE DATA REQUESTS

| Date | Hypothesis | Data Needed | Status | Request ID |
|------|------------|-------------|--------|------------|
| 2026-02-20 | Accruals Quality | Historical accruals (2020-2024) | PENDING | - |

---

## ✅ SIGN-OFF

**Policy Acknowledged:** Trade Algo Researcher  
**Policy Owner:** Jacky  
**Enforced From:** 2026-02-20  
**Review Date:** As needed

---

**Remember: Better to wait for good data than to proceed with bad data.**
