# Hypothesis: Retail Order Flow Imbalance

**Status:** idea  
**Created:** 2026-02-19  
**Source:** Post-2020 retail trading boom research (meme stocks, Robinhood effect)  
**Asset Class:** Equities  
**Direction:** Contrarian (fade retail)  
**Horizon:** 1-5 days  
**Target Win Rate:** 58-62%

---

## Core Idea

Retail investors are noise traders. Extreme retail buying predicts short-term reversal (overreaction). Extreme retail selling predicts bounce (panic bottom). Uses Whalesburg/Netflow data as proxy.

**Academic Support:**
- Barber, Odean (2023): "The Behavior of Individual Investors" - retail underperformance
- Laarits (2022): "Retail Trading and Market Quality"
- Welch (2022): "The Wisdom of the Robinhood Crowd"

---

## Signal Construction

**Retail Flow Proxy:**
- Whalesburg data (smart money vs dumb money)
- Robinhood top 100 holdings changes
- Social media sentiment spikes
- Options small-lot buying (retail indicator)

**Entry (Fade Retail FOMO):**
```python
IF retail_net_buying > 90th_percentile (extreme FOMO):
    AND social_media_mentions spike:
    AND price_up_5d > 15%:
    
    Short stock (1-3 days)
```

**Entry (Fade Retail Panic):**
```python
IF retail_net_selling > 90th_percentile (panic):
    AND price_down_5d > 15%:
    
    Long stock (1-3 days)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Avg Return | 2-4% per trade |
| Sharpe | 1.1-1.4 |
| Best For | Meme stocks, high retail interest names |

---

## Data Requirements

- **Whalesburg:** Smart/dumb money ratio
- **Robinhood API:** Top 100 holdings (limited)
- **Social media:** Reddit, StockTwits mentions
- **Options:** Small-lot put/call ratio

---

## Risk

- Squeeze risk if retail coordinated (GME, AMC)
- Need real-time data (lag = missed opportunity)

---

*Fade the crowd.*
