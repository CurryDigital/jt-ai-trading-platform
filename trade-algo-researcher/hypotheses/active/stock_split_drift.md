# Hypothesis: Stock Split Announcement Drift

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 1-3 months  
**Target Win Rate:** 70-75%

---

## Core Idea

Stock split announcements signal confidence (management expects price to rise). Post-announcement drift persists 1-3 months as retail buying increases.

**Academic Research:**
- "Return drift following stock split announcements"
- Ikenberry et al. (1996): 8% abnormal returns post-split
- 70-75% of split stocks outperform

---

## Signal

**Entry:**
- Stock announces split (2:1, 3:1, etc.)
- T+1 after announcement
- Price >$50 (avoids penny stocks)

**Exit:**
- 60 days post-announcement
- Or split execution date

---

## Universe

All stocks announcing splits (need news feed)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 70-75% |
| Avg Return | 5-8% over 2 months |
| Sharpe | 1.2-1.8 |

---

## Data

- Stock split announcements (Benzinga, Bloomberg)
- Price data from yfinance

---

## Risk

- Reverse splits (bearish signal)
- Market correction masks split effect
- Selection bias

---

*Next: Build split announcement database, backtest 2019-2024.*
