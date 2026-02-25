# China AI Chip and Infrastructure Theme Strategy

**Hypothesis ID:** CN_AI_CHIP_INFRA_001  
**Date:** 2026-02-20  
**Region:** China (CN, HK-listed)  
**Asset Class:** Equities  
**Expected Sharpe:** 1.3-1.8  
**Expected Win Rate:** 60-65%  
**Time Horizon:** Medium-term (1-3 months)

---

## Core Thesis

**China is investing heavily in domestic AI chip and infrastructure capabilities due to US export restrictions on NVIDIA and advanced semiconductors.**

### Macro Drivers
1. **US Chip Ban (Oct 2022, Oct 2023):** NVIDIA A100/H100 banned; China forced to develop domestic alternatives
2. **State Investment:** "Big Fund" (China Integrated Circuit Industry Investment Fund) - $50B+ committed
3. **SMIC Progress:** 7nm breakthrough; N+2 process viable for AI accelerators
4. **Local Demand:** Baidu, Alibaba, Tencent developing domestic AI models (Ernie, Tongyi Qianwen, Hunyuan)
5. **Infrastructure Buildout:** National data center initiative; "East Data West Computing" project

### Key Insight
State-backed investment cycles create predictable patterns:
- **Announcement Phase:** Policy/news flow drives initial rally
- **Capex Phase:** Earnings visibility improves; institutional accumulation
- **Execution Phase:** Results validation; winners/losers separate
- **Maturity:** Normalization; mean reversion

---

## Universe

### Tier 1: AI Chip Designers (Direct Play)
| Ticker | Exchange | Role | Notes |
|--------|----------|------|-------|
| 688981.SS | Shanghai | SMIC | Foundry; 7nm capability; government-backed |
| 688256.SS | Shanghai | Hua Hong | Mature node foundry; auto/industrial |
| 688012.SS | Shanghai | NAURA | Equipment; etching/CVD tools; localization |
| 688072.SS | Shanghai | Zhaoyi Innovation | NOR Flash; AI edge applications |
| 688396.SS | Shanghai | HJ Micro | Analog/Digital IC; industrial AI |

### Tier 2: Infrastructure/Computing (Enablers)
| Ticker | Exchange | Role | Notes |
|--------|----------|------|-------|
| 000938.SZ | Shenzhen | Inspur | Servers; AI computing platforms |
| 603019.SS | Shanghai | Sugon | HPC; data center servers |
| 002236.SZ | Shenzhen | Hikvision | AI vision; edge computing |
| 300033.SZ | Shenzhen | Joinquant | Data center REITs; computing parks |
| 600570.SS | Shanghai | Hundsun | Fintech; AI trading infrastructure |

### Tier 3: HK-Listed ADR Proxies
| Ticker | Exchange | Role | Notes |
|--------|----------|------|-------|
| 9988.HK | HKEX | Alibaba | Tongyi Qianwen AI; cloud capex |
| 0700.HK | HKEX | Tencent | Hunyuan AI; gaming/enterprise |
| 3690.HK | HKEX | Meituan | Local AI; delivery optimization |
| 1024.HK | HKEX | Kuaishou | AI content; short video algorithms |
| 9866.HK | HKEX | NIO | Autonomous driving; AI chips |

### Tier 4: Supply Chain/Components
| Ticker | Exchange | Role | Notes |
|--------|----------|------|-------|
| 002049.SZ | Shenzhen | Unigroup Guoxin | Memory controllers; secure chips |
| 600584.SS | Shanghai | JCET | Packaging; advanced packaging for AI |
| 603933.SS | Shanghai | Chance Star | Materials; silicon wafers |

---

## Signal Logic

### Primary Signal: Policy-Capex-Momentum (PCM)

```python
# Phase 1: Policy Catalyst (Entry)
IF policy_news_score > 0.7:  # NLP on Xinhua/State Council announcements
    IF ticker IN china_ai_universe:
        momentum_20d = (close - close[20]) / close[20]
        IF momentum_20d > 0.10 AND momentum_20d < 0.50:  # 10-50% rally (not overheated)
            SIGNAL = WATCHLIST

# Phase 2: Capex Confirmation (Entry)
IF quarterly_capex YoY > 30% OR capex_guidance_raised:
    IF volume_20d > volume_20d_avg * 1.5:  # Institutional accumulation
        IF RS_vs_CSI300 > 1.05:  # Outperforming market
            SIGNAL = LONG
            position_size = base * (capex_growth / 50)  # Size by conviction

# Phase 3: Earnings Validation (Hold/Add)
IF earnings_surprise > 0 AND revenue_growth > 20%:
    IF gross_margin_stable OR improving:
        HOLD / ADD
    ELSE:
        REDUCE  # Execution risk

# Phase 4: Exit Conditions
IF momentum_20d < -0.15:  # 15% drawdown from high
    EXIT = STOP_LOSS
    
IF policy_sentiment < -0.3:  # Negative policy shift
    EXIT = POLICY_RISK
    
IF holding_days > 90 AND momentum_60d < 0:  # Thesis played out/no follow-through
    EXIT = TIME_STOP
```

### Secondary Signal: Relative Value Within Theme

```python
# Pair trade: Strong vs Weak within theme
FOR each_tier IN [tier1_chips, tier2_infra, tier3_hk]:
    rank_by_momentum = tier_universe.sort_by(returns_60d, descending=True)
    
    LONG = top_quintile(rank_by_momentum)
    SHORT = bottom_quintile(rank_by_momentum)  # If shorting allowed
    
    # Or long-only: rotate to top performers
    IF current_position NOT IN top_quintile:
        REBALANCE_to_top_quintile()
```

---

## Entry/Exit Rules

### Entry Conditions
1. **Policy Catalyst:** Major policy announcement (fund launch, subsidy, tax break)
2. **Volume Confirmation:** 20-day volume > 1.5x average (institutional flow)
3. **Momentum Filter:** 20-day return 10-50% (trending but not parabolic)
4. **Relative Strength:** Outperforming CSI 300 by >5%
5. **Capex Signal:** YoY capex growth >30% OR guidance raised

### Exit Conditions
1. **Stop Loss:** -15% from entry
2. **Time Stop:** 90 days without follow-through catalyst
3. **Policy Reversal:** Negative policy/regulatory news
4. **Earnings Miss:** Revenue/capex miss guidance
5. **Rotation Signal:** Momentum shifts to other theme

---

## Position Sizing

```python
max_theme_exposure = 0.20  # 20% of portfolio
max_tier1_exposure = 0.10  # 10% in direct chip plays (higher risk)
max_tier2_exposure = 0.07  # 7% in infrastructure
max_tier3_exposure = 0.03  # 3% in HK-listed proxies

per_position_max = 0.03  # 3% single name
num_positions_target = 8-12  # Diversified within theme
```

---

## Risk Management

### Specific Risks
| Risk | Mitigation |
|------|------------|
| **US Escalation** | Stop loss on new export ban news; reduce Tier 1 |
| **Policy Pivot** | Monitor 5-year plans; exit if AI deprioritized |
| **Execution Failures** | Focus on Tier 2 (infrastructure) vs Tier 1 (chip design) |
| **Liquidity** | Avoid <500M RMB daily volume; prefer HK-listed for size |
| **Currency** | HK positions naturally USD-hedged; SH/SZ positions have CNY exposure |

### Correlation Check
- Avoid if portfolio already has high China tech exposure
- Check correlation with existing positions in BABA, TCEHY, etc.

---

## Expected Performance

### Backtest Assumptions (Proxy)
Historical testing via similar themes (2014-2015 "Made in China 2025", 2020-2021 semis):
- **Win Rate:** 60-65% (theme plays have higher variance)
- **Avg Winner:** +25%
- **Avg Loser:** -12%
- **Profit Factor:** 2.0-2.5
- **Sharpe:** 1.3-1.8 (higher returns, higher volatility)
- **Max Drawdown:** -20% (theme concentration risk)

### Scenario Analysis
| Scenario | Probability | Return Impact |
|----------|-------------|---------------|
| Successful localization | 30% | +40-60% |
| Partial progress | 45% | +15-25% |
| Stalled by sanctions | 20% | -10-20% |
| Major policy shift | 5% | -30%+ |

---

## Data Requirements

### Essential (Free)
- [ ] OHLCV for universe (yfinance/Bloomberg)
- [ ] Xinhua/State Council policy announcements (scraping)
- [ ] Quarterly earnings (Tushare/FMP)
- [ ] Stock Connect flows for HK-listed

### Optional ($)
- [ ] Supply chain data (semiconductor equipment orders)
- [ ] Industry capex tracking (Bernstein, Morgan Stanley)
- [ ] NLP sentiment on China tech (RavenPack/Benzinga)

---

## Academic Support

- **Industrial Policy Effects:** China semiconductor subsidies (2014-2024) show 18-month investment cycles
- **Trend Following in Concentrated Themes:** Hurst et al. (2017) - momentum works in sector-specific contexts
- **Limits to Arbitrage:** Theme plays have high dispersion; stock selection matters (Shleifer & Vishny, 1997)

---

## Related Strategies

- **AH Premium Arbitrage:** May overlap with HK-listed AI plays (9988, 0700)
- **China Policy Drift:** Same signal source (policy NLP)
- **RSI Mean Reversion CN:** Entry timing for oversold positions

---

## Testing Plan

1. **Phase 1:** Validate universe selection (20 names)
2. **Phase 2:** Test policy signal using historical announcements (2018-2024)
3. **Phase 3:** Full backtest with capex filtering
4. **Phase 4:** Paper trade 3-6 months

---

**Status:** IDEA → Pending Data Collection  
**Priority:** HIGH (thematic macro tailwinds)  
**Effort:** Medium (needs policy news tracking)  
**Expected Validation:** 2-3 weeks
