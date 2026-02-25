# DEPLOYMENT PACK: S001-S006 STRATEGIES
## Clean Sector Structure (4+ Tickers = Sector, <4 = Others)

**Generated:** 2026-02-25 04:30 UTC  
**Sector Threshold:** Minimum 4 tickers to qualify as standalone sector  
**Methodology:** 3-tier validation (Train 2021-22 / Test 2023-24 / Validate 2025+)

---

# MASTER SUMMARY TABLE

| Strategy | Logic | Total Tickers | # Sectors (4+) | # Others | Universe Avg Test | Universe Avg Val | Est. Annual Trades |
|----------|-------|---------------|----------------|----------|-------------------|------------------|-------------------|
| **S001** | RSI <25, Hold 10d | **56** | **3** | **39** | **76.4%** | **78.2%** | ~500 |
| **S002** | 3-Day Panic, Hold 5d | **52** | **1** | **39** | **62.5%** | **65.8%** | ~800 |
| **S003** | Gap >2%, Hold 3d | **22** | **0** | **22** | **68.2%** | **65.4%** | ~150 |
| **S004** | Volume >2.5x, Hold 5d | **22** | **1** | **16** | **71.3%** | **74.2%** | ~200 |
| **S005** | Price >SMA50, Hold 15d | **26** | **1** | **18** | **64.8%** | **67.1%** | ~600 |
| **S006** | Friday <-1%, Hold 5d | **22** | **0** | **22** | **67.2%** | **66.8%** | ~250 |

**TOTAL UNIVERSE: ~200 tickers across 6 strategies**
**STANDALONE SECTORS (4+ tickers): 6 total**

---

# DIRECTORY STRUCTURE (4+ Threshold)

```
20260225/
├── DEPLOYMENT.md (this file)
├── S001/
│   ├── S001-HK-Banks.md (7 tickers) ✅
│   ├── S001-US-Tech.md (4 tickers) ✅
│   ├── S001-Crypto.md (4 tickers) ✅
│   └── S001-Others.md (41 tickers)
├── S002/
│   ├── S002-HK-Banks.md (4 tickers) ✅
│   └── S002-Others.md (48 tickers)
├── S003/
│   └── S003-Others.md (22 tickers)
├── S004/
│   ├── S004-HK-Tech.md (4 tickers) ✅
│   └── S004-Others.md (18 tickers)
├── S005/
│   ├── S005-US-Banks.md (4 tickers) ✅
│   └── S005-Others.md (22 tickers)
└── S006/
    └── S006-Others.md (22 tickers)
```

**Total: 6 standalone sectors + 6 Others files**

---

# S001: RSI MEAN REVERSION

## Strategy Overview
**Logic:** RSI(14) < 25, Hold 10 days  
**Total Tickers:** 56  
**Universe Avg:** Test 76.4% / Validate 78.2%  
**Standalone Sectors:** 3  
**Others Bucket:** 41 tickers

---

## SECTOR 1: HK BANKS (7 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 88.9% / Validate 93.3%  
**Total Trades:** 176

| Ticker | Name | Test | Val | Trades | Allocation |
|--------|------|------|-----|--------|------------|
| 1398.HK | ICBC | 100% | 100% | 19 | 15% |
| 3988.HK | Bank of China | 100% | 100% | 8 | 15% |
| 3328.HK | Bank of Comm | 100% | 91% | 16 | 15% |
| 2388.HK | BOC HK | 93% | 100% | 28 | 15% |
| 0939.HK | CCB | 88% | 72% | 37 | 15% |
| 0005.HK | HSBC | 70% | 100% | 20 | 15% |
| 3968.HK | CMB | 77% | 100% | 47 | 10% |

**File:** `S001/S001-HK-Banks.md`

---

## SECTOR 2: US TECH (4 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 76.0% / Validate 72.5%  
**Total Trades:** 97

| Ticker | Name | Test | Val | Trades | Allocation |
|--------|------|------|-----|--------|------------|
| PLTR | Palantir | 96% | 71% | 22 | 25% |
| ASML | ASML | 74% | 100% | 19 | 25% |
| AMD | AMD | 61% | 67% | 23 | 25% |
| ZM | Zoom | 65% | 75% | 26 | 25% |

**File:** `S001/S001-US-Tech.md`

---

## SECTOR 3: CRYPTO (4 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 74.3% / Validate 58.9%  
**Total Trades:** 153

| Ticker | Name | Test | Val | Trades | Allocation |
|--------|------|------|-----|--------|------------|
| SOL-USD | Solana | 85% | 50% | 26 | 25% |
| ADA-USD | Cardano | 75% | 70% | 47 | 25% |
| MSTR | MicroStrategy | 67% | 53% | 21 | 25% |
| DOT-USD | Polkadot | 63% | 51% | 59 | 25% |

**File:** `S001/S001-Crypto.md`

---

## SECTOR 4: OTHERS (41 tickers)
**Qualifies: NO (<4 tickers per sub-sector)**

Consolidated: HK Insurance (3), HK Utilities (2), HK Property (2), CN Banks (1), CN Pharma (1), CN Property (1), CN Consumer (2), CN Energy (2), HK Tech (1), HK Consumer (1), HK Transport (1), US Consumer (3), US Semiconductors (1), FX (3), Commodities (2), China Property (1), HK Tech (1), China Insurance (1), US Growth Tech (4), Diversified (5)

**Bucket Win Rate:** Test 74.2% / Validate 76.8%

**Top 10 Others:**

| Rank | Ticker | Sub-Sector | Test | Val |
|------|--------|------------|------|-----|
| 1 | 0002.HK | HK Utilities | 94% | 67% |
| 2 | 0027.HK | HK Utilities | 83% | 100% |
| 3 | 000538.SZ | CN Pharma | 82% | 67% |
| 4 | 2628.HK | HK Insurance | 76% | 90% |
| 5 | 600036.SS | CN Banks | 79% | 56% |
| 6 | WMT | US Consumer | 100% | 50% |
| 7 | MCD | US Consumer | 85% | 73% |
| 8 | AMAT | US Semiconductors | 92% | 100% |
| 9 | 0066.HK | HK Transport | 71% | 92% |
| 10 | 2319.HK | HK Consumer | 73% | 67% |

**File:** `S001/S001-Others.md`

---

# S002: 3-DAY PANIC REVERSAL

## Strategy Overview
**Logic:** 3 consecutive down days, Hold 5 days  
**Total Tickers:** 52  
**Standalone Sectors:** 1  
**Others Bucket:** 48 tickers

---

## SECTOR 1: HK BANKS (4 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 61.3% / Validate 74.5%

| Ticker | Name | Test | Val | Trades |
|--------|------|------|-----|--------|
| 0005.HK | HSBC | 68% | 74% | 34 |
| 3328.HK | Bank of Comm | 63% | 82% | 40 |
| 3988.HK | Bank of China | 59% | 53% | 34 |
| 0939.HK | CCB | 56% | 90% | 41 |

**File:** `S002/S002-HK-Banks.md`

---

## SECTOR 2: OTHERS (48 tickers)
**Top 10:**

| Rank | Ticker | Sector | Test | Val |
|------|--------|--------|------|-----|
| 1 | GE | US Industrials | 73% | 89% |
| 2 | NVDA | US Tech | 73% | 57% |
| 3 | COST | US Consumer | 72% | 54% |
| 4 | QQQ | ETF | 71% | 67% |
| 5 | SPY | ETF | 70% | 73% |
| 6 | NOW | US Tech | 70% | 50% |
| 7 | ORCL | US Tech | 70% | 62% |
| 8 | LINK-USD | Crypto | 69% | 59% |
| 9 | 0762.HK | HK Telecom | 69% | 51% |
| 10 | TSM | Semiconductors | 67% | 52% |

**File:** `S002/S002-Others.md`

---

# S003: GAP DOWN RECOVERY

## Strategy Overview
**Total Tickers:** 22  
**Standalone Sectors:** 0  
**Others Bucket:** 22 tickers

(No sector has 4+ tickers)

**Top 10 Others:**

| Rank | Ticker | Sector | Test | Val |
|------|--------|--------|------|-----|
| 1 | CAT | US Industrials | 91% | 50% |
| 2 | FDX | US Industrials | 83% | 70% |
| 3 | 1810.HK | HK Tech | 79% | 58% |
| 4 | 688126.SS | CN Tech | 80% | 67% |
| 5 | V | US Financial | 80% | 60% |
| 6 | 2313.HK | HK Consumer | 69% | 57% |
| 7 | UBER | US Transport | 71% | 67% |
| 8 | PLTR | US Tech | 66% | 62% |
| 9 | BA | US Industrials | 67% | 63% |
| 10 | GE | US Industrials | 67% | 64% |

**File:** `S003/S003-Others.md`

---

# S004: VOLUME SPIKE BREAKOUT

## Strategy Overview
**Total Tickers:** 22  
**Standalone Sectors:** 1  
**Others Bucket:** 18 tickers

---

## SECTOR 1: HK TECH (4 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 70.1% / Validate 81.7%

| Ticker | Name | Test | Val | Trades |
|--------|------|------|-----|--------|
| 9988.HK | Alibaba | 80% | 80% | 5 |
| 9999.HK | NetEase | 67% | 80% | 6 |
| 1024.HK | Kuaishou | 91% | 67% | 11 |
| 0700.HK | Tencent | 60% | 100% | 5 |

**File:** `S004/S004-HK-Tech.md`

---

## SECTOR 2: OTHERS (18 tickers)
**Top 10:**

| Rank | Ticker | Sector | Test | Val |
|------|--------|--------|------|-----|
| 1 | 2318.HK | HK Insurance | 90% | 100% |
| 2 | BTC-USD | Crypto | 100% | 75% |
| 3 | 0027.HK | HK Utilities | 83% | 100% |
| 4 | AMAT | US Semiconductors | 80% | 100% |
| 5 | F | US Auto | 80% | 80% |
| 6 | 0762.HK | HK Telecom | 75% | 70% |
| 7 | 2331.HK | HK Consumer | 75% | 50% |
| 8 | NOC | US Defense | 67% | 100% |
| 9 | FDX | US Transport | 67% | 100% |
| 10 | 688981.SS | CN Tech | 69% | 50% |

**File:** `S004/S004-Others.md`

---

# S005: TREND FOLLOWING

## Strategy Overview
**Total Tickers:** 26  
**Standalone Sectors:** 1  
**Others Bucket:** 22 tickers

---

## SECTOR 1: US BANKS (4 tickers) ✅
**Qualifies: YES (≥4 tickers)**

**Sector Win Rate:** Test 64.0% / Validate 68.7%

| Ticker | Name | Test | Val | Trades |
|--------|------|------|-----|--------|
| JPM | JPMorgan | 66% | 65% | 334 |
| BAC | Bank of America | 65% | 64% | 281 |
| GS | Goldman Sachs | 64% | 74% | 317 |
| C | Citigroup | 62% | 73% | 270 |

**File:** `S005/S005-US-Banks.md`

---

## SECTOR 2: OTHERS (22 tickers)
**Top 10:**

| Rank | Ticker | Sector | Test | Val |
|------|--------|--------|------|-----|
| 1 | SPY | ETF | 74% | 82% |
| 2 | QQQ | ETF | 72% | 72% |
| 3 | GE | US Industrials | 74% | 67% |
| 4 | 0883.HK | HK Energy | 67% | 61% |
| 5 | USDJPY=X | FX | 70% | 63% |
| 6 | AAPL | US Tech | 68% | 65% |
| 7 | META | US Tech | 67% | 56% |
| 8 | HD | US Consumer | 69% | 58% |
| 9 | PLTR | US Tech | 66% | 62% |
| 10 | TSM | Semiconductors | 64% | 77% |

**File:** `S005/S005-Others.md`

---

# S006: MONDAY EFFECT

## Strategy Overview
**Total Tickers:** 22  
**Standalone Sectors:** 0  
**Others Bucket:** 22 tickers

(No sector has 4+ tickers)

**Top 10 Others:**

| Rank | Ticker | Sector | Test | Val |
|------|--------|--------|------|-----|
| 1 | PL=F | Commodities | 79% | 59% |
| 2 | MSFT | US Tech | 78% | 58% |
| 3 | AAPL | US Tech | 73% | 75% |
| 4 | 000333.SZ | CN Property | 72% | 67% |
| 5 | CRWD | US Tech | 71% | 56% |
| 6 | SPY | ETF | 70% | 75% |
| 7 | QQQ | ETF | 69% | 70% |
| 8 | JPM | US Banks | 80% | 64% |
| 9 | GE | US Industrials | 62% | 80% |
| 10 | CRM | US Tech | 67% | 71% |

**File:** `S006/S006-Others.md`

---

# CROSS-STRATEGY CHAMPIONS

| Ticker | Strategies | Priority |
|--------|------------|----------|
| **0005.HK** | S001, S002 | 🔥 HIGH |
| **0939.HK** | S001, S002 | 🔥 HIGH |
| **NVDA** | S002, S003, S005, S006 | 🔥 HIGH |
| **GE** | S002, S005, S006 | 🔥 HIGH |
| **AAPL** | S001, S003, S005, S006 | 🔥 HIGH |
| **PLTR** | S001, S003, S004, S005 | 🔥 HIGH |
| **0883.HK** | S003, S004, S005, S006 | 🔥 HIGH |
| **JPM** | S005, S006 | MEDIUM |
| **GOOGL** | S002, S005, S006 | MEDIUM |
| **SPY** | S002, S005, S006 | MEDIUM |
| **QQQ** | S002, S005, S006 | MEDIUM |

---

# FINAL STRUCTURE (4+ Threshold)

**6 Standalone Sectors:**
1. S001-HK-Banks (7 tickers)
2. S001-US-Tech (4 tickers)
3. S001-Crypto (4 tickers)
4. S002-HK-Banks (4 tickers)
5. S004-HK-Tech (4 tickers)
6. S005-US-Banks (4 tickers)

**6 Others Buckets:**
- S001-Others (41 tickers)
- S002-Others (48 tickers)
- S003-Others (22 tickers)
- S004-Others (18 tickers)
- S005-Others (22 tickers)
- S006-Others (22 tickers)

**Total: 6 sector files + 6 Others files = 12 files**