# Hypothesis: Elon Musk Twitter Sentiment Alpha

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities (TSLA, X, SpaceX-related)  
**Direction:** Long/Short  
**Horizon:** 1-3 days  
**Target Win Rate:** 55-65%

---

## Core Idea

Elon Musk's tweets create measurable price impact on TSLA and related stocks. Sentiment analysis of tweets predicts 1-3 day drift. SEC settlement (2018) changed pattern but alpha remains.

**The Edge:**
- 2018-2022: Direct TSLA mentions = 5-10% moves
- Post-SEC: Coded language, crypto/dogecoin tweets affect TSLA indirectly
- Volume spike on tweets precedes retail FOMO

---

## Signal Construction

**Tweet Classification:**
```python
# Tweet types with historical impact
direct_tsla = ["Tesla", "Model 3", "FSD", "production", "deliveries"]
production = ["manufacturing", "factory", "ramp", "output"]
financial = ["funding secured", "private", "stock price"]
crypto = ["bitcoin", "dogecoin", "crypto"]
meme = ["gamestonk", "diamond hands", "hodl"]
```

**Signal Scoring:**
```
IF tweet mentions TSLA directly AND sentiment positive
  → Long TSLA, 1-2 day hold

IF tweet mentions production/delivery issues AND sentiment negative  
  → Short TSLA or long puts, 1-2 day hold

IF tweet mentions crypto (BTC/DOGE)
  → Long TSLA (correlation trade), 1 day hold

IF tweet contains "funding secured" type language
  → Ignore (SEC monitoring, pattern changed)
```

---

## Expected Performance

| Period | Win Rate | Avg Move | Sharpe |
|--------|----------|----------|--------|
| 2018-2020 | 65% | 5-10% | 1.8 |
| 2021-2023 | 55% | 2-4% | 1.0 |
| 2024+ | 50% | 1-2% | 0.6 |

**Trend:** Alpha decaying as market adapts.

---

## Data Requirements

- **X API v2** (Twitter) - real-time tweet stream
- **TSLA options flow** - institutional positioning
- **FinBERT sentiment** - financial NLP model
- **Latency:** <2 minutes tweet to signal

---

## Related Tickers

| Tweet Topic | Primary | Secondary | Correlation |
|-------------|---------|-----------|-------------|
| TSLA production | TSLA | — | 1.0 |
| SpaceX success | — | ASTS, RKLB | 0.4 |
| DOGE/BTC | DOGE | MSTR, COIN | 0.6 |
| AI/Robotaxi | TSLA | NVDA | 0.5 |

---

## Risk Factors

1. **SEC enforcement** — Pattern changed after 2018 settlement
2. **Alpha decay** — Market now front-runs obvious signals
3. **False positives** — Joke tweets, memes misclassified
4. **Correlation breakdown** — TSLA increasingly macro-driven

---

## Academic Support

- Kogan et al. (2019): Twitter sentiment and stock returns
- Jame et al. (2021): Retail investor attention and returns
- Ozkan & Ozkan (2021): Social media and volatility

---

## Verdict

**Declining edge.** Still works for:
- Production/delivery tweets (fundamental)
- Major product announcements (AI day, robotaxi)
- Less effective for meme/crypto tweets (priced in)

---

*The original social media alpha — now crowded.*
