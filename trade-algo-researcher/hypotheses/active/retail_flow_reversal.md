# Hypothesis: Retail Flow Reversal (Robinhood Effect)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Contrarian to retail  
**Horizon:** 2-5 days  
**Target Win Rate:** 65-70%

---

## Core Idea

Retail traders (Robinhood, Webull) are systematically wrong at extremes. When retail is euphoric (heavy buying), stock drops next 2-5 days. When retail panics (heavy selling), stock bounces.

**The Edge:**
- Retail buys after good news (already priced in)
- Retail sells on bad news (overreaction)
- Institutional flow opposite to retail
- Zero-commission trading increased retail participation → increased predictability

---

## Signal Sources

**Proxy for Retail Flow:**
- OptionMetrics: Small lot options (<10 contracts)
- Unusual call buying (retail loves calls)
- High volume + low institutional ownership
- Mention spikes on Reddit/Twitter
- Robinhood top 100 stocks
- High retail ownership % (Vanda Research)

---

## Signal Construction

**Short Setup (Retail Euphoria):**
```
IF retail_call_volume / put_volume > 3.0 AND
   stock_up_5d > 15% AND
   social_mentions > 2_stddev AND
   institutional_flow < 0 (selling)
THEN short, hold 3 days
```

**Long Setup (Retail Panic):**
```
IF retail_put_volume spikes AND
   stock_down_5d > 20% AND
   social_sentiment < -0.5 AND
   institutional_flow > 0 (buying)
THEN long, hold 3 days
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 65-70% |
| Avg Return | 3-5% per trade |
| Sharpe | 1.5-2.0 |
| Max DD | 15% |

---

## Data Requirements

- OptionMetrics (small lot options)
- Social media sentiment (Twitter, Reddit)
- Vanda Research retail ownership data
- Institutional flow (13F, Bloomberg)

---

## Why It Works

1. **Retail is systematically late** — buys after rally, sells after crash
2. **Emotional trading** — FOMO on way up, panic on way down
3. **Institutional counter-party** — smart money takes other side
4. **Market microstructure** — retail market orders hit bid/ask, create slippage

---

## Academic Support

- Barber, Odean: Retail traders underperform (1.5% annually)
- Linnainmaa: Retail order flow predicts negative returns
- "Dumb money" effect well-documented

---

## Risk

- Meme stocks can defy logic (GME, AMC)
- Short squeezes when retail coordinates
- Requires real-time sentiment data

---

*Trade against the crowd. Be the casino, not the gambler.*
