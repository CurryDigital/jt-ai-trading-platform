# Hypothesis: Opening Gap Fade (SPY)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Mean reversion  
**Horizon:** Intraday (first 30-60 minutes)  
**Target Win Rate:** 70-75%

---

## Core Idea

SPY (S&P 500 ETF) opening gaps fill ~70-80% of the time by end of day. When SPY gaps up/down >0.5% at open, trade the fade toward prior close.

**Academic Research:**
- "Gap Fill Trading Strategies" — Opening gaps fill 70%+ of the time
- Overnight risk premium gets priced in, then reverses intraday

---

## Signal

**Entry:**
- Gap Up >0.5% → Short at open
- Gap Down >0.5% → Long at open

**Exit:**
- Price returns to prior day close (gap fill)
- Time stop: 60 minutes
- Stop loss: 0.3% against position

---

## Universe

SPY (primary), QQQ, IWM for diversification

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 70-75% |
| Avg Win | 0.4% |
| Avg Loss | 0.3% |
| Expectancy | +0.19% per trade |
| Sharpe | 1.5-2.0 |

---

## Data

- OHLC daily from yfinance
- Real-time gap calculation at 09:30 ET

---

## Risk

- Black swan events (gap extends)
- Trend days where gap doesn't fill
- Requires quick execution at open

---

*Next: Backtest on 5 years of SPY data.*
