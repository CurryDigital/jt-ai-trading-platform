# Hypothesis: Post-Earnings Announcement Drift (PEAD)

**Status:** validated (synthetic) → needs real data confirmation  
**Updated:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long (with short optionality)  
**Horizon:** Short-term (1-5 days)  
**Target Sharpe:** 1.5-2.0  
**Actual Sharpe (synthetic):** 2.43 ✅

---

## Validation Results

### Backtest Performance (Synthetic Data)
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Sharpe Ratio | **2.43** | ≥1.5 | ✅ PASS |
| Win Rate | 64.4% | ≥52% | ✅ PASS |
| Avg Return | 1.465% | - | - |
| Total Trades | 160 | - | - |
| Max Drawdown | -22.51% | <15% | ⚠️ HIGH |

### Key Findings
- Strong SUE-return relationship confirmed
- Higher SUE scores (2-3) show best returns (2.644% avg)
- Clear alpha signal in synthetic data

---

## Next Step: Real Data Validation

**Status:** Waiting for JT Trading Agent data

**Required:**
- S&P 100 earnings 2019-2024
- Actual EPS vs analyst estimates
- Announcement dates

**If real data confirms Sharpe >1.5:**
→ Promote to Golden Strategy
→ Create strategy.yaml
→ Deploy to JT platform

---

## Strategy Design (Confirmed)

### Signal
- Entry: T+1 after earnings if |SUE| > 1.5
- Exit: T+5 (time-based)
- Direction: Long if SUE > 0, Short if SUE < 0

### Risk Management
- Max position: 2% per trade
- Sector limit: 10%
- Stop loss: -3%

---

*Validated on synthetic data. Real data confirmation required.*
