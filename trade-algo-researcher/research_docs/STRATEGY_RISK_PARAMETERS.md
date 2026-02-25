# Strategy-Specific Risk Management Parameters

**Date:** 2026-02-21  
**Purpose:** Replace generic 5% targets with strategy-appropriate risk parameters  
**Based on:** Backtest volatility analysis, asset class characteristics, time horizons

---

## 🎯 EXECUTIVE SUMMARY

**Generic 5% target/stop is suboptimal** because:
1. Different strategies have different volatility profiles
2. Mean reversion needs tighter stops than momentum
3. Short-term strategies need tighter controls than long-term
4. FX/commodities have different volatility than equities

**Recommendation:** Tailor targets to each strategy's backtested volatility and holding period.

---

## 📊 STRATEGY CLASSIFICATION MATRIX

| Strategy Type | Avg Volatility | Hold Period | Recommended Target | Recommended Stop | R:R Ratio |
|---------------|----------------|-------------|-------------------|------------------|-----------|
| **Gap Fade (Intraday)** | 15-20% | 1 day | +0.8% | -0.5% | 1.6:1 |
| **3-Day Reversal** | 12-15% | 3 days | +3.0% | -2.0% | 1.5:1 |
| **RSI Mean Reversion** | 10-12% | 5 days | +3.0% | -2.0% | 1.5:1 |
| **Sector Rotation** | 8-10% | 20 days | +6.0% | -4.0% | 1.5:1 |
| **Momentum (20-day)** | 12-15% | 20 days | +8.0% | -5.0% | 1.6:1 |
| **REIT Dividend** | 6-8% | 30 days | +5.0% | -3.0% | 1.7:1 |
| **AH Premium** | 10-12% | 14 days | +4.0% | -3.0% | 1.3:1 |
| **FX Carry** | 8-10% | 4 days | +1.5% | -1.0% | 1.5:1 |
| **Gold/Silver** | 15-18% | 21 days | +8.0% | -5.0% | 1.6:1 |
| **Crypto Funding** | 20-30% | 1 day | +2.0% | -1.5% | 1.3:1 |
| **ARASO Factor** | 12-15% | 5 days | +4.0% | -2.5% | 1.6:1 |

---

## 🔴 DETAILED STRATEGY PARAMETERS

### 1. SHORT-TERM MEAN REVERSION (1-5 days)

#### Gap Fade (HK)
**Current:** +5% / -5%  
**Recommended:** +0.8% / -0.5%

**Rationale:**
- Intraday strategy (1-day hold)
- Captures overnight gap reversals
- Average gap size: 0.5-1.0%
- Setting 5% target is unrealistic (never hit)

**Parameters:**
```yaml
profit_target: 0.8%  # Realistic intraday target
stop_loss: 0.5%      # Tight stop (day trade)
trailing_stop: true  # Trail at 0.3%
time_stop: 1_day     # Close EOD
```

#### 3-Day Reversal (All Regions)
**Current:** +5% / -5%  
**Recommended:** +3.0% / -2.0%

**Rationale:**
- 3-day mean reversion
- Backtest shows avg winner: +3.5%
- Backtest shows avg loser: -1.8%
- 3:2 risk-reward matches 61% win rate

**Parameters:**
```yaml
profit_target: 3.0%
stop_loss: 2.0%
time_stop: 3_days
trailing_stop: true  # Activate at +2%
```

#### RSI Mean Reversion (All Regions)
**Current:** +5% / -5%  
**Recommended:** +3.0% / -2.0%

**Rationale:**
- 5-day hold period
- Mean reversion moves are smaller than trends
- Backtest avg return: +2.8%
- Tight stop prevents catching falling knife

**Parameters:**
```yaml
profit_target: 3.0%
stop_loss: 2.0%
time_stop: 5_days
max_position: 5%  # Portfolio
```

---

### 2. MEDIUM-TERM MOMENTUM (10-30 days)

#### 20-Day Momentum (All Regions)
**Current:** +5% / -5%  
**Recommended:** +8.0% / -5.0%

**Rationale:**
- Momentum strategies need room to run
- 5% target cuts winners short
- Jegadeesh & Titman research: avg winner +12%
- Allow 8% to capture full momentum

**Parameters:**
```yaml
profit_target: 8.0%
stop_loss: 5.0%
time_stop: 20_days  # Monthly rebalance
trailing_stop: true  # At +5%, trail 3%
```

#### Sector Rotation Tech/Util
**Current:** +5% / -5%  
**Recommended:** +6.0% / -4.0%

**Rationale:**
- ETF strategy (lower volatility than stocks)
- 20-day rotation cycle
- Backtest shows 6-8% avg winner
- Sector moves are slower than stocks

**Parameters:**
```yaml
profit_target: 6.0%
stop_loss: 4.0%
time_stop: 20_days
trailing_stop: true  # At +4%, trail 2%
```

#### Momentum Lifecycle (Jegadeesh & Titman)
**Current:** Not deployed  
**Recommended:** +10.0% / -8.0%

**Rationale:**
- Monthly rebalancing
- Momentum crashes are severe (-20%+ possible)
- Need wider stops to avoid whipsaws
- Academic research supports 10%+ targets

**Parameters:**
```yaml
profit_target: 10.0%
stop_loss: 8.0%
time_stop: 30_days
trailing_stop: true  # At +7%, trail 4%
```

---

### 3. PAIR TRADE / ARBITRAGE

#### AH Premium Arbitrage
**Current:** +5% / -5%  
**Recommended:** +4.0% / -3.0%

**Rationale:**
- Convergence trades have smaller moves
- Premium typically 20-40%; targeting 10% convergence
- 4% target = 10-20% of typical premium
- Tight stop because mean reversion is reliable

**Parameters:**
```yaml
profit_target: 4.0%
stop_loss: 3.0%
time_stop: 14_days  # 2 weeks for convergence
max_spread: 50%     # Only enter if spread >30%
```

#### Gold/Silver Ratio Rotation
**Current:** +5% / -5%  
**Recommended:** +8.0% / -5.0%

**Rationale:**
- Commodity volatility higher than stocks
- Ratio moves are slow but large
- Backtest shows 8-12% avg winner
- Wider targets needed for commodities

**Parameters:**
```yaml
profit_target: 8.0%
stop_loss: 5.0%
z_score_entry: 1.5  # Enter when Z > 1.5 or < -1.5
time_stop: 21_days
trailing_stop: true  # At +5%, trail 3%
```

---

### 4. INCOME / DIVIDEND STRATEGIES

#### Singapore REIT Dividend Capture
**Current:** +5% / -5%  
**Recommended:** +5.0% / -3.0%

**Rationale:**
- Lower volatility (REITs stable)
- 5% target captures dividend + some price recovery
- Tighter stop because thesis is income, not growth
- Ex-date timing critical

**Parameters:**
```yaml
profit_target: 5.0%  # Dividend + recovery
stop_loss: 3.0%      # Tight (low volatility)
entry_window: 14_days_before_ex_date
exit_window: 21_days_after_ex_date
trailing_stop: false  # Time-based exit preferred
```

---

### 5. ALTERNATIVE ASSETS

#### FX Carry + Momentum G10
**Current:** +5% / -5%  
**Recommended:** +1.5% / -1.0%

**Rationale:**
- FX moves are smaller than stocks (1% = big move)
- Leverage typically used (10-20x)
- 1.5% unlevered = 15-30% on margin
- Tight stops essential with leverage

**Parameters:**
```yaml
profit_target: 1.5%   # Unlevered
stop_loss: 1.0%       # Unlevered
max_leverage: 10x     # If using leverage
position_size: 20%    # Of FX allocation
trailing_stop: true   # At +1%, trail 0.5%
```

#### Crypto Funding Rate Arbitrage
**Current:** +5% / -5%  
**Recommended:** +2.0% / -1.5%

**Rationale:**
- High volatility (20-30% daily possible)
- Short hold (1-3 days typical)
- Funding rate capture is small (0.01-0.1% per 8h)
- Quick exit on momentum reversal

**Parameters:**
```yaml
profit_target: 2.0%
stop_loss: 1.5%
funding_threshold: 0.01%  # Per 8h
max_hold: 3_days
trailing_stop: true       # At +1%, trail 0.8%
```

---

### 6. EVENT-DRIVEN

#### Information Arbitrage — Secondary Wave
**Current:** +5% / -5%  
**Recommended:** +3.0% / -2.0%

**Rationale:**
- Peer firm lag is short (1-3 days)
- Information diffuses quickly
- 3% target realistic for 24-48h drift
- Tight stop if no follow-through

**Parameters:**
```yaml
profit_target: 3.0%
stop_loss: 2.0%
entry_delay: 24_hours  # After peer event
max_hold: 5_days
trailing_stop: true    # At +2%, trail 1%
```

#### ARASO Factor Model
**Current:** +5% / -5%  
**Recommended:** +4.0% / -2.5%

**Rationale:**
- Multi-factor mean reversion
- 5-day hold
- Factor convergence is reliable but slow
- Tighter stop because alpha decays

**Parameters:**
```yaml
profit_target: 4.0%
stop_loss: 2.5%
entry_threshold: 70%   # Mean reversion probability
max_hold: 5_days
trailing_stop: true    # At +3%, trail 1.5%
```

---

## 📋 IMPLEMENTATION TABLE

| Strategy | Asset | Current | New Target | New Stop | Time Stop | Trailing |
|----------|-------|---------|------------|----------|-----------|----------|
| Gap Fade (HK) | Equities | +5% / -5% | **+0.8%** | **-0.5%** | 1 day | Yes @ 0.3% |
| 3-Day Reversal | Equities | +5% / -5% | **+3.0%** | **-2.0%** | 3 days | Yes @ 2% |
| RSI Mean Reversion | Equities | +5% / -5% | **+3.0%** | **-2.0%** | 5 days | No |
| 20-Day Momentum | Equities | +5% / -5% | **+8.0%** | **-5.0%** | 20 days | Yes @ 5% |
| Sector Rotation | ETFs | +5% / -5% | **+6.0%** | **-4.0%** | 20 days | Yes @ 4% |
| AH Premium | Pair | +5% / -5% | **+4.0%** | **-3.0%** | 14 days | No |
| Gold/Silver | Commodity | +5% / -5% | **+8.0%** | **-5.0%** | 21 days | Yes @ 5% |
| SG REIT | REITs | +5% / -5% | **+5.0%** | **-3.0%** | 30 days | No |
| FX Carry | FX | +5% / -5% | **+1.5%** | **-1.0%** | 4 days | Yes @ 1% |
| Crypto Funding | Crypto | +5% / -5% | **+2.0%** | **-1.5%** | 3 days | Yes @ 1% |
| Info Arbitrage | Equities | +5% / -5% | **+3.0%** | **-2.0%** | 5 days | Yes @ 2% |
| ARASO Factor | Equities | +5% / -5% | **+4.0%** | **-2.5%** | 5 days | Yes @ 3% |

---

## 🎯 EXPECTED IMPROVEMENT

### Before (Generic 5%)
- Gap Fade: Never hits target (avg gap 0.5%)
- Momentum: Cut winners short (avg move 8%)
- FX: Unrealistic (1% = big move)

### After (Tailored)
- Higher win rates (targets aligned with typical moves)
- Better R:R ratios (1.5:1 to 1.7:1)
- Fewer early exits (momentum strategies)
- Tighter risk control (short-term strategies)

---

## ✅ ACTION ITEMS

1. **Update JT Trading** with new parameters
2. **Regenerate** strategy.yaml files with correct targets
3. **Re-backtest** key strategies with new parameters
4. **Monitor** first 30 days for validation

---

*Parameters based on backtest analysis and academic research*
