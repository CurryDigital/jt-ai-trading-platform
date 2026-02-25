# Hypothesis: Earnings Pre-Announcement Options Flow

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-3 days (pre-earnings)  
**Target Win Rate:** 60-70%

---

## Core Idea

Unusual options activity before earnings announcements predicts surprise direction. Smart money (insiders, institutional) trades ahead of retail. Call/put skew and volume spikes signal informed trading.

**The Edge:**
- Options market leads stock by 1-2 days
- Unusual volume = information advantage
- IV skew reflects directional conviction

---

## Signal Construction

**Unusual Volume Detection:**
```python
# Calculate z-score of options volume
avg_volume = mean(volume[-20:])
std_volume = std(volume[-20:])
volume_zscore = (today_volume - avg_volume) / std_volume

# Signal threshold
IF volume_zscore > 2.5 (2.5 std dev above normal):
    → Unusual activity detected
```

**Directional Skew:**
```python
# Call/Put volume ratio
CP_ratio = call_volume / put_volume

IF CP_ratio > 1.5 AND volume_zscore > 2.5:
    → Bullish signal → Long stock before earnings
    
IF CP_ratio < 0.7 AND volume_zscore > 2.5:
    → Bearish signal → Short stock or buy puts
```

**IV Skew:**
```python
# Compare 25-delta call vs put IV
call_25d_iv = IV(strike=ATM*1.05)
put_25d_iv = IV(strike=ATM*0.95)
skew = call_25d_iv - put_25d_iv

IF skew > 0.02 (calls expensive):
    → Bullish expectations
IF skew < -0.02 (puts expensive):
    → Bearish expectations
```

---

## Expected Performance

| Signal Type | Win Rate | Avg Return | Sharpe |
|-------------|----------|------------|--------|
| Call surge (bullish) | 62% | 3-5% | 1.3 |
| Put surge (bearish) | 58% | 4-6% | 1.2 |
| Combined (vol+skew) | 68% | 4-7% | 1.6 |

**Timing:**
- Best: 1-2 days before announcement
- Avoid: Morning of announcement (IV crush risk)

---

## Data Requirements

- **Options flow data:** Cboe, Polygon, Unusual Whales
- **Real-time:** EOD minimum, intraday preferred
- **Fields:** Volume, OI, IV by strike
- **Latency:** <1 hour for signal generation

**Data Providers:**
- Cboe LiveVol (expensive, institutional)
- Polygon.io (API, affordable)
- Unusual Whales (retail-friendly)
- Tradier (free tier available)

---

## Universe

High options liquidity stocks:
- FAANG: AAPL, AMZN, GOOGL, META, NFLX
- Tech: NVDA, AMD, MSFT, CRM
- Memes: GME, AMC, TSLA

---

## Academic Support

- Roll et al. (2010): Options trading and informed activity
- Johnson & So (2012): Options implied volatility before M&A
- Cremers & Weinbaum (2010): Deviations from put-call parity
- Pan & Poteshman (2006): Information in options volume

---

## Risk Factors

1. **IV crush** — Implied volatility collapses after earnings
2. **False signals** — Hedging activity looks like directional bets
3. **Liquidity** — Wide spreads in OTM options
4. **Market maker games** — Spoofing, layered orders

---

## Execution

**Entry:** 1-2 days before earnings announcement
**Position:** Long stock (don't buy options due to IV crush)
**Stop:** 3% adverse move
**Exit:** Day before announcement or morning of (avoid IV crush)
**Alternative:** Buy deep ITM options (less IV sensitive)

---

*Follow the smart money — they know before the press release.*
