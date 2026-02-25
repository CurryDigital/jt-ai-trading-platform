# BACKTEST PLAN: New Hypotheses (2020-2026 Research)

**Date:** 2026-02-19  
**Phase:** Testing  
**Hypotheses:** 13  
**Priority:** High

---

## HYPOTHESIS 1: ESG Improvers
**File:** `hypotheses/active/esg_momentum_greenium.md`  
**Status:** idea → **testing**  
**Academic Basis:** Berkeley Haas (2024), IDEAS/RePEc (2024)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | S&P 500, Russell 1000 |
| Period | 2018-2024 (6 years) |
| Rebalance | Monthly |
| Entry | ESG upgrade (B→A) within 30 days |
| Exit | 9 months OR downgrade |

### Data Requirements
- ESG ratings: MSCI (paid) OR ESG ETF holdings proxy (free)
- Rating changes: Monthly updates

### Success Criteria
- Win rate > 55%
- Sharpe > 0.8
- Outperforms "high ESG levels" strategy

### Timeline: 2 weeks

---

## HYPOTHESIS 2: Retail Order Flow Imbalance
**File:** `hypotheses/active/retail_order_flow_imbalance.md`  
**Status:** idea → **testing**  
**Academic Basis:** Barber/Odean (2023), Welch (2022)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Meme stocks, high retail interest |
| Period | 2020-2024 (meme stock era) |
| Rebalance | Daily |
| Entry | Retail FOMO > 90th percentile |
| Exit | 3 days OR sentiment reversal |

### Data Requirements
- Whalesburg OR Reddit API (WallStreetBets mentions)
- Options small-lot buying data

### Success Criteria
- Win rate > 58%
- Sharpe > 1.0
- Survives GME/AMC squeeze periods

### Timeline: 3 weeks

---

## HYPOTHESIS 3: Supply Chain Reshoring
**File:** `hypotheses/active/supply_chain_reshoring.md`  
**Status:** idea → **testing**  
**Academic Basis:** Baldwin (2022), IMF (2023)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Semiconductors, Industrials, Mexico REITs |
| Period | 2022-2024 (CHIPS Act era) |
| Rebalance | Quarterly |
| Entry | Reshoring announcement OR subsidy win |
| Exit | 18 months OR theme exhaustion |

### Data Requirements
- Earnings call NLP (reshoring mentions)
- CHIPS Act awards (public data)
- Mexico industrial real estate (FIBRA)

### Success Criteria
- Win rate > 60%
- Sharpe > 0.9
- Correlation to CHIPS Act timeline

### Timeline: 4 weeks (NLP data collection)

---

## HYPOTHESIS 4: Inflation Regime Switching
**File:** `hypotheses/active/inflation_regime_switching.md`  
**Status:** idea → **testing**  
**Academic Basis:** Reis (2022), Blanchard (2023)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Multi-asset (stocks, bonds, commodities) |
| Period | 1970-2024 (multiple inflation cycles) |
| Rebalance | Monthly |
| Entry | CPI 3-month trend change |
| Exit | Regime flip confirmation |

### Data Requirements
- CPI, PCE (BLS - free)
- Wage growth (Atlanta Fed)
- Supply chain pressure (NY Fed)

### Success Criteria
- Regime prediction accuracy > 70%
- Sharpe > 1.0
- Positive returns in both regimes

### Timeline: 2 weeks

---

## HYPOTHESIS 5: LLM NLP Sentiment
**File:** `hypotheses/active/llm_nlp_sentiment.md`  
**Status:** idea → **testing**  
**Academic Basis:** Lopez-Lira (2023), Kim (2024)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | S&P 500 |
| Period | 2023-2024 (GPT-4 era) |
| Rebalance | Daily (earnings season) |
| Entry | LLM sentiment > +3 OR < -3 |
| Exit | 3 days OR sentiment reversal |

### Data Requirements
- OpenAI API ($100-500/month)
- Earnings transcripts (FactSet/SA)
- Cost: ~$0.50 per transcript

### Success Criteria
- Win rate > 60%
- Sharpe > 1.2
- Beats traditional keyword NLP

### Timeline: 2 weeks

---

## HYPOTHESIS 6: Momentum Lifecycle Combo
**File:** `hypotheses/active/momentum_lifecycle_combo.md`  
**Status:** idea → **testing**  
**Academic Basis:** Jegadeesh/Titman (1993), Hong/Stein (1999)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | US large-caps |
| Period | 1990-2024 (34 years) |
| Rebalance | Monthly |
| Entry | Stage-appropriate signal |
| Exit | Stage-appropriate exit |

### Data Requirements
- Price data (free)
- Earnings surprise (IBES paid OR free proxy)

### Success Criteria
- Win rate > 60%
- Sharpe > 1.1
- Beats standalone momentum

### Timeline: 2 weeks

---

## HYPOTHESIS 7: Accruals Quality + RSI
**File:** `hypotheses/active/accruals_quality_mean_reversion.md`  
**Status:** idea → **testing**  
**Academic Basis:** Sloan (1996)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | S&P 500 |
| Period | 2000-2024 (24 years) |
| Rebalance | Weekly |
| Entry | RSI < 30 + accruals quality filter |
| Exit | RSI > 50 OR 5 days |

### Data Requirements
- Financial statements (Compustat paid OR yfinance free)
- Accruals calculation: (NI - OCF) / Assets

### Success Criteria
- Win rate > 62%
- Sharpe > 1.3
- Improves on RSI-only baseline

### Timeline: 1 week

---

## HYPOTHESIS 8: Time-Series Momentum Overlay
**File:** `hypotheses/active/time_series_momentum_overlay.md`  
**Status:** idea → **testing**  
**Academic Basis:** Hurst/Ooi/Pedersen (2017)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Multi-asset (apply as overlay) |
| Period | 1980-2024 (44 years) |
| Rebalance | Monthly |
| Entry | 12-month excess return > 0 |
| Exit | Trend reversal |

### Data Requirements
- Price data (free)
- Risk-free rate (T-bill)

### Success Criteria
- Standalone Sharpe > 1.0
- Improves RSI strategy when combined
- Crisis alpha during 2008, 2020

### Timeline: 2 weeks

---

## HYPOTHESIS 9: Volatility Risk Premium
**File:** `hypotheses/active/volatility_risk_premium.md`  
**Status:** idea → **testing**  
**Academic Basis:** Coval/Shumway (2001)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Low-vol equities, VIX proxies |
| Period | 2004-2024 (20 years) |
| Rebalance | Monthly |
| Entry | Realized vol < 10th percentile |
| Exit | Vol spike OR 3 months |

### Data Requirements
- VIX futures (CBOE free delayed)
- Options data (paid for direct VRP)

### Success Criteria
- Win rate > 60%
- Sharpe > 1.0
- Lower drawdown than market

### Timeline: 2 weeks

---

## HYPOTHESIS 10: Quality Value (QARP)
**File:** `hypotheses/active/quality_value_qarp.md`  
**Status:** idea → **testing**  
**Academic Basis:** Asness (2018)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | S&P 500 |
| Period | 1990-2024 (34 years) |
| Rebalance | Quarterly |
| Entry | Quality > 60th AND Value > 60th |
| Exit | 12 months OR score deterioration |

### Data Requirements
- Financial statements (profitability, stability metrics)

### Success Criteria
- Win rate > 60%
- Sharpe > 1.1
- Beats quality-only and value-only

### Timeline: 2 weeks

---

## HYPOTHESIS 11: CMV Multi-Factor
**File:** `hypotheses/active/cmv_multi_factor.md`  
**Status:** idea → **testing**  
**Academic Basis:** Asness (2013), Koijen (2018)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Multi-asset (FX, bonds, commodities, equities) |
| Period | 1980-2024 (44 years) |
| Rebalance | Monthly |
| Entry | Carry + Momentum + Value combined |
| Exit | Factor reversal |

### Data Requirements
- FX: Interest rates, spot prices
- Bonds: Yield curves
- Commodities: Futures curves

### Success Criteria
- Sharpe > 1.2
- Low correlation to equities
- Positive returns in all decades

### Timeline: 3 weeks

---

## HYPOTHESIS 12: Limits to Arbitrage Exploit
**File:** `hypotheses/active/limits_to_arbitrage_exploit.md`  
**Status:** idea → **testing**  
**Academic Basis:** Shleifer/Vishny (1997)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | Russell 2000 (small/mid cap) |
| Period | 2019-2024 (5 years) |
| Rebalance | Bi-weekly (match short interest reporting) |
| Entry | Squeeze score > 0.7 |
| Exit | 20 days OR squeeze exhaustion |

### Data Requirements
- Short interest (exchange - free)
- Borrow costs (IBKR - real-time)

### Success Criteria
- Win rate > 55%
- Sharpe > 0.9
- 25-30% of winners > 30%

### Timeline: 2 weeks

---

## HYPOTHESIS 13: PEAD + NLP Enhanced
**File:** `hypotheses/active/pead_nlp_enhanced.md`  
**Status:** idea → **testing**  
**Academic Basis:** Ball/Brown (1968), Lopez-Lira (2023)

### Backtest Parameters
| Parameter | Value |
|-----------|-------|
| Universe | S&P 500, Russell 1000 |
| Period | 2020-2024 (4 years) |
| Rebalance | Daily (earnings season) |
| Entry | SUE > 1.5 + LLM sentiment > 2 |
| Exit | 5 days OR -4% stop |

### Data Requirements
- Earnings data (IBES/Zacks)
- Transcripts (FactSet/SA)
- OpenAI API ($0.50 per transcript)

### Success Criteria
- Win rate > 65%
- Sharpe > 1.3
- Beats classic PEAD

### Timeline: 2 weeks

---

## PRIORITY ORDER

### Tier 1 (Quick Wins - 1-2 weeks)
1. **Accruals Quality + RSI** - Uses existing data
2. **Time-Series Momentum** - Uses price data only
3. **Quality Value QARP** - Uses financial statements
4. **Inflation Regime** - Uses free macro data

### Tier 2 (Medium Effort - 2-3 weeks)
5. **ESG Improvers** - Need ESG data source
6. **LLM NLP Sentiment** - Need API + transcripts
7. **PEAD + NLP** - Need earnings + API
8. **Momentum Lifecycle** - Need earnings surprise data

### Tier 3 (Complex - 3-4 weeks)
9. **Retail Order Flow** - Need alternative data
10. **Supply Chain Reshoring** - Need NLP pipeline
11. **CMV Multi-Factor** - Need multi-asset data
12. **Volatility Risk Premium** - Need options/futures data
13. **Limits to Arbitrage** - Need borrow cost data

---

## RESOURCE ALLOCATION

| Week | Focus |
|------|-------|
| Week 1 | Tier 1 backtests (4 hypotheses) |
| Week 2 | Tier 2 backtests begin, Tier 1 analysis |
| Week 3 | Tier 2 completion, Tier 3 begin |
| Week 4 | Tier 3 completion, aggregate results |

---

## SUCCESS METRICS

**Promote to Strategy if:**
- Sharpe > 1.0
- Win rate > 55%
- Max DD < 15%
- 3+ years of positive returns
- Reproducible across markets (for universal strategies)

**Reject if:**
- Sharpe < 0.7 after 2 years of data
- Win rate < 50%
- Max DD > 25%
- Fails in multiple market regimes

---

**Backtesting phase initiated. 13 hypotheses moving to testing.**
