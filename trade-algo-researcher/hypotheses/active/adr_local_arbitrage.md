# Hypothesis: ADR-Local Share Arbitrage

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities (Dual-Listed)  
**Direction:** Neutral  
**Horizon:** Intraday to 1 day  
**Target Sharpe:** 1.5-2.5

---

## Core Idea

Dual-listed stocks (e.g., BABA US vs 9988.HK, TSM US vs 2330.TW) exhibit temporary mispricing during market hours overlap due to:
- Liquidity differences (US ADRs more liquid than local shares)
- Information asymmetry (news breaks in one timezone first)
- Currency effects not immediately priced

**Trade:** Buy undervalued leg, sell overvalued leg when deviation >1%

---

## Universe

### China (US ADR vs Hong Kong)
| ADR | Local | Premium/Discount Pattern |
|-----|-------|-------------------------|
| BABA | 9988.HK | ADR typically +2-5% premium |
| JD | 9618.HK | ADR +1-3% premium |
| NIO | 9866.HK | More volatile, larger deviations |
| BIDU | 9888.HK | Stable 2% premium |
| PDD | 3690.HK | Growth stock, higher volatility |

### Taiwan (US ADR vs Taiwan)
| ADR | Local | Notes |
|-----|-------|-------|
| TSM | 2330.TW | World's most traded dual-list |
| UMC | 2303.TW | Smaller cap, wider spreads |
| ASX | 3711.TW | Less liquid |

### Japan (US ADR vs Tokyo)
| ADR | Local | Notes |
|-----|-------|-------|
| SONY | 6758.T | Consumer electronics |
| TAK | 4502.T | Pharma, stable |
| MFG | 8411.T | Bank, dividend play |

---

## Signal Construction

### Deviation Calculation
```python
def adr_deviation(adr_ticker, local_ticker, fx_rate):
    """
    Calculate ADR premium/discount to local shares
    """
    adr_price = get_price(adr_ticker)  # USD
    local_price_usd = get_price(local_ticker) * fx_rate  # Convert to USD
    
    # ADR multiplier (e.g., 1 ADR = 8 ordinary shares)
    multiplier = get_adr_ratio(adr_ticker)
    local_price_adr_equiv = local_price_usd * multiplier
    
    deviation = (adr_price - local_price_adr_equiv) / local_price_adr_equiv
    
    return deviation
```

### Entry Rules
1. **Deviation >1.5%:** Short ADR, Long Local
2. **Deviation <-1.5%:** Long ADR, Short Local
3. **Hold:** Until deviation <0.5%
4. **Max hold:** 3 days (time stop)

---

## Risk Factors

1. **Currency risk:** FX moves can widen apparent deviation
2. **Short borrow:** Local shares may be hard to short
3. **Settlement:** T+2 mismatch between US and local markets
4. **Corporate actions:** Dividends, splits handled differently
5. **Liquidity:** Local markets may have wide spreads

---

## Academic Basis

**Gagnon, L. & Karolyi, G.A. (2010):** "Multi-Market Trading and Arbitrage"
- SSRN: Multi-Market Trading and Arbitrage
- Documents persistent ADR premiums between dual-listed shares
- Mean reversion within 1-3 days
- Premiums reflect liquidity and information differences

**Rabinovitch, R. et al. (2003):** "ADR pricing dynamics"
- Cross-border information transmission in dual-listed stocks
- Time zone effects on price discovery

---

## Data Requirements

- Real-time prices: US (NYSE/NASDAQ) + Local (HKEX, TWSE, TSE)
- FX rates: USD/HKD, USD/TWD, USD/JPY
- ADR ratios (shares per ADR)
- Short availability data

---

*Next step: Build real-time deviation monitor for TSM and BABA.*
