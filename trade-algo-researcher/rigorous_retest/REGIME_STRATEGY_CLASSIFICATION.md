# REGIME-AWARE STRATEGY CLASSIFICATION
## Bull vs Bear Market Performance Split

**Regime Definition:** SPY price vs 200-day MA  
- **BULL:** SPY > 200d MA (Risk-on, trending up)
- **BEAR:** SPY < 200d MA (Risk-off, trending down)

---

## 🐂 BULL-ONLY STRATEGIES (5)

**Trade only when SPY > 200d MA:**

| Ticker | Bull WR | Bull Trades | Bear WR | Bear Trades | MC Robust |
|--------|---------|-------------|---------|-------------|-----------|
| **META** | 68.4% | 19 | 50.0% | 16 | 100% |
| **0700.HK** | 59.1% | 22 | 21.4% | 14 | 59% |
| **1398.HK** | 62.5% | 24 | 30.8% | 13 | 100% |
| **QQQ** | 60.0% | 15 | 50.0% | 22 | 98% |
| **0005.HK** | 70.0% | 10 | 41.7% | 12 | 87% |

**Characteristics:**
- Work well in risk-on environments
- Tech/Growth names dominate
- 0700.HK (Tencent) is strong in bull markets
- HK Banks (1398.HK, 0005.HK) work in bull

---

## 🐻 BEAR-ONLY STRATEGIES (3)

**Trade only when SPY < 200d MA:**

| Ticker | Bear WR | Bear Trades | Bull WR | Bull Trades | MC Robust |
|--------|---------|-------------|---------|-------------|-----------|
| **TSLA** | 62.5% | 16 | 53.8% | 26 | 82% |
| **SOL-USD** | 56.2% | 16 | 50.0% | 30 | 90% |
| **MSFT** | 76.9% | 13 | 50.0% | 20 | 85% |

**Characteristics:**
- Work in risk-off/capitulation environments
- TSLA mean reversion stronger in bear
- Crypto (SOL) capitulation trades work
- MSFT defensive in bear markets

---

## ⚖️ BOTH REGIMES (7)

**Trade in any market condition:**

| Ticker | Bull WR | Bear WR | MC Robust |
|--------|---------|---------|-----------|
| **GOOGL** | 71.4% | 57.1% | 96% |
| **SHOP** | 63.6% | 60.0% | 98% |
| **COIN** | 58.8% | 56.5% | 100% |
| **PLTR** | 66.7% | 61.5% | 100% |
| **BTC-USD** | 62.5% | 62.5% | 100% |
| **3988.HK** | 60.0% | 60.0% | 99% |
| **NVDA** | 62.5% | 61.5% | 0% ❌ |

**Characteristics:**
- True all-weather strategies
- BTC/COIN remarkably consistent
- GOOGL/SHOP/PLTR robust
- NVDA excluded (MC 0%)

---

## DEPLOYMENT FRAMEWORK

### Current Regime Check:
```
Check SPY vs 200d MA daily
- If SPY > 200d MA → Use BULL strategies
- If SPY < 200d MA → Use BEAR strategies
```

### Portfolio Construction:

#### BULL Portfolio (Current if SPY > 200d):
- META (RSI < 35)
- 0700.HK (RSI < 35)
- 1398.HK (RSI < 35)
- QQQ (RSI < 35)
- 0005.HK (RSI < 35)
- GOOGL (RSI < 35) [all-weather]
- SHOP (RSI < 35) [all-weather]
- COIN (RSI < 35) [all-weather]
- PLTR (RSI < 35) [all-weather]
- BTC-USD (RSI < 35) [all-weather]

#### BEAR Portfolio (If SPY < 200d):
- TSLA (RSI < 35)
- SOL-USD (RSI < 35)
- MSFT (RSI < 35)
- GOOGL (RSI < 35) [all-weather]
- SHOP (RSI < 35) [all-weather]
- COIN (RSI < 35) [all-weather]
- PLTR (RSI < 35) [all-weather]
- BTC-USD (RSI < 35) [all-weather]

---

## KEY INSIGHTS

### 1. Regime Matters
- Same strategy (RSI < 35) performs very differently in bull vs bear
- META: 68% bull vs 50% bear
- 0700.HK: 59% bull vs 21% bear
- **Must trade regime-appropriate strategies**

### 2. Crypto is Regime-Independent
- BTC-USD: 62.5% in BOTH regimes
- COIN: 58-56% in both
- SOL: Slight bear edge but workable

### 3. Tech Giants Split
- META: Bull only
- MSFT: Bear only
- GOOGL/SHOP: Both regimes
- **Different tech stocks for different regimes**

### 4. HK Market is Bull-Dependent
- 0700.HK, 1398.HK, 0005.HK: All bull-only
- Struggle in bear markets
- **Avoid HK in bear regimes**

---

## CURRENT STATUS (2026-02-25)

**SPY vs 200d MA:** Need to check current regime

If SPY > 200d MA → Deploy BULL portfolio (15 strategies)
If SPY < 200d MA → Deploy BEAR portfolio (11 strategies)

---

## FILES

```
rigorous_retest/
├── RETEST_REGIME_SPLIT.py          # Regime detection script
├── REGIME_STRATEGY_CLASSIFICATION.md # This file
└── [All previous test files]
```

---

**Bottom Line: 15 strategies for bull markets, 11 for bear markets, with 7 working in both regimes.**
