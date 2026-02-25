# Hypothesis: AH Premium Arbitrage (A-shares vs H-shares)

**Status:** idea  
**Created:** 2026-02-18  
**Markets:** HK, CN (dual-listed stocks)  
**Direction:** Long/Short (pair trade)  
**Horizon:** 1-4 weeks  
**Target Win Rate:** 60-70%

---

## Core Idea

Chinese companies dual-listed in Hong Kong (H-shares) and Shanghai/Shenzhen (A-shares) often trade at different prices. The AH premium/discount mean-reverts due to arbitrage forces and capital flow relaxation.

**The Edge:**
- A-shares typically trade at 20-40% premium to H-shares
- Premium widens during China bull markets, narrows during bear markets
- Capital connects (Stock Connect) allow partial arbitrage
- Retail-driven A-shares more emotional, H-shares more institutional

---

## Signal Construction

**Universe:** Dual-listed Chinese stocks
- 0700.HK / 600519.SH (not dual-listed, need actual dual-listed pairs)
- 0005.HK / not A-share
- Need: Companies listed on BOTH HKEX and SSE/SZSE

**Actual Dual-Listed Pairs:**
- 2318.HK / 601318.SH (Ping An)
- 0998.HK / 600028.SH (Sinopec)
- 1398.HK / 601398.SH (ICBC)
- 0939.HK / 601939.SH (CCB)
- 1288.HK / 601288.SH (Agricultural Bank)
- 3988.HK / 601988.SH (Bank of China)
- 6030.HK / 600030.SH (CITIC Securities)

**Calculation:**
```python
AH_premium = (A_share_price - H_share_price_in_CNY) / H_share_price_in_CNY
# H-share price converted to CNY using HKD/CNY rate
```

**Entry (Long H-shorts, Short A-shares proxy):**
```python
IF AH_premium > 30% (historical 90th percentile):
    Long H-shares (e.g., 2318.HK)
    Short A-share ETF proxy (e.g., ASHR puts or avoid if can't short)
    Hold until premium < 20%
```

**Exit:**
- Premium narrows to < 20%
- Or 4-week time stop

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return per Trade | 3-5% |
| Sharpe | 1.0-1.5 |
| Best Environment | China bull/bear extremes |

**Historical Context:**
- AH premium averaged 20-25% over past decade
- Can swing from -10% (H premium) to +40% (A premium)
- Mean reversion typically takes 2-4 weeks

---

## Data Requirements

- **Dual-listed ticker mapping:** HKEX code ↔ SSE/SZSE code
- **Real-time prices:** Both markets
- **FX rates:** HKD/CNY for conversion
- **Historical AH premium:** For percentile calculation
- **Stock Connect flows:** Northbound/southbound daily data

**Sources:**
- HKEX website (dual-listed companies list)
- Bloomberg/Reuters (AH premium data)
- Wind/Choice (China data)

---

## Risk Factors

1. **Currency risk:** CNY/HKD fluctuation
2. **Shorting constraints:** Hard to short A-shares directly
3. **Policy risk:** Stock Connect quota limits, capital controls
4. **Timing:** Premium can widen further before mean reversion

**Mitigation:**
- Use A-share ETFs (ASHR, KWEB) as proxy for short side
- Position size smaller (1-2% per pair)
- Monitor Stock Connect daily quotas

---

## Academic Support

- Fong et al. (2021): AH premium persistence and arbitrage limits
- Chen et al. (2019): Investor sentiment and AH premium
- Wang & Jiang (2018): Stock Connect impact on AH convergence

---

## Implementation

**Long-only version (simpler):**
- Buy H-shares when AH premium > 30%
- Hold until premium < 20%
- No short leg needed

**Full arbitrage:**
- Requires A-share shorting capability (QFII, Stock Connect)
- Or use options/ETFs for A-share exposure

---

*Exploit the China dual-listing discount.*
