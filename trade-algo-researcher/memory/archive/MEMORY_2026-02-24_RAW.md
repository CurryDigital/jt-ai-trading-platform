# Trade Algo Researcher - MEMORY.md

Curated research wisdom and durable facts from continuous strategy research.

---

## Golden Strategies Archive

### E7: Multi-Indicator Consensus ⭐ TOP PERFORMER
**Discovered:** 2026-02-24  
**Average Win Rate:** 72.4% across all tickers  
**Status:** GOLDEN 🏆

**Entry Criteria:**
- Requires 3 of 4 indicators aligned:
  1. RSI > 50 (bullish momentum)
  2. MACD > Signal (trend confirmation)
  3. Price > SMA20 (short-term uptrend)
  4. ADX > 25 (trend strength)

**Best Performers:**
| Ticker | Win Rate | n | Decay |
|--------|----------|---|-------|
| MSFT | 80.7% | 327 | -3.2% |
| MSTR | 80.7% | 332 | +4.5% |
| NVDA | 78.2% | 307 | -11.2% |
| QQQ | 78.3% | 332 | -1.6% |
| AMD | 76.7% | 313 | -6.2% |
| TSLA | 73.6% | 348 | -4.2% |

**Notes:** Most consistent strategy - every tested ticker showed >55% win rate.

---

### E5: ADX Trend with Profit Target
**Discovered:** 2026-02-24  
**Average Win Rate:** 71.4% across all tickers  
**Status:** GOLDEN 🏆

**Entry Criteria:**
- ADX > 25 (trend strength)
- Price > SMA20 (bullish trend)

**Exit:** 5% profit target OR 5-day hold

**Best Performers:**
| Ticker | Win Rate | n | Decay |
|--------|----------|---|-------|
| MSTR | 79.8% | 89 | +2.4% |
| NVDA | 78.6% | 126 | -11.5% |
| TSLA | 78.5% | 214 | -7.1% |
| QQQ | 75.9% | 191 | -1.3% |
| MSFT | 75.7% | 115 | -0.2% |
| SPY | 71.9% | 196 | +8.4% |
| AMD | 70.1% | 117 | -1.1% |

**Notes:** Profit target significantly improves performance over fixed hold period.

---

## Rejected Hypotheses Archive

### H6: Stochastic + MACD Confluence ❌ REJECTED
**Status:** No signals generated on any ticker  
**Issue:** Conditions too restrictive - Stoch<20 + MACD>Signal + Price>SMA50 rarely align

### H7: ADX + Volume Expansion ❌ REJECTED  
**Status:** Insufficient samples  
**Issue:** Volume >1.5x average + breakout too rare

### H8: RSI Divergence Pattern ⚠️ VALIDATED (not Golden)
**Status:** Promising but needs tuning  
**Best:** SPY 81.2% (16 trades), COIN 56.2% (16 trades)  
**Issue:** Sample size too small for Golden status

### H9: BB Mean Reversion v2 ❌ REJECTED
**Status:** Poor performance  
**Issue:** ADX>20 filter doesn't improve mean reversion

### E6: BB Walk with Trailing Stop ❌ REJECTED
**Status:** Complete failure  
**Average Win Rate:** 4.2%  
**Issue:** Trailing stop logic exits too early

---

## Research Patterns Discovered

### What Works:
1. **Multi-indicator consensus** outperforms single indicators
2. **Profit targets** (5%) improve win rates over fixed holds
3. **Trend-following** on strong ADX (>25) stocks performs well
4. **Mega-cap tech** (MSFT, NVDA, MSTR) responds best to systematic signals

### What Doesn't Work:
1. **Trailing stops** on short-term holds - exits too early
2. **Mean reversion** in trending markets - low win rates
3. **Too many confluence conditions** - no tradeable signals
4. **AAPL-specific strategies** - high decay, doesn't generalize well

---

## Ticker-Specific Insights

### MSTR (MicroStrategy)
- Highest volatility
- Best responder to E5 (79.8% win rate)
- Trend-following works exceptionally well

### MSFT (Microsoft)
- Most consistent across strategies
- E7 Multi-Consensus: 80.7% win rate
- Low decay, reliable signals

### NVDA (NVIDIA)
- Strong trend following
- E5: 78.6%, E7: 78.2%
- Higher decay (-11%) but still profitable

### AAPL (Apple)
- Challenging for systematic strategies
- E5 shows -17.7% decay
- May need custom parameter tuning

---

## Research Methodology

**Train Period:** 2021-2022  
**Test Period:** 2023-2024  
**Hold Period:** 5 days (unless profit target hit)  
**Golden Criteria:** Test WR ≥70%, n≥30, Decay <15%  
**Validated Criteria:** Test WR ≥55%, n≥10

---

*Last Updated: 2026-02-24*
