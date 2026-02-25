# DEPLOYMENT PACK: S001-S006 STRATEGIES
## Clean Sector Structure (5+ Tickers = Sector, <5 = Others)

**Generated:** 2026-02-25 04:15 UTC  
**Sector Threshold:** Minimum 5 tickers to qualify as standalone sector  
**Methodology:** 3-tier validation (Train 2021-22 / Test 2023-24 / Validate 2025+)

---

# STRATEGY DIRECTORY STRUCTURE

```
20260225/
├── DEPLOYMENT.md (this file)
├── S001/
│   ├── S001-HK-Banks.md (6 tickers)
│   ├── S001-HK-Insurance.md (3 tickers → moved to Others)
│   ├── S001-Others.md (47 tickers)
│   └── S001-Summary.md
├── S002/
│   ├── S002-Others.md (52 tickers - no sector has 5+)
│   └── S002-Summary.md
├── S003/
│   ├── S003-Others.md (22 tickers - no sector has 5+)
│   └── S003-Summary.md
├── S004/
│   ├── S004-HK-Tech.md (3 tickers → moved to Others)
│   ├── S004-Others.md (19 tickers)
│   └── S004-Summary.md
├── S005/
│   ├── S005-US-Banks.md (4 tickers → moved to Others)
│   ├── S005-Others.md (22 tickers)
│   └── S005-Summary.md
└── S006/
    ├── S006-Others.md (22 tickers - no sector has 5+)
    └── S006-Summary.md
```

---

# MASTER SUMMARY TABLE

| Strategy | Logic | Total Tickers | # Sectors (5+) | # Others | Universe Avg Test | Universe Avg Val | Est. Annual Trades |
|----------|-------|---------------|----------------|----------|-------------------|------------------|-------------------|
| **S001** | RSI <25, Hold 10d | **56** | **1** | **55** | **76.4%** | **78.2%** | ~500 |
| **S002** | 3-Day Panic, Hold 5d | **52** | **0** | **52** | **62.5%** | **65.8%** | ~800 |
| **S003** | Gap >2%, Hold 3d | **22** | **0** | **22** | **68.2%** | **65.4%** | ~150 |
| **S004** | Volume >2.5x, Hold 5d | **22** | **0** | **22** | **71.3%** | **74.2%** | ~200 |
| **S005** | Price >SMA50, Hold 15d | **26** | **0** | **26** | **64.8%** | **67.1%** | ~600 |
| **S006** | Friday <-1%, Hold 5d | **22** | **0** | **22** | **67.2%** | **66.8%** | ~250 |

**TOTAL UNIVERSE: ~200 tickers across 6 strategies**
**STANDALONE SECTORS (5+ tickers): 1 only (S001-HK-Banks)**

---

# S001: RSI MEAN REVERSION

## Strategy Overview
**Logic:** RSI(14) < 25 (extreme oversold), Hold 10 days  
**Total Tickers:** 56  
**Universe Avg:** Test 76.4% / Validate 78.2%  
**Standalone Sectors:** 1 (HK Banks)  
**Others Bucket:** 50 tickers

---

## SECTOR 1: HK BANKS (6 tickers)
**Qualifies as standalone sector: YES (≥5 tickers)**

**Sector Win Rate:** Test 88.9% / Validate 93.3%  
**Total Trades:** 147  
**Sector Notes:** Defensive dividend stocks, strong mean reversion in large-cap Chinese banks

| # | Ticker | Name | Exchange | Test WR | Val WR | Trades | Status | Allocation |
|---|--------|------|----------|---------|--------|--------|--------|------------|
| 1 | 1398.HK | ICBC | HKEX | 100.0% | 100.0% | 19 | 🏆 | 15% |
| 2 | 3988.HK | Bank of China | HKEX | 100.0% | 100.0% | 8 | 🏆 | 15% |
| 3 | 3328.HK | Bank of Communications | HKEX | 100.0% | 90.9% | 16 | 🏆 | 15% |
| 4 | 2388.HK | BOC Hong Kong | HKEX | 92.9% | 100.0% | 28 | 🏆 | 15% |
| 5 | 0939.HK | CCB | HKEX | 87.5% | 72.0% | 37 | ✅ | 15% |
| 6 | 0005.HK | HSBC Holdings | HKEX | 70.0% | 100.0% | 20 | ✅ | 15% |
| 7 | 3968.HK | China Merchants Bank | HKEX | 76.5% | 100.0% | 47 | ✅ | 10% |

**File:** `S001/S001-HK-Banks.md`

---

## SECTOR 2: OTHERS (50 tickers)
**Qualifies as standalone sector: NO (<5 tickers each)**

**Consolidated from:**
- HK Insurance (3 tickers)
- HK Utilities (2 tickers)  
- HK Property (2 tickers)
- CN Banks (1 ticker)
- CN Pharma (1 ticker)
- CN Property (1 ticker)
- CN Consumer (2 tickers)
- CN Energy (2 tickers)
- HK Tech (1 ticker)
- HK Consumer (1 ticker)
- HK Transport (1 ticker)
- US Tech (4 tickers)
- US Consumer (3 tickers)
- US Semiconductors (1 ticker)
- Crypto (4 tickers)
- FX (3 tickers)
- Commodities (2 tickers)
- Diversified (10 tickers)

**Bucket Win Rate:** Test 72.1% / Validate 73.8%  
**Total Trades:** 903  
**Max Allocation per Ticker:** 2%

### Top 15 Others by Performance:

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | 0002.HK | HK Utilities | 94.1% | 66.7% | 17 |
| 2 | 0027.HK | HK Utilities | 82.9% | 100.0% | 41 |
| 3 | 000538.SZ | CN Pharma | 81.8% | 66.7% | 11 |
| 4 | 2628.HK | HK Insurance | 76.0% | 90.0% | 59 |
| 5 | 600036.SS | CN Banks | 79.3% | 55.6% | 29 |
| 6 | WMT | US Consumer | 100.0% | 50.0% | 10 |
| 7 | MCD | US Consumer | 85.0% | 72.7% | 20 |
| 8 | AMAT | US Semiconductors | 91.7% | 100.0% | 12 |
| 9 | 0066.HK | HK Transport | 71.4% | 92.3% | 49 |
| 10 | 2319.HK | HK Consumer | 73.2% | 66.7% | 56 |
| 11 | PLTR | US Tech | 95.5% | 70.6% | 22 |
| 12 | ASML | US Tech | 73.7% | 100.0% | 19 |
| 13 | SOL-USD | Crypto | 84.6% | 50.0% | 26 |
| 14 | SHOP | US Tech | 76.5% | 65.0% | 34 |
| 15 | 601318.SS | CN Insurance | 68.6% | 90.9% | 35 |

**File:** `S001/S001-Others.md` (full list of 50 tickers)

---

## S001 BUY SIGNAL

**ENTRY CONDITIONS (ALL must be met):**

1. **RSI(14) < 25**
   - Calculate RSI using closing prices
   - Period = 14 days
   - Must be strictly below 25.0

2. **Entry Execution:**
   - **Trigger:** At market open next trading day after signal
   - **Order Type:** Market order
   - **Position Sizing:** 
     - HK Banks: Equal weight across triggered tickers (max 2 concurrent)
     - Others: 2% max per ticker

**EXAMPLE:**
```
Date: 2024-03-15
1398.HK Close: $4.20
RSI(14): 23.5 (BELOW 25 ✓)
SIGNAL: BUY at next market open
```

---

## S001 SELL SIGNAL

**EXIT CONDITIONS:**

1. **Time-Based Exit ONLY:** 10 trading days after entry
   - Exit at market close on day 10

2. **No stop loss, no profit target**

**EXAMPLE:**
```
Entry: 2024-03-18
Exit: 2024-04-01 (10 trading days)
Action: SELL at market close
```

---

# S002: 3-DAY PANIC REVERSAL

## Strategy Overview
**Logic:** 3 consecutive down days, buy Day 3 close, hold 5 days  
**Total Tickers:** 52  
**Standalone Sectors:** 0 (no sector has 5+ tickers)  
**Others Bucket:** 52 tickers  
**Universe Avg:** Test 62.5% / Validate 65.8%

---

## ALL TICKERS: OTHERS (52 tickers)

**Qualifies as standalone sector: NO**  
**Bucket Win Rate:** Test 62.5% / Validate 65.8%  
**Total Trades:** 1,946  
**Max Allocation per Ticker:** 2%

### Top 20 by Performance:

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | GE | US Industrials | 73.3% | 88.9% | 30 |
| 2 | NVDA | US Tech | 72.5% | 56.5% | 40 |
| 3 | COST | US Consumer | 72.1% | 54.1% | 43 |
| 4 | QQQ | ETF | 71.0% | 66.7% | 31 |
| 5 | NOW | US Tech | 70.0% | 50.0% | 30 |
| 6 | ORCL | US Tech | 70.0% | 62.1% | 40 |
| 7 | SPY | ETF | 70.3% | 72.7% | 37 |
| 8 | LINK-USD | Crypto | 68.7% | 58.9% | 67 |
| 9 | 0762.HK | HK Telecom | 68.6% | 51.2% | 51 |
| 10 | TSM | Semiconductors | 67.3% | 52.2% | 52 |
| 11 | 0941.HK | HK Telecom | 65.3% | 58.3% | 49 |
| 12 | ASML | Semiconductors | 64.1% | 60.0% | 39 |
| 13 | 0005.HK | HK Banks | 67.6% | 73.7% | 34 |
| 14 | 3328.HK | HK Banks | 62.5% | 81.8% | 40 |
| 15 | 3988.HK | HK Banks | 58.8% | 52.9% | 34 |
| 16 | 0939.HK | HK Banks | 56.1% | 90.0% | 41 |
| 17 | 0001.HK | HK Property | 64.4% | 64.7% | 59 |
| 18 | 300750.SZ | CN EV | 61.9% | 56.8% | 84 |
| 19 | 000333.SZ | CN Property | 63.5% | 79.2% | 52 |
| 20 | 6862.HK | HK Consumer | 60.6% | 61.3% | 66 |

**File:** `S002/S002-Others.md` (full list of 52 tickers)

---

## S002 BUY SIGNAL

**ENTRY CONDITIONS:**

1. **3 Consecutive Down Days**
   ```
   Close[t-3] > Close[t-2] > Close[t-1] > Close[t]
   ```

2. **Entry Execution:**
   - **Trigger:** At market close on Day 3 (today)
   - **Order Type:** Market order
   - **Position Sizing:** 2% max per ticker

---

## S002 SELL SIGNAL

**EXIT CONDITIONS:**

1. **Time-Based Exit:** 5 trading days after entry

---

# S003: GAP DOWN RECOVERY

## Strategy Overview
**Logic:** Gap down >2%, buy at open, hold 3 days  
**Total Tickers:** 22  
**Standalone Sectors:** 0  
**Others Bucket:** 22 tickers  
**Universe Avg:** Test 68.2% / Validate 65.4%

---

## ALL TICKERS: OTHERS (22 tickers)

**Top Performers:**

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | CAT | US Industrials | 90.9% | 50.0% | 11 |
| 2 | 1810.HK | HK Tech | 78.9% | 58.3% | 19 |
| 3 | FDX | US Industrials | 83.3% | 70.0% | 6 |
| 4 | 688126.SS | CN Tech | 80.0% | 66.7% | 5 |
| 5 | BA | US Industrials | 66.7% | 62.5% | 18 |
| 6 | V | US Financial | 80.0% | 60.0% | 5 |
| 7 | 2313.HK | HK Consumer | 68.9% | 57.1% | 45 |
| 8 | UBER | US Transport | 70.6% | 66.7% | 17 |
| 9 | PLTR | US Tech | 66.0% | 62.1% | 53 |
| 10 | NVDA | US Tech | 60.7% | 64.3% | 28 |

**File:** `S003/S003-Others.md`

---

# S004: VOLUME SPIKE BREAKOUT

## Strategy Overview
**Logic:** Volume >2.5x 20-day avg, hold 5 days  
**Total Tickers:** 22  
**Standalone Sectors:** 0  
**Others Bucket:** 22 tickers  
**Universe Avg:** Test 71.3% / Validate 74.2%

---

## ALL TICKERS: OTHERS (22 tickers)

**Top Performers:**

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | 2318.HK | HK Insurance | 90.0% | 100.0% | 10 |
| 2 | BTC-USD | Crypto | 100.0% | 75.0% | 6 |
| 3 | 0027.HK | HK Utilities | 83.3% | 100.0% | 6 |
| 4 | 9988.HK | HK Tech | 80.0% | 80.0% | 5 |
| 5 | AMAT | US Semiconductors | 80.0% | 100.0% | 5 |
| 6 | F | US Auto | 80.0% | 80.0% | 5 |
| 7 | 1024.HK | HK Tech | 90.9% | 66.7% | 11 |
| 8 | 0762.HK | HK Telecom | 75.0% | 70.0% | 16 |
| 9 | 9999.HK | HK Tech | 66.7% | 80.0% | 6 |
| 10 | 2331.HK | HK Consumer | 75.0% | 50.0% | 12 |

**File:** `S004/S004-Others.md`

---

# S005: TREND FOLLOWING

## Strategy Overview
**Logic:** Price > SMA(50), hold 15 days  
**Total Tickers:** 26  
**Standalone Sectors:** 0  
**Others Bucket:** 26 tickers  
**Universe Avg:** Test 64.8% / Validate 67.1%

---

## ALL TICKERS: OTHERS (26 tickers)

**Top Performers:**

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | SPY | ETF | 73.5% | 81.8% | 351 |
| 2 | QQQ | ETF | 72.2% | 72.2% | 353 |
| 3 | GE | US Industrials | 73.5% | 66.7% | 355 |
| 4 | 0883.HK | HK Energy | 66.8% | 60.8% | 274 |
| 5 | USDJPY=X | FX | 70.2% | 63.1% | 322 |
| 6 | HD | US Consumer | 69.0% | 57.9% | 300 |
| 7 | AAPL | US Tech | 67.7% | 64.7% | 282 |
| 8 | META | US Tech | 67.3% | 56.1% | 349 |
| 9 | JPM | US Banks | 65.9% | 64.7% | 334 |
| 10 | BAC | US Banks | 65.1% | 63.6% | 281 |

**File:** `S005/S005-Others.md`

---

# S006: MONDAY EFFECT

## Strategy Overview
**Logic:** Friday decline >1%, buy Monday, hold 5 days  
**Total Tickers:** 22  
**Standalone Sectors:** 0  
**Others Bucket:** 22 tickers  
**Universe Avg:** Test 67.2% / Validate 66.8%

---

## ALL TICKERS: OTHERS (22 tickers)

**Top Performers:**

| Rank | Ticker | Sector | Test | Val | Trades |
|------|--------|--------|------|-----|--------|
| 1 | PL=F | Commodities | 78.9% | 58.8% | 19 |
| 2 | MSFT | US Tech | 77.8% | 58.3% | 18 |
| 3 | 000333.SZ | CN Property | 72.2% | 66.7% | 18 |
| 4 | AAPL | US Tech | 72.7% | 75.0% | 11 |
| 5 | CRWD | US Tech | 70.8% | 56.2% | 24 |
| 6 | SPY | ETF | 70.0% | 75.0% | 10 |
| 7 | QQQ | ETF | 69.2% | 70.0% | 13 |
| 8 | JPM | US Banks | 80.0% | 63.6% | 15 |
| 9 | GE | US Industrials | 61.5% | 80.0% | 13 |
| 10 | CRM | US Tech | 66.7% | 71.4% | 15 |

**File:** `S006/S006-Others.md`

---

# CROSS-STRATEGY CHAMPIONS

Tickers performing on **3+ strategies** (Tier 1 deploy):

| Ticker | Name | Strategies | Best Sector | Priority |
|--------|------|------------|-------------|----------|
| **0005.HK** | HSBC | S001, S002 | HK Banks | 🔥 HIGH |
| **NVDA** | NVIDIA | S002, S003, S005, S006 | US Tech | 🔥 HIGH |
| **GE** | General Electric | S002, S005, S006 | US Industrials | 🔥 HIGH |
| **AAPL** | Apple | S001, S003, S005, S006 | US Tech | 🔥 HIGH |
| **PLTR** | Palantir | S001, S003, S004, S005 | US Tech | 🔥 HIGH |
| **0883.HK** | CNOOC | S003, S004, S005, S006 | HK Energy | 🔥 HIGH |
| **GOOGL** | Alphabet | S002, S005, S006 | US Tech | MEDIUM |
| **1810.HK** | Xiaomi | S002, S003, S004, S005 | HK Tech | 🔥 HIGH |
| **0939.HK** | CCB | S001, S002 | HK Banks | MEDIUM |

---

# DEPLOYMENT RECOMMENDATIONS

## Tier 1: Champions (3+ strategies)
**Allocation:** 5% per ticker
- 0005.HK, NVDA, GE, AAPL, PLTR, 0883.HK, 1810.HK

## Tier 2: Strong Performers (2 strategies)
**Allocation:** 3% per ticker
- GOOGL, 0939.HK, 1398.HK, 3988.HK, JPM, WMT, etc.

## Tier 3: Diversification (1 strategy)
**Allocation:** 2% per ticker
- All remaining tickers in Others buckets

---

# RISK MANAGEMENT

## Per-Strategy Limits:
| Strategy | Max Capital | Max Concurrent Positions |
|----------|-------------|--------------------------|
| S001 | 30% | 12 (6 HK Banks + 6 Others) |
| S002 | 25% | 10 |
| S003 | 10% | 4 |
| S004 | 15% | 5 |
| S005 | 20% | 8 |
| S006 | 10% | 4 |

## Per-Ticker Limit:
- **Tier 1 (Champions):** Max 10% total exposure
- **Tier 2:** Max 6% total exposure
- **Tier 3:** Max 4% total exposure

## Exit Rules:
- ALL strategies: Time-based exit only (no stops)
- Position sizing used for risk control

---

*Clean sector structure: 1 standalone sector (S001-HK-Banks), 5 Others buckets*
*Total: ~200 tickers, 1 sector + 5 Others files*