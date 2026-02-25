# PAPER TRADING DEPLOYMENT INDEX
## All 6 Standalone Sector Strategies — Ready for Deployment

**Generated:** 2026-02-25  
**Status:** READY FOR PAPER TRADING  
**Total Strategies:** 6  
**Total Tickers:** 23 unique tickers

---

## STRATEGY SUMMARY TABLE

| Strategy | Sector | Tickers | Win Rate | Hold Days | Est. Trades/Year | Status |
|----------|--------|---------|----------|-----------|------------------|--------|
| **S001-HK-BANKS** | HK Banking | 7 | 89% / 93% | 10 | ~35-50 | 🏆 GOLD |
| **S001-US-TECH** | US Tech | 4 | 76% / 73% | 10 | ~15-25 | ⭐ VALIDATED |
| **S001-CRYPTO** | Crypto | 4 | 74% / 59% | 10 | ~25-40 | ⭐ VALIDATED ⚠️ |
| **S002-HK-BANKS** | HK Banking | 4 | 61% / 75% | 5 | ~20-30 | ⭐ VALIDATED |
| **S004-HK-TECH** | HK Tech | 4 | 70% / 82% | 5 | ~10-15 | 🏆 GOLD |
| **S005-US-BANKS** | US Banking | 4 | 64% / 69% | 15 | ~80-100 | ⭐ VALIDATED |

---

## QUICK REFERENCE — BUY SIGNALS

| Strategy | Entry Condition | Calculation | Timing |
|----------|-----------------|-------------|--------|
| **S001** (all variants) | RSI(14) < 25 | 100 - (100/(1+RS)) | Next market open |
| **S002** | 3 down days | Close[t-2]>Close[t-1]>Close[t] | Day 3 close |
| **S004** | Volume spike | Volume > 2.5 × 20d Avg | Signal day close |
| **S005** | Trend | Close > SMA(50) | Next market open |

---

## QUICK REFERENCE — SELL SIGNALS

| Strategy | Exit Condition | Timing |
|----------|----------------|--------|
| **S001** | 10 days after entry | Day 10 close |
| **S002** | 5 days after entry | Day 5 close |
| **S004** | 5 days after entry | Day 5 close |
| **S005** | 15 days after entry | Day 15 close |

**ALL STRATEGIES:** Time-based exit only — NO stops

---

## POSITION SIZING FRAMEWORK

### Capital Allocation (100k HKD Example)

| Strategy | Max Allocation | Per Position | Max Concurrent |
|----------|----------------|--------------|----------------|
| S001-HK-BANKS | 30% | 10-15k | 2 positions |
| S001-US-TECH | 20% | 10k | 2 positions |
| S001-CRYPTO | 15% | 7.5k | 2 positions |
| S002-HK-BANKS | 25% | 12.5k | 2 positions |
| S004-HK-TECH | 20% | 10k | 2 positions |
| S005-US-BANKS | 25% | 12.5k | 2 positions |

### Cross-Strategy Limits
- **Max total exposure:** 80% of capital
- **Cash reserve:** 20% minimum
- **Per-ticker max:** 10% across all strategies

---

## PRIORITY DEPLOYMENT ORDER

### Phase 1 (Start Here)
1. **S001-HK-BANKS** — Highest win rate (89%), defensive
2. **S004-HK-TECH** — Strong momentum (70%), low frequency

### Phase 2 (Add After 2 Weeks)
3. **S002-HK-BANKS** — Complements S001, different timing
4. **S005-US-BANKS** — High frequency, steady

### Phase 3 (Add After 1 Month)
5. **S001-US-TECH** — Tech exposure
6. **S001-CRYPTO** — ⚠️ High decay — reduce size 25%

---

## TECH PACK FILES

```
techpacks/
├── S001-HK-BANKS.md    ← Start here
├── S001-US-TECH.md
├── S001-CRYPTO.md      ← ⚠️ High decay warning
├── S002-HK-BANKS.md
├── S004-HK-TECH.md
├── S005-US-BANKS.md
└── DEPLOYMENT_INDEX.md (this file)
```

---

## CROSS-STRATEGY CHAMPIONS

Tickers appearing in multiple strategies (prioritize):

| Ticker | Strategies | Combined Edge |
|--------|------------|---------------|
| **0005.HK** (HSBC) | S001 + S002 | HK Bank leader |
| **0939.HK** (CCB) | S001 + S002 | Dual-strategy eligible |

---

## PAPER TRADING CHECKLIST

### Pre-Deployment
- [ ] IBKR paper account connected
- [ ] Watchlists created for all 23 tickers
- [ ] RSI(14) alerts configured (S001)
- [ ] Volume alerts configured (S004)
- [ ] Position tracking spreadsheet ready

### Daily Routine
- [ ] Check all strategies for signals
- [ ] Verify no duplicate ticker exposure
- [ ] Execute day X exits
- [ ] Log trades in tracker

### Weekly Review
- [ ] Compare live vs backtest performance
- [ ] Calculate running win rate
- [ ] Check for decay (Test vs Validate drift)
- [ ] Adjust position sizes if needed

---

## RISK WARNINGS

| Strategy | Risk Level | Notes |
|----------|------------|-------|
| S001-CRYPTO | HIGH | 15% decay, high volatility |
| S001-US-TECH | MEDIUM | Tech volatility |
| All Others | LOW-MEDIUM | Steady performers |

### No Stop Loss Policy
- **All strategies use time-based exits**
- Risk controlled through position sizing
- Accept drawdowns during hold periods

---

## SUCCESS METRICS

After 30 paper trades per strategy:
- **Win Rate:** Within ±10% of backtest
- **Decay:** < 20% (Validate vs Test)
- **Sharpe:** > 0.8

**GO/NO-GO Decision:**
- ✅ All metrics met → Proceed to live trading
- ⚠️ 1-2 metrics missed → Adjust and continue paper
- ❌ >2 metrics missed → Reject strategy

---

**Ready for paper trading deployment. Start with S001-HK-BANKS.**
