# Hypothesis: Trump Policy Announcement Momentum

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities / FX / Commodities  
**Direction:** Long/Short (policy-dependent)  
**Horizon:** 1-5 days  
**Target Win Rate:** 60-70%

---

## Core Idea

Trump policy announcements (tariffs, trade war, deregulation) create predictable 1-3 day momentum in affected sectors. Market initially underreacts, then drifts in announcement direction.

**The Edge:**
- Trump's communication style = clear directional signal
- Sector rotation predictable (tariffs → industrials down, defense up)
- 24-48 hour drift before full absorption

---

## Signal Construction

**Detection:**
```
Source: Truth Social, X posts, press conferences
Keywords: "tariff", "trade war", "sanctions", "deregulation"
Sentiment: VADER or FinBERT classification
```

**Long Trades:**
```
IF "deregulation" + financials/banks mentioned
OR "defense spending" + defense stocks
OR "domestic manufacturing" + US industrials
THEN long affected sector, 2-3 day hold
```

**Short Trades:**
```
IF "tariffs on [country]" + import-exposed sectors
OR "trade war" + multinationals
OR "sanctions" + affected companies
THEN short affected sector, 2-3 day hold
```

**Universe Mapping:**
| Policy Type | Long | Short |
|-------------|------|-------|
| Tariffs | Domestic steel, Defense | Multinationals, China-exposed |
| Deregulation | Banks, Energy, Crypto | — |
| Tax cuts | Small-caps (IWM) | — |
| Trade war fears | Gold, USD | Emerging markets |

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return | 2-4% per trade |
| Sharpe | 1.2-1.6 |
| Best Window | T+0 to T+2 |

**Academic Support:**
- Savor & Wilson (2013): Stock market reaction to monetary policy
- Lucca & Moench (2015): Pre-FOMC announcement drift
- Applications to political announcements similar pattern

---

## Data Requirements

- **Truth Social API** or scraping
- **X API** (Twitter) for real-time monitoring
- **News feeds:** Bloomberg, Reuters headline alerts
- **Keyword NLP:** Policy type classification
- **Latency:** <5 minutes from post to signal

---

## Risk Factors

1. **False signals** — Off-hand comments not policy
2. **Reversal** — "Trump puts" — market learns to fade
3. **Implementation lag** — Announcement ≠ immediate action
4. **Legal challenges** — Policy blocked by courts

---

## Execution

**Entry:** Within 30 minutes of announcement
**Sizing:** 2-3% per signal (high conviction)
**Stop:** 2% adverse move
**Exit:** 48 hours or momentum exhaustion

---

*Political alpha from policy volatility.*
