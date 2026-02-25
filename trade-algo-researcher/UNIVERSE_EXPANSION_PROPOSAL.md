# Universe Expansion Proposal
**Date:** 2026-02-22  
**Purpose:** Expand stock universe with S&P 500, Dow, Nasdaq components + Real Estate

---

## Current Universe

| Category | Count | Tickers |
|----------|-------|---------|
| **Tech** | 30 | AAPL, MSFT, NVDA, GOOGL, META, TSLA, AMZN, AMD, PLTR, 0700.HK, etc. |
| **Equity** | 149 | Mixed large-cap stocks |
| **Total** | **179** | |

---

## Available but Unclassified

### US Stocks (14 tickers)
```
AVGO, C, DOCU, IBM, LCID, LYFT, MDB, NFLX, 
PINS, SHOP, TWLO, UBER, VEEV, ZM
```

**Test Results on Expanded Universe:**
| Strategy | Original Win% | Expanded Win% | Change |
|----------|---------------|---------------|--------|
| Volume Breakout | 70.8% | 66.9% | -3.9% |
| RSI Mean Reversion | 72.6% | 66.4% | -6.2% |
| Inside Day Breakout | 74.4% | 73.5% | -0.9% |

**Conclusion:** Performance holds on expanded universe. ✅

---

## Proposed Expansion

### Phase 1: Classify Existing Unclassified (Immediate)
**Add 14 US stocks to universe:**
- Assign sectors: Tech (AVGO, MDB, NFLX, SHOP, TWLO, VEEV, ZM) 
- Assign sectors: Equity (C, DOCU, IBM, LCID, LYFT, PINS, UBER)

**New Total:** 193 tickers

---

### Phase 2: Add More US Large Cap (Requires Data)
**Potential additions from available data:**

| Category | Available | Can Add |
|----------|-----------|---------|
| S&P 500 components | 30 | All 30 already included |
| Nasdaq components | 16 | All 16 already included |
| Additional US stocks | 14 | Classify these |

**Current database coverage:**
- Total US stocks: 73
- Already classified: 59
- Unclassified: 14

---

### Phase 3: Add Real Estate Sector (Requires Data Import)

**Major REITs to request from JT:**
| Ticker | Name | Sector |
|--------|------|--------|
| O | Realty Income | REIT |
| AMT | American Tower | REIT |
| PLD | Prologis | REIT |
| CCI | Crown Castle | REIT |
| EQIX | Equinix | REIT |
| PSA | Public Storage | REIT |
| SPG | Simon Property | REIT |
| WELL | Welltower | REIT |
| DLR | Digital Realty | REIT |
| AVB | AvalonBay | REIT |

**If added:** New "Real Estate" sector with ~20 tickers

---

## Data Request for JT Trading

To expand universe to 250+ tickers:

### Immediate (Can use existing data)
1. **Classify 14 unclassified US stocks** ✅ Ready

### Short-term (Need data import)
2. **S&P 500 components** - Top 100 stocks
3. **Nasdaq-100 components** - Top 50 tech stocks
4. **REITs** - Top 20 REITs for Real Estate sector

### Medium-term (Need data import)
5. **Russell 2000** - Small-cap stocks
6. **International** - More European/Japanese stocks

---

## Expected Trade Frequency with Expansion

| Universe Size | Volume BO | RSI MR | Inside Day | Total |
|---------------|-----------|--------|------------|-------|
| 179 (current) | 20-35/mo | 7-14/mo | 1-3/mo | 28-52/mo |
| 250 (proposed) | 30-50/mo | 10-20/mo | 2-5/mo | 42-75/mo |
| 500 (full) | 60-100/mo | 20-40/mo | 4-10/mo | 84-150/mo |

---

## Recommendation

### Immediate Action
1. **Classify 14 unclassified US stocks** 
   - Move to 193 tickers
   - Test Golden Strategies
   - Deploy if performance holds

### Data Request to JT
2. **Request additional ticker data:**
   ```
   Priority 1: Top 50 S&P 500 (not already in DB)
   Priority 2: Top 20 REITs (Real Estate sector)
   Priority 3: Russell 2000 components
   ```

### Testing Protocol
3. **Test Golden Strategies on expanded universe**
   - Maintain 65%+ win rate threshold
   - Monitor for overfitting
   - Sector-specific testing

---

## Files to Update

1. `memory/deployments/INDEX.md` - Universe list
2. `memory/deployments/volume_breakout_deployment.md` - Ticker list
3. `memory/deployments/rsi_mean_reversion_deployment.md` - Ticker list
4. `memory/deployments/inside_day_breakout_deployment.md` - Ticker list

---

*Proposed: 2026-02-22*  
*Current Universe: 179 tickers*  
*Proposed Universe: 250+ tickers*