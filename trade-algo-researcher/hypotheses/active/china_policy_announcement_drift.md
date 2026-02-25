# Hypothesis: China Policy Announcement Drift

**Status:** idea  
**Created:** 2026-02-18  
**Markets:** CN (ADRs), HK (China exposure)  
**Direction:** Long/Short (policy-dependent)  
**Horizon:** 1-5 days  
**Target Win Rate:** 60-70%

---

## Core Idea

Chinese policy announcements (regulatory crackdowns, stimulus, sector support) create predictable 1-5 day drifts. Market underreacts initially, then drifts as implications sink in.

**The Edge:**
- China policy moves are telegraphed (Five-Year Plans, PBoC signals)
- Market initially prices in headline, misses second-order effects
- 24-48 hour window before full absorption
- HK/ADR markets trade during US hours = faster reaction

**Examples:**
- 2021 EdTech crackdown: TAL, GOTU dropped 70% over weeks
- 2023 Gaming license freeze: NTES, TCEHY volatility
- 2024 Stimulus announcements: BABA, JD rallies

---

## Signal Construction

**News Sources:**
- Xinhua News Agency (official policy)
- South China Morning Post (HK perspective)
- Caixin (business-focused)
- State Council announcements
- PBoC monetary policy statements

**Policy Categories:**

**BEARISH (Short):**
- Regulatory crackdown (antitrust, data privacy)
- Sector restrictions (gaming hours, EdTech)
- Delisting fears (PCAOB audit disputes)
- Capital controls tightening

**BULLISH (Long):**
- Stimulus announcements (infrastructure spending)
- Rate cuts (LPR, RRR)
- Sector support (EV subsidies, chip manufacturing)
- Index inclusion (MSCI, FTSE adds)

**Entry:**
```python
IF bearish_policy_announced AND affected_ticker_gaps_down < 10%:
    # Short - drift continues
    Short ticker
    Hold 3-5 days
    
IF bullish_policy_announced AND affected_ticker_gaps_up < 5%:
    # Long - drift continues  
    Long ticker
    Hold 2-3 days
```

**Universe:**
- US-listed China ADRs: BABA, JD, PDD, NIO, LI, XPEV, TCEHY, BIDU, BEKE
- HK-listed China exposure: 0700.HK, 3690.HK, 9988.HK, 1810.HK

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return | 3-8% per trade |
| Sharpe | 1.2-1.8 |
| Best Window | T+0 to T+2 (24-48 hours) |

**Key Insight:** Directional accuracy less important than speed. React within 4 hours of announcement.

---

## Data Requirements

- **News feed:** Real-time China policy alerts
- **NLP classification:** Bullish/bearish policy sentiment
- **Ticker mapping:** Policy → affected stocks
- **HKEX trading hours:** 09:30-16:00 HKT (overlap with China news)

**Sources:**
- Bloomberg Government (policy alerts)
- Caixin Global (English China news)
- Xinhua English (official source)
- Twitter/X China watchers

---

## Risk Factors

1. **Policy reversal:** China can flip-flop (gaming licenses example)
2. **Market closure:** A-shares closed when news breaks = HK/ADR only
3. **False signals:** Rumors vs confirmed policy
4. **Liquidity:** Small-cap ADRs wide spreads

**Mitigation:**
- Wait for official confirmation (not rumors)
- Position size smaller (1-2% per trade)
- Stop loss 5% (tight - policy moves fast)

---

## Academic Support

- Chen et al. (2022): Regulatory uncertainty and Chinese ADR returns
- Fung et al. (2021): Information transmission between China and US markets
- Jiang et al. (2020): Policy risk in Chinese equities

---

## Implementation

**Monitoring:**
- Set alerts for: "China", "regulator", "policy", "crackdown", "stimulus"
- Check Xinhua at 09:00 HKT (pre-market)
- Monitor PBoC announcements (MLF, LPR rates)

**Trade Execution:**
- News breaks → Analyze within 1 hour
- Enter within 4 hours (before US close)
- Hold 1-5 days depending on policy type
- Exit on reversal signal or time stop

---

*Trade China's policy waves.*
