# Hypothesis: Credit-Equity Lag (HYG/SPY Divergence)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Cross-Asset (Credit + Equities)  
**Direction:** Long/Short  
**Horizon:** 1-2 weeks  
**Target Sharpe:** 1.0-1.5

---

## Core Idea

High yield bonds (HYG, JNK) lead equity markets during credit stress periods. When credit markets freeze or sell off, equity markets typically follow with 3-5 day lag.

**Mechanism:**
- Credit markets are "smarter" — institutional investors, better information
- Equity retail investors slower to react to credit stress
- Corporate bond spreads reflect default risk before stocks price it

**Trade:** When HYG drops >2% in 3 days, short SPY with 1-day lag

---

## Academic Foundation

**Kwan (1996):** "Can bond yields predict equity returns?"
- Corporate bond spreads lead equity returns
- Information diffusion from credit to equity markets

**Gilchrist & Zakrajšek (2012):** "Credit Spreads and Business Cycle Fluctuations"
- Excess bond premium predicts economic activity
- Credit market as leading indicator

**Bharath & Shumway (2008):** "Forecasting Default with the Merton Distance to Default Model"
- Credit spreads reflect default probability
- Stocks adjust slower to default risk changes

---

## Signal Construction

### Credit Stress Indicator
```python
def credit_stress_signal(hyg_returns, spy_returns, lookback=3):
    """
    Generate signal when credit leads equity down
    """
    # HYG performance over lookback period
    hyg_change = hyg_returns.rolling(lookback).sum()
    
    # SPY performance over same period
    spy_change = spy_returns.rolling(lookback).sum()
    
    # Divergence: HYG down, SPY flat or up
    divergence = (hyg_change < -0.02) & (spy_change > -0.01)
    
    return divergence
```

### Trading Rules
1. **Entry:** HYG down >2% over 3 days, SPY flat/down less
2. **Position:** Short SPY (or long SPY puts)
3. **Hold:** 5-10 days for equity catch-down
4. **Exit:** HYG stabilizes or SPY catches down

---

## Universe

| Instrument | Ticker | Role |
|------------|--------|------|
| High Yield Bonds | HYG | Lead indicator |
| High Yield Bonds | JNK | Confirmation |
| Investment Grade | LQD | Risk-off comparison |
| S&P 500 | SPY | Lagging indicator (short) |
| VIX | VIX | Volatility confirmation |

---

## Historical Examples

### February 2020 (Pre-COVID)
- HYG started dropping Feb 14
- SPY peaked Feb 19, then crashed
- Lag: 3-5 days

### September 2021 (Evergrande)
- High yield stress Sep 13
- SPY drop Sep 20
- Lag: 1 week

### 2022 Bear Market
- Multiple HYG leading signals
- Consistent 3-7 day lag to SPY

---

## Risk Factors

1. **Fed intervention:** QE can decouple credit/equity
2. **Flight to quality:** Treasuries rally while HY sells off
3. **Sector concentration:** HY heavy on energy/telecom
4. **False signals:** HYG can bounce while SPY hasn't dropped yet

---

## Data Requirements

- HYG/JNK daily prices
- SPY daily prices  
- High yield spreads (BofA ML index)
- VIX for volatility context

---

*Next step: Collect 2019-2024 HYG and SPY data, measure lead-lag correlation.*
