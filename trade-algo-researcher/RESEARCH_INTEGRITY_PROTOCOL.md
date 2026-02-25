# RESEARCH INTEGRITY PROTOCOL
# Enforced from 2026-02-21

## CORE PRINCIPLES

1. **NO MADE-UP NUMBERS**
   - Every statistic must come from actual backtest execution
   - No theoretical projections
   - No "expected" Sharpe ratios without validation

2. **NO BLIND ACCEPTANCE OF PRE-POPULATED DATA**
   - `gold.strategy_definitions` data must be verified
   - Every strategy re-backtested independently
   - Academic paper results = hypothesis only, not validation

3. **FACT-BASED RESEARCH ONLY**
   - Data source must be traceable (silver/gold schema, yfinance, etc.)
   - Backtest code must be reviewable
   - Results must be reproducible

4. **TRANSPARENT METHODOLOGY**
   - Entry/exit rules explicitly defined
   - Transaction costs included (slippage, commission)
   - Out-of-sample testing where possible
   - Survivorship bias accounted for

---

## REVALIDATION CHECKLIST

For EVERY strategy before marking "validated":

- [ ] Backtest executed with actual historical data
- [ ] Minimum 100 trades (or all available data if less)
- [ ] Transaction costs included (0.05% slippage, $0.005/share)
- [ ] Sharpe ratio calculated from actual returns
- [ ] Max drawdown measured from equity curve
- [ ] Win rate > 50% (mean reversion) or > 55% (momentum)
- [ ] Results documented in `backtest_results` table
- [ ] Methodology written to `research_docs/`

---

## DATA SOURCES (APPROVED)

| Source | Type | Access |
|--------|------|--------|
| silver.historical_stock_data | OHLCV | Verified |
| gold.etf_daily_data | ETF prices | Verified |
| gold.stock_metrics | RSI, MACD | Verified |
| yfinance | Supplementary | Verified |
| FRED | Economic data | Verified |
| HKEX/SGX | Exchange data | Needs scraper |

---

## RED FLAGS (REJECT IMMEDIATELY)

- Sharpe ratios without backtest execution
- "Expected" win rates from papers
- Pre-populated validation without verification
- Proxy data presented as actual (e.g., HK tickers for SG banks)
- Claims without reproducible code

---

## COMMITMENT

I will:
1. Revalidate ALL 25+ strategies from scratch
2. Reset all "validated" statuses to "testing" or "idea"
3. Only promote strategies with rigorous backtest evidence
4. Document every assumption and limitation
5. Admit when data is insufficient

---

Enforced: 2026-02-21  
Researcher: Trade Algo Researcher  
Status: PROTOCOL ACTIVE
