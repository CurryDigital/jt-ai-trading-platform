# Hypothesis: Peer Firm Information Lag (Shell ↔ Sinopec Pattern)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** Short-term (1-3 days)  
**Target Sharpe:** 1.2-1.8

---

## Core Idea

When major integrated oil company (Shell, Exxon, Chevron) announces earnings or strategic shift, smaller national oil companies and regional E&Ps lag by 1-3 days in price adjustment.

**Examples:**
- Shell announces earnings miss → Sinopec, PetroChina drop next day
- XOM announces capex increase → Energy services (SLB, Halliburton) rally with 2-day lag
- BP announces renewables pivot → Peers re-rate gradually

---

## Academic Foundation

**Menzly & Ozbas (2010):** "Market Segmentation and Cross-Predictability of Returns"
- Firms with shared analyst coverage show return predictability
- Information diffuses slowly across peer groups

**Cohen & Frazzini (2008):** "Economic Links and Predictable Returns"
- Customer-supplier links create lead-lag effects
- Peers with similar input costs also linked

**Green et al. (2011):** "The Value of Client Access in the Mutual Fund Industry"
- Institutional trading creates information cascades

---

## Universe

### Majors (Lead)
| Ticker | Company | Market Cap |
|--------|---------|------------|
| XOM | Exxon Mobil | $400B+ |
| CVX | Chevron | $300B+ |
| SHEL | Shell | $200B+ |
| BP | BP | $100B+ |
| TTE | TotalEnergies | $150B+ |

### Nationals (Lag)
| Ticker | Company | Market Cap | Lead Correlation |
|--------|---------|------------|------------------|
| SNP | Sinopec | $80B | Shell, XOM |
| PTR | PetroChina | $200B | Shell, XOM |
| EC | Ecopetrol | $30B | XOM, CVX |
| PBR | Petrobras | $70B | XOM, CVX |
| RELIANCE.NS | Reliance | $200B | Shell, BP |

### Energy Services (Secondary Lag)
| Ticker | Company | Driver |
|--------|---------|--------|
| SLB | Schlumberger | E&P capex |
| HAL | Halliburton | E&P capex |
| NOV | NOV | Rig counts |
| FTI | TechnipFMC | Offshore projects |

---

## Signal Construction

### Primary Signal
```python
def peer_lag_signal(lead_ticker, event_date, event_type):
    """
    Generate signals from major peer announcements
    """
    # Get lead stock reaction
    lead_return = get_return(lead_ticker, event_date, event_date+1)
    
    # Map to lagging peers
    peer_mapping = {
        'XOM': ['SNP', 'PTR', 'EC', 'SLB', 'HAL'],
        'CVX': ['PBR', 'EC', 'SLB', 'HAL'],
        'SHEL': ['SNP', 'PTR', 'BP', 'REL'],
        'BP': ['SHEL', 'TTE', 'REL'],
    }
    
    # Determine direction and magnitude
    if event_type == 'earnings_miss' and lead_return < -0.05:
        return {peer: 'short' for peer in peer_mapping.get(lead_ticker, [])}
    elif event_type == 'earnings_beat' and lead_return > 0.05:
        return {peer: 'long' for peer in peer_mapping.get(lead_ticker, [])}
    elif event_type == 'capex_increase':
        return {svc: 'long' for svc in ['SLB', 'HAL', 'NOV']}
    
    return {}
```

### Entry Rules
1. **Day 0 (Event):** Major announces earnings/strategy
2. **Day 1:** Observe market reaction (don't trade yet)
3. **Day 2:** If lead moved >5%, enter position on laggards
4. **Hold:** 1-3 days for catch-up

### Exit Rules
- Time stop: Exit Day 5 regardless
- Profit target: 50% of lead's move
- Stop loss: -2%

---

## Expected Performance

### Backtest Assumptions
- Period: 2019-2024
- Universe: 5 majors → 10 nationals/services
- Events: Quarterly earnings + strategic announcements
- Slippage: 5bps

### Target Metrics
| Metric | Target | Conservative |
|--------|--------|--------------|
| Sharpe Ratio | 1.5 | 1.2 |
| Win Rate | 58% | 55% |
| Avg Return/Trade | 1.2% | 0.8% |
| Max Drawdown | 12% | 18% |

---

## Risk Factors

1. **Currency risk:** Nationals trade in local currency (SNP in USD but China exposure)
2. **Sovereign risk:** National oil companies subject to government intervention
3. **Time zone gaps:** Asian markets closed when US majors announce
4. **False positives:** Not all major announcements are peer-relevant
5. **Crowding:** If widely known, arbitrage opportunity disappears

---

## Data Requirements

| Data | Source | Priority |
|------|--------|----------|
| Earnings dates | yfinance / FMP | Required |
| Earnings surprises | FMP / IBKR | Required |
| News alerts | RavenPack / manual | High |
| Price data | yfinance | Required |
| Analyst coverage | IBKR / manual | Medium |

---

## Validation Plan

### Phase 1: Correlation Analysis (Week 1)
- [ ] Calculate rolling correlations between majors and nationals
- [ ] Measure optimal lag (τ) for each pair
- [ ] Identify strongest lead-lag relationships

### Phase 2: Event Study (Week 2)
- [ ] Collect 5 years of earnings announcements
- [ ] Measure price response: Day 0 (lead), Day 1-3 (peers)
- [ ] Calculate average catch-up return

### Phase 3: Backtest (Week 3)
- [ ] Simulate entry on Day 2, exit Day 5
- [ ] Test different thresholds (3%, 5%, 7% lead moves)
- [ ] Risk management parameter optimization

### Phase 4: Live Test (Week 4+)
- [ ] Paper trade for 1 quarter
- [ ] Measure real-world slippage
- [ ] Adjust for market regime changes

---

## Extensions

### Other Sectors
- **Banks:** JPM → regional banks (PNFP, TCBI)
- **Semiconductors:** NVDA → memory (MU, WDC)
- **Retail:** AMZN → retail ETF components
- **Airlines:** DAL → ULCCs (SAVE, ULCC)

### Geographic Variants
- **Europe:** Shell/BP → ENI, Repsol
- **Asia:** PetroChina → CNOOC, Sinopec
- **LatAm:** Petrobras → Ecopetrol, YPF

---

## References

1. Menzly, L., & Ozbas, O. (2010). Market segmentation and cross-predictability of returns. *The Journal of Finance*, 65(4), 1555-1580.
2. Cohen, L., & Frazzini, A. (2008). Economic links and predictable returns. *The Journal of Finance*, 63(4), 1977-2011.
3. Green, J., Hand, J. R., & Zhang, X. F. (2011). The value of client access in the mutual fund industry. *SSRN*.

---

*Next step: Collect earnings calendar data and run correlation analysis.*
