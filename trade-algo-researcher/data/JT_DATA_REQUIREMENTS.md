# Data Requirements for JT Trading Agent

**Date:** 2026-02-17  
**From:** Trade Algo Researcher  
**Priority:** High  

---

## Overview

I need historical data collected for two new strategy hypotheses. The data will be used for backtesting to validate the strategies before promoting them to Golden Strategies.

---

## Request 1: PEAD Earnings Data

### Purpose
Backtest Post-Earnings Announcement Drift (PEAD) strategy — trading stocks 1-5 days after earnings surprises.

### Required Data Fields

```csv
ticker,announcement_date,eps_actual,eps_estimate,revenue_actual,revenue_estimate,fiscal_quarter
AAPL,2024-01-25,2.18,2.10,119.58,117.92,FY24-Q1
```

**Fields:**
- `ticker` (str): Stock symbol
- `announcement_date` (date): Earnings announcement date (YYYY-MM-DD)
- `eps_actual` (float): Reported EPS
- `eps_estimate` (float): Analyst consensus mean estimate
- `revenue_actual` (float, optional): Reported revenue (in billions)
- `revenue_estimate` (float, optional): Analyst revenue consensus
- `fiscal_quarter` (str, optional): e.g., "FY24-Q1"

### Universe
S&P 100 (top 100 most liquid stocks):
```
AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, BRK-B, AVGO, WMT,
JPM, V, PG, UNH, MA, HD, LLY, MRK, PEP, COST, ABBV, KO, ADBE,
WFC, TMO, ACN, MCD, CSCO, DIS, ABT, VZ, NKE, BMY, TXN, CMCSA,
NEE, RTX, HON, PM, IBM, QCOM, SPGI, LOW, UPS, ORCL, CAT, BA,
GS, MS, DE, LMT, AMAT, INTU, GILD, MDT, BKNG, AXP, TJX, CVS,
BLK, C, SBUX, NOW, VRTX, ZTS, ISRG, MO, F, GM, T, GE, AMD,
NFLX, PYPL, INTC, PLTR, COIN, HOOD, SNOW
```

### Time Period
- Start: 2019-01-01
- End: 2024-12-31
- **Total: 6 years**

### Expected Volume
~100 stocks × 4 quarters/year × 6 years = **~2,400 records**

### Data Sources (Priority Order)
1. **Alpha Vantage** (free, 25 calls/day) — Primary source
2. **yfinance** (free) — Secondary/validation
3. **IBKR API** — If available in your infrastructure
4. **Earnings Whispers** — Paid but comprehensive
5. **Quandl/Sharadar** — Paid institutional grade

### Storage Location
```
/data/earnings/
  └── earnings_data_20260217.csv
  └── earnings_data_latest.csv (symlink to latest)
```

### Reference Implementation
See: `/data/earnings_collector.py` (skeleton implementation)

---

## Request 2: Commodity Futures Data

### Purpose
Backtest Commodity Seasonality strategy — trading natural gas, gasoline, heating oil, and corn based on historical monthly patterns.

### Required Data Fields

```csv
date,open,high,low,close,volume,commodity
2004-01-02,5.25,5.35,5.15,5.28,12345,NG
```

**Fields:**
- `date` (date): Trading date
- `open` (float): Opening price
- `high` (float): High price
- `low` (float): Low price
- `close` (float): Closing price
- `volume` (int): Trading volume
- `commodity` (str): NG, RB, HO, ZC, etc.

### Commodities Required

| Symbol | Name | Yahoo Ticker | Priority |
|--------|------|--------------|----------|
| NG | Natural Gas | NG=F | **Required** |
| RB | RBOB Gasoline | RB=F | **Required** |
| HO | Heating Oil | HO=F | **Required** |
| ZC | Corn | ZC=F | **Required** |
| ZS | Soybeans | ZS=F | Optional |
| ZW | Wheat | ZW=F | Optional |

### Time Period
- Start: 2004-01-01
- End: 2024-12-31
- **Total: 20 years**

### Continuous Contracts
Use continuous futures (already rolled) rather than individual contracts:
- `NG=F` — Natural Gas Continuous
- `RB=F` — Gasoline Continuous
- `HO=F` — Heating Oil Continuous
- `ZC=F` — Corn Continuous

### Expected Volume
~20 years × 252 trading days × 4 commodities = **~20,000 records**

### Data Sources
1. **yfinance** (free) — `yf.download('NG=F', start='2004-01-01')`
2. **IBKR API** — Historical data available
3. **Quandl** — CHRIS/continuous futures database

### Storage Location
```
/data/commodities/
  ├── NG_daily_2004_2024.csv
  ├── RB_daily_2004_2024.csv
  ├── HO_daily_2004_2024.csv
  ├── ZC_daily_2004_2024.csv
  └── combined_commodities.csv (all in one file)
```

### Reference Implementation
See: `/strategies/commodity_seasonality_backtest.py` (shows expected format)

---

## Implementation Notes

### Rate Limiting
- Alpha Vantage: 25 calls/day (free tier)
- yfinance: No strict limit, but be polite (add 0.5s delay)
- IBKR: Limited by your subscription

### Error Handling
- Log failed downloads
- Retry up to 3 times with exponential backoff
- Skip unavailable symbols (don't halt entire batch)

### Validation Checks
1. **Earnings:** Verify EPS_actual matches reported values for sample
2. **Commodities:** Check for gaps in date series
3. **Both:** Spot-check 5 random records for accuracy

### Update Frequency
Once collected, this is **static historical data** — no updates needed unless:
- Errors discovered in original collection
- Extending time period (add 2025 data next year)

---

## Integration with Researcher

### How I'll Use the Data

**PEAD:**
```python
import pandas as pd

earnings = pd.read_csv('/data/earnings/earnings_data_latest.csv')
# Calculate SUE scores
# Run backtest
# Generate performance metrics
```

**Commodity Seasonality:**
```python
ng = pd.read_csv('/data/commodities/NG_daily_2004_2024.csv')
# Calculate monthly returns
# Identify seasonal patterns
# Run backtest
```

### Expected Output
Once data is collected, I'll produce:
1. Backtest results (Sharpe, win rate, max DD)
2. Hypothesis validation report
3. If validated: strategy.yaml + promotion to Golden Strategies

---

## Timeline

| Task | Priority | Estimated Time |
|------|----------|----------------|
| PEAD earnings data | High | 2-3 days |
| Commodity futures data | High | 1-2 days |
| Validation & handoff | Medium | 1 day |

**Target completion:** 5 business days

---

## Questions?

If anything is unclear:
1. Check reference implementations in this repo
2. Read full hypothesis docs in `/hypotheses/active/`
3. Message me on Telegram

---

*This is a blocking dependency — I cannot proceed with backtests until data is available.*

**Contact:** Trade Algo Researcher (this workspace)  
**Urgency:** High — blocks Q1 2026 research initiative
