# Hypothesis: Northbound Stock Connect Flow Momentum

**Status:** idea  
**Created:** 2026-02-18  
**Markets:** HK, CN (Stock Connect)  
**Direction:** Long  
**Horizon:** 1-2 weeks  
**Target Win Rate:** 58-62%

---

## Core Idea

Mainland China investors ("northbound" flow via Stock Connect) exhibit momentum behavior. Heavy buying via Stock Connect predicts short-term HK stock outperformance.

**The Edge:**
- Northbound flows = retail + institutional China money
- Often trend-following (momentum chasing)
- 1-2 week persistence before mean reversion
- HK stocks with heavy northbound flows outperform peers

**Stock Connect Mechanics:**
- Shanghai/Shenzhen investors buy HK stocks (southbound)
- HK/global investors buy A-shares (northbound)
- Daily quotas (but rarely hit)

---

## Signal Construction

**Data:**
- Daily northbound flow by stock (HKEX publishes)
- Top 10 traded stocks via Stock Connect
- Net buying/selling volume

**Signal:**
```python
# Calculate northbound flow score
northbound_score = (northbound_net_buy_volume_5d / avg_daily_volume) * 100

IF northbound_score > 50 (significant inflow):
    AND stock in top 10 northbound buy list:
    AND price_momentum_5d > 0:
    
    Long stock
    Hold 5-10 days
    Exit on flow reversal or time stop
```

**Universe:**
- 0700.HK (Tencent) - always top northbound favorite
- 3690.HK (Meituan)
- 9988.HK (Alibaba HK)
- 2318.HK (Ping An)
- 1299.HK (AIA)
- 0005.HK (HSBC)
- 0388.HK (HKEX itself)

**Enhanced Filter:**
```python
# Higher conviction when:
- Northbound flow accelerating (5d > 20d average)
- Broader market sentiment positive (HSI > 20-day MA)
- No major lock-up expiry/insider selling
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Avg Return | 2-4% per trade |
| Sharpe | 0.9-1.2 |
| Hold Period | 5-10 days |

**Risks:**
- Flows can reverse quickly
- Crowded trade (many watching same data)
- Quota limits (rare but possible)

---

## Data Requirements

- **HKEX Stock Connect data:** Daily northbound flows
- **Top 10 traded:** Most active via Stock Connect
- **Historical flows:** For backtesting momentum persistence
- **Real-time access:** Best executed with T+0 data

**Sources:**
- HKEX website (Stock Connect daily data)
- Bloomberg/Reuters (flow analytics)
- Wind (China-focused data)
- Eastmoney (retail flow tracking)

---

## Academic Support

- Fong et al. (2022): Stock Connect flow persistence
- Chen & Wang (2021): Investor behavior in Stock Connect
- HKEx research papers on Connect program

---

## Implementation

**Daily Routine:**
1. Check HKEX after close for northbound flow data
2. Identify top 10 net buy stocks
3. Calculate 5-day flow vs average
4. Enter next day open if signal triggered
5. Monitor daily for flow reversal

**Exit Triggers:**
- Northbound turns net seller (2 consecutive days)
- Price hits 5% profit target
- 10-day time stop
- HSI breaks below 20-day MA (risk-off)

---

## Related Strategies

**Southbound Version:**
- HK/global investors buying A-shares
- Similar momentum effect
- Universe: MCHI, KWEB holdings

**Pairs Trade:**
- Long: Heavy northbound inflow stocks
- Short: Heavy northbound outflow stocks
- Market neutral

---

*Follow the smart money from Mainland China.*
