# Telegram Summary Reporting Format

**Chat ID:** `-5175536290` (JTCML Algo Researcher)  
**Frequency:** Twice daily (HK Open 09:15 HKT, US Close 05:00 HKT)  
**Purpose:** Share key findings, stock recommendations, and strategy attribution

---

## HK Open Summary Format (09:15 HKT)

```
📊 HK Open Summary — 2026-02-17

🎯 KEY FINDINGS:
• Overnight US: NVDA +3.2%, AI hardware momentum continues
• No Adobe-style drops in SaaS (-5% max)
• CK Hutchison (0001.HK): No Panama news, flat pre-market

📈 BUY RECOMMENDATIONS:
| Ticker | Strategy | Conviction | Rationale |
|--------|----------|------------|-----------|
| VRT | GPU Supply Chain (Tertiary) | ⭐⭐⭐⭐ | 2-4 week info lag, cooling demand surging |
| 0700.HK | China Tech Momentum | ⭐⭐⭐ | Following US AI trend, undervalued vs US peers |

📉 SELL/SHORT RECOMMENDATIONS:
| Ticker | Strategy | Conviction | Rationale |
|--------|----------|------------|-----------|
| 0001.HK | Panama Network (Geopolitical) | ⭐⭐ | Monitor for court ruling volatility |

⚡ STRATEGY ATTRIBUTION:
• Information Arbitrage — Tertiary Wave: VRT
• Information Arbitrage — Secondary Wave: 0700.HK ( Tencent )
• Network Effects: 0001.HK (CK Hutchison)

📝 NEXT ACTIONS:
• Watch for Panama court timeline updates
• Monitor VRT entry on any dip
```

---

## US Close Summary Format (05:00 HKT)

```
📊 US Close Summary — 2026-02-17

🎯 KEY FINDINGS:
• NVDA +5.4% on Blackwell demand — tertiary wave intact
• TEAM -3.2% on AI disruption fears — DVS thesis playing out
• No new Adobe-style -10%+ drops detected

📈 BUY/LONG RECOMMENDATIONS:
| Ticker | Strategy | Conviction | Rationale | Entry Signal |
|--------|----------|------------|-----------|--------------|
| VRT | GPU Supply Chain (Tertiary) | ⭐⭐⭐⭐ | Cooling demand lag, 3-6 week τ | NVDA strength |
| FN | GPU Supply Chain (Tertiary) | ⭐⭐⭐ | Optical components, 4-8 week τ | Scale in |
| MP | GPU Supply Chain (Quaternary) | ⭐⭐⭐ | Rare earths, speculative 2-4 mo | Small position |

📉 SELL/SHORT RECOMMENDATIONS:
| Ticker | Strategy | Conviction | Rationale | Entry Signal |
|--------|----------|------------|-----------|--------------|
| TEAM | Adobe Correlation (DVS) | ⭐⭐⭐⭐⭐ | DVS 1008, slow AI response | Short on strength |
| ADSK | Adobe Correlation (DVS) | ⭐⭐⭐⭐ | Generative design threat | Monitor -5% bounce |
| NOW | Adobe Correlation (DVS) | ⭐⭐⭐ | Platform moat but premium | Light short |

⚡ STRATEGY ATTRIBUTION:
• Information Arbitrage — Secondary Wave: TEAM, ADSK, NOW (SaaS AI disruption)
• Information Arbitrage — Tertiary Wave: VRT, FN (GPU supply chain)
• ARASO Factor Model: AAPL (residual z-score -1.8, HMM 0.75)
• Disruption Vulnerability (DVS): TEAM (1008), ADSK (1680)
• Network Effects: CKH (Panama, monitoring)

📊 PORTFOLIO UPDATE:
| Ticker | Position | Today's P&L | Action |
|--------|----------|-------------|--------|
| TEAM | Short | +3.2% | Hold, target -15% |
| VRT | Long | +2.1% | Add on -3% dip |

🌏 HK PREP:
• Watch 0001.HK for Panama developments
• China tech (0700.HK, 9988.HK) following US AI trend
• Correlation: US-HK tech ≈ 0.85

📝 NEXT ACTIONS:
• Scale into MP if NVDA continues strength
• Tighten TEAM stop to entry -2%
• Monitor job postings for Adobe AI response
```

---

## Reporting Requirements

### Must Include:

1. **Key Findings** (3-5 bullet points)
   - Major price moves
   - Disruption events detected
   - Information decay measurements

2. **Buy/Long Recommendations**
   - Ticker symbol
   - Strategy name (e.g., "GPU Supply Chain (Tertiary Wave)")
   - Conviction (⭐ to ⭐⭐⭐⭐⭐)
   - Rationale (1 sentence)
   - Entry signal (for US Close)

3. **Sell/Short Recommendations**
   - Same format as Buy recommendations
   - Include entry timing guidance

4. **Strategy Attribution**
   - List all active strategies
   - Map each recommendation to specific strategy
   - Include ARASO factor model signals if applicable

5. **Portfolio Update** (US Close only)
   - Current positions
   - Today's P&L
   - Action (Hold/Add/Reduce/Close)

6. **HK Prep** (US Close only)
   - HK-listed stocks to watch
   - Correlation expectations
   - Overnight catalysts

### Strategy Names to Use:

- `Information Arbitrage — Secondary Wave`
- `Information Arbitrage — Tertiary Wave`
- `Information Arbitrage — Quaternary Wave`
- `ARASO Factor Model` (with residual z-score if available)
- `Disruption Vulnerability (DVS)`
- `Network Effects (Geopolitical)`
- `Network Effects (Supply Chain)`
- `Predictive Edge (Job Postings)`
- `Predictive Edge (Patents)`

### Conviction Levels:

| Stars | Meaning | Position Size |
|-------|---------|---------------|
| ⭐⭐⭐⭐⭐ | Extremely high confidence | Full position (4-5% risk) |
| ⭐⭐⭐⭐ | High confidence | Standard position (2-3% risk) |
| ⭐⭐⭐ | Moderate confidence | Half position (1-2% risk) |
| ⭐⭐ | Low confidence / monitoring | Watchlist only |
| ⭐ | Speculative | Paper trade only |

---

## How to Send

The agent should use the message tool:

```python
message(
    action="send",
    channel="telegram",
    target="-5175536290",
    message="[Formatted summary as above]"
)
```

---

*Format Version: 1.0*  
*Updated: 2026-02-16*
