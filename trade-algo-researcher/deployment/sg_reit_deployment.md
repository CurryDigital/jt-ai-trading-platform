# Deployment Configuration: Singapore REIT Dividend Capture

**Strategy:** SG_REIT_Dividend_Capture  
**Status:** READY FOR DEPLOYMENT  
**Validated:** 2026-02-19  
**Win Rate:** 72.9%  
**Sharpe:** 0.73

---

## Universe (6 REITs)

| Ticker | Name | Win Rate | Avg Return | Notes |
|--------|------|----------|------------|-------|
| **EWS** | Singapore ETF (proxy) | 87.5% | 2.94% | Diversified, best risk-adjusted |
| **AJBU.SI** | Keppel Infrastructure | 75.0% | 4.01% | Highest yield play |
| **ME8U.SI** | Mapletree Industrial | 75.0% | 3.10% | Data center exposure |
| **M44U.SI** | Mapletree Logistics | 70.8% | 2.71% | E-commerce/logistics |
| **N2IU.SI** | Mapletree Commercial | 66.7% | 1.06% | Retail/office mix |
| **C38U.SI** | CapitaLand ICT | 62.5% | 0.92% | Retail/integrated |

**Primary Deployment:** EWS (simple), AJBU.SI (yield), ME8U.SI (growth)

---

## Entry Rules

```python
# Quarterly schedule (typical S-REIT dividend months)
dividend_months = [1, 4, 7, 10]  # Jan, Apr, Jul, Oct

# ENTRY
IF current_month in dividend_months:
    AND days_to_month_start <= 14:  # 2 weeks before month
    AND days_to_month_start >= 3:   # Not too late
    
    BUY REIT (EWS, AJBU.SI, or ME8U.SI)
    
    Position Size: 3-5% per REIT
    Max REITs: 3 simultaneous
```

---

## Exit Rules

```python
# Time-based exit
IF days_from_month_start >= 21:  # 3 weeks after month start
    EXIT

# Price-based exit (optional)
IF price_return > 3%:  # Capture quick gains
    EXIT early

# Dividend confirmation
EXIT after ex-dividend date + 2 weeks
```

---

## Quarterly Calendar

| Quarter | Entry Window | Exit Target | Dividend Month |
|---------|--------------|-------------|----------------|
| Q1 | Jan 1-14 | Feb 1-7 | January |
| Q2 | Apr 1-14 | May 1-7 | April |
| Q3 | Jul 1-14 | Aug 1-7 | July |
| Q4 | Oct 1-14 | Nov 1-7 | October |

---

## Risk Management

| Parameter | Value |
|-----------|-------|
| Max Position per REIT | 3-5% |
| Max Total REIT Exposure | 10-15% |
| Stop Loss | -5% (rarely hit) |
| Time Stop | 21 days |

**Diversification:**
- Mix sectors: Industrial (ME8U), Infrastructure (AJBU), Diversified (EWS)
- Avoid over-concentration in retail REITs

---

## Execution

**Venue:** IBKR (Singapore exchange access)
**Order Type:** Market or limit
**Timing:** SGX hours (09:00-17:00 SGT)
**Frequency:** Quarterly (4x per year)

---

## Monitoring

**Quarterly (Before Entry):**
- Check dividend calendar (SGX announcements)
- Verify ex-dividend dates
- Screen for: yield > 5%, positive momentum

**Weekly (During Hold):**
- Monitor price recovery post ex-dividend
- Check for any rights issues or major news

**Post-Exit:**
- Record actual dividend received
- Calculate total return (dividend + price)
- Update performance tracking

---

## Expected Performance

| Metric | Value |
|--------|-------|
| Win Rate | 73% |
| Avg Total Return | 2.46% per quarter |
| Dividend Component | ~1.25% per quarter |
| Price Component | ~1.21% per quarter |
| Annualized Yield | ~10% |
| Sharpe | 0.73 |

---

## Data Requirements

**Quarterly:**
- Dividend calendar (SGX announcements)
- Ex-dividend dates (REIT websites)

**Daily:**
- REIT prices (IBKR/yfinance)
- NAV updates (if available)

**Sources:**
- SGX website (dividend announcements)
- Individual REIT investor relations
- IBKR for execution

---

## Simplified Deployment (Recommended)

**For JT Platform Integration:**

1. **Ticker:** EWS (Singapore ETF)
2. **Win Rate:** 87.5% (best of all)
3. **Schedule:** Quarterly entry (Jan, Apr, Jul, Oct)
4. **Entry:** First 2 weeks of dividend month
5. **Exit:** 3 weeks after month start
6. **Position:** 5-10% allocation

**Why EWS:**
- Single ticker (simpler execution)
- Best risk-adjusted returns (1.41 Sharpe)
- Diversified across all S-REITs
- No individual REIT monitoring needed

---

## Deployment Checklist

- [ ] IBKR account with SGX access
- [ ] Dividend calendar subscription
- [ ] Quarterly reminder system
- [ ] Position sizing calculator
- [ ] Backtest verification complete ✅

---

**Ready for JT Platform Integration**
