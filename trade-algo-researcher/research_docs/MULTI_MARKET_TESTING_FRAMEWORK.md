# Multi-Market Testing Architecture

**Version:** 2.0  
**Date:** 2026-02-18  
**Purpose:** Systematic multi-market validation for stock hypotheses

---

## Core Principle

**No hypothesis is rejected until tested across multiple markets.**

What fails in US may work in:
- Less efficient markets (HK, CN)
- Different time zones (ASIA, EU)
- Specific sectors by region
- Emerging vs developed markets

---

## Market Classification

### Tier 1: Developed Markets (Most Efficient)
| Market | Code | Characteristics | Expected Alpha |
|--------|------|-----------------|----------------|
| United States | US | Algo-heavy, HFT dominant | Lowest |
| Japan | JP | Sophisticated, liquid | Low |
| UK | UK | Mature, institutional | Low |
| Germany | DE | Efficient, regulated | Low |

### Tier 2: Semi-Efficient Markets
| Market | Code | Characteristics | Expected Alpha |
|--------|------|-----------------|----------------|
| Hong Kong | HK | China exposure, retail flow | Medium |
| Singapore | SG | Financial hub, liquid | Medium |
| Australia | AU | Resource-heavy, institutional | Medium |
| Canada | CA | Resource-heavy, US-linked | Medium |

### Tier 3: Emerging Markets (Least Efficient)
| Market | Code | Characteristics | Expected Alpha |
|--------|------|-----------------|----------------|
| China A-Shares | CN | Retail dominant, restricted | High |
| India | IN | Growth, retail participation | High |
| Brazil | BR | Commodity-linked, volatile | High |
| Korea | KR | Chaebols, retail heavy | Medium-High |

---

## Testing Protocol

### Parallel Market Testing Rule

**Test on 4 markets SIMULTANEOUSLY:**
1. United States (US)
2. Hong Kong (HK)
3. China (CN) - ADRs or A-shares ETFs
4. Singapore (SG)

**Classification Rule:**
- If strategy **WORKS on ANY 1+ markets** → **USABLE** (tag as MARKET-SPECIFIC)
- If strategy **FAILS on ALL 4 markets** → **REJECTED**

**No sequential rejection.** Don't reject after US failure - test all 4 markets first.

### Phase 1: Parallel Testing (Mandatory)

**Duration:** 2019-2024 (5 years)  
**Minimum Sample:** 50 stocks per market

| Market | Universe | Minimum Trades | Pass Criteria |
|--------|----------|----------------|---------------|
| US | SPY, QQQ, IWM, 50 large-caps | 50 | WR ≥55%, Sharpe ≥0.6 |
| HK | HSI constituents, 50 liquid | 30 | WR ≥52%, Sharpe ≥0.4 |
| CN | BABA, JD, NIO, MCHI, KWEB | 30 | WR ≥52%, Sharpe ≥0.4 |
| SG | STI constituents, EWS | 30 | WR ≥52%, Sharpe ≥0.4 |

### Phase 2: Classification

After testing ALL 4 markets:

**IF works on ≥1 markets:**
- Classify as **MARKET-SPECIFIC**
- Tag with working markets: [US], [HK], [CN], [SG]
- Deploy only on validated market(s)

**IF fails on ALL 4 markets:**
- Classify as **REJECTED**
- Permanently archive
- Do not retest

### Phase 3: Sector Expansion (Optional)

For validated strategies, test sector applicability within working markets.

| Sector | US Proxy | HK Proxy | CN Proxy |
|--------|----------|----------|----------|
| Tech | XLK | 0700.HK, 9988.HK | BABA, JD |
| Finance | XLF | 0005.HK, 1299.HK | FXI (ETF) |
| Energy | XLE | 0883.HK | SNP (if available) |
| Property | XLRE | 1113.HK | VNQ (US) |

---

## Hypothesis Classification

### After Parallel Testing, Classify As:

**USABLE (Works on ≥1 market)** 🟢
- Tested on 4 markets
- Passed criteria on 1+ markets
- Tag with applicable markets: [US], [HK], [CN], [SG]
- Deploy only on passing market(s)
- Examples: 3-Day Reversal [HK], Gap Fade [HK], RSI [US,HK]

**REJECTED (Fails on ALL 4 markets)** 🔴
- Tested on 4 markets
- Failed criteria on ALL markets
- Permanently archive
- Do not retest
- Example: Peer Firm Lag [REJECTED]

### Classification Matrix

| Classification | Criteria | Deploy On |
|----------------|----------|-----------|
| **UNIVERSAL** | Works on ≥3 of 4 markets | All tested markets |
| **MARKET-SPECIFIC** | Works on 1-2 of 4 markets | Passing markets only |
| **SECTOR-SPECIFIC** | Works only in specific sectors | Validated sectors only |
| **REJECTED** | Fails on ALL 4 markets | None |

---

## Implementation

### File Structure

```
hypotheses/
├── active/
│   ├── rsi_mean_reversion.md [UNIVERSAL]
│   ├── gap_fade.md [MARKET-SPECIFIC: HK, CN]
│   └── peer_firm_lag.md [REJECTED]
├── validated/
│   └── (promoted strategies)
└── rejected/
    └── (failed hypotheses with notes)

research_docs/
├── MULTI_MARKET_TESTING_FRAMEWORK.md (this file)
├── TESTED_HYPOTHESES_REGISTRY.md
├── US_TEST_RESULTS.md
├── ASIA_TEST_RESULTS.md
└── MARKET_SPECIFIC_DEPLOYMENT.md

strategies/
├── multi_market_backtest.py (universal runner)
├── us_backtest.py
├── hk_backtest.py
└── cn_backtest.py
```

### Testing Automation

**New Script: `multi_market_test.py`**
```python
def test_hypothesis(hypothesis_name, markets=['US', 'HK', 'CN']):
    """
    Test hypothesis across multiple markets
    Returns: classification (UNIVERSAL/MARKET-SPECIFIC/REJECTED)
    """
    results = {}
    
    for market in markets:
        if market == 'US':
            result = run_us_backtest(hypothesis_name)
        elif market == 'HK':
            result = run_hk_backtest(hypothesis_name)
        elif market == 'CN':
            result = run_cn_backtest(hypothesis_name)
        
        results[market] = result
    
    return classify_hypothesis(results)

def classify_hypothesis(results):
    """Classify based on cross-market results."""
    passing_markets = [m for m, r in results.items() 
                       if r['win_rate'] > 0.55 and r['sharpe'] > 0.6]
    
    if len(passing_markets) >= 3:
        return 'UNIVERSAL', passing_markets
    elif len(passing_markets) >= 1:
        return 'MARKET-SPECIFIC', passing_markets
    else:
        return 'REJECTED', []
```

### Hypothesis Template Update

Every hypothesis file should include:

```markdown
## Market Applicability

**Primary Market:** [US/HK/CN/EU]
**Tested Markets:** US ✅, HK ✅, CN ⏳

### Results by Market

| Market | Win Rate | Sharpe | Trades | Status |
|--------|----------|--------|--------|--------|
| US | 47.8% | -1.04 | 104 | ❌ Failed |
| HK | 53.6% | 0.85 | 531 | ✅ Works |
| CN | — | — | — | Not tested |

**Classification:** MARKET-SPECIFIC (HK)
**Deployment:** Validated tickers: 0005.HK, 1299.HK, 9988.HK
```

---

## Deployment Rules

### Universal Strategies
- Deploy on ALL markets simultaneously
- Position sizing: Equal across markets
- Rebalancing: Synced or staggered

### Market-Specific Strategies
- Deploy ONLY on validated markets
- Position sizing: Full allocation in target market
- Do NOT deploy on failed markets (even if "similar")

### Example: 3-Day Reversal

**Status:** MARKET-SPECIFIC (HK)

**Deploy On:**
- ✅ 0005.HK (HSBC) - 76% win rate
- ✅ 1299.HK - 70% win rate
- ✅ 9988.HK (BABA HK) - 59% win rate

**Do NOT Deploy On:**
- ❌ SPY (47% win rate)
- ❌ QQQ (33% win rate)
- ❌ AAPL (44% win rate)

---

## Data Sources by Market

| Market | Free Data | Paid Data | Cost |
|--------|-----------|-----------|------|
| US | yfinance | Polygon, Bloomberg | $50-500/mo |
| HK | yfinance | Bloomberg, Refinitiv | $200-500/mo |
| CN | yfinance (ADRs) | Wind, Bloomberg | $300-600/mo |
| SG | yfinance | Bloomberg | $200-400/mo |

---

## Testing Checklist

For every stock hypothesis:

### Parallel Testing (Mandatory)
- [ ] Test on **US** (50+ stocks)
- [ ] Test on **HK** (50+ stocks)
- [ ] Test on **CN** (30+ stocks)
- [ ] Test on **SG** (30+ stocks)
- [ ] **Evaluate:** Did it work on ANY market?
- [ ] If YES → Classify as USABLE (tag markets)
- [ ] If NO (all 4 failed) → Classify as REJECTED

### Documentation
- [ ] Document results in hypothesis file
- [ ] Update registry with classification
- [ ] Tag deployment restrictions
- [ ] List specific validated tickers per market

**Exception:** News-based, macro, or commodity hypotheses (market-agnostic)

**Sequential testing is WRONG. Always test 4 markets in parallel.**

---

## Registry Update

Track in `TESTED_HYPOTHESES_REGISTRY.md`:

| Hypothesis | US | HK | CN | Classification | Deploy On |
|------------|----|----|----|----------------|-----------|
| RSI Mean Reversion | ✅ | ✅ | ⏳ | UNIVERSAL | All |
| Gap Fade | ❌ | ✅ | ⏳ | MARKET-SPECIFIC | HK only |
| Peer Firm Lag | ❌ | ❌ | ❌ | REJECTED | None |
| 3-Day Reversal | ❌ | ✅ | ⏳ | MARKET-SPECIFIC | HK only |

---

*Test 4 markets in parallel. If ANY works, strategy is usable. Only reject if ALL fail.*
