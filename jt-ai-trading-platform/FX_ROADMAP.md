# FX Trading Enhancement Roadmap

**Focus Area**: Foreign Exchange (Forex) Trading Infrastructure  
**Priority**: High (Jacky's primary interest)  
**Date**: 2026-02-16  
**Status**: Proposed - Awaiting Jacky's approval

---

## Current State Analysis

### What's Working
| Component | Status | Notes |
|-----------|--------|-------|
| FX Data Ingestion | ✅ Basic | yfinance EOD data via `refresh_fx_layer()` |
| Prophet Forecasts | ✅ | 7-day predictions for FX pairs |
| Strategy Templates | ✅ 2 templates | MR_FX (Mean Reversion), TREND_FX |
| IBKR Integration | ✅ Ready | `Forex` contract support in `ib_service.py` |
| Position Sizing | ✅ Basic | Micro lot sizing (1000 units) |
| Win Rate Sim | ✅ | Historical backtest per pair |

### Critical Gaps
| Gap | Impact | Priority |
|-----|--------|----------|
| Real-time FX ticks | High latency, stale prices | 🔴 Critical |
| No interest rate diff | Can't calculate carry trade | 🔴 Critical |
| No spread monitoring | Hidden cost erosion | 🟡 High |
| Single data source | yfinance dependency risk | 🟡 High |
| No correlation matrix | Can't hedge effectively | 🟢 Medium |
| Missing macro FX drivers | DXY, yields not factored | 🟢 Medium |

---

## Proposed FX Enhancement Phases

### Phase 1: Real-Time FX Infrastructure (Foundation)
**Goal**: Sub-second FX price updates, eliminate yfinance dependency for live trading

#### 1.1 IBKR FX Streaming
- **Task**: Implement `reqMktData` for FX pairs in `ib_service.py`
- **Output**: Real-time bid/ask/last for EURUSD, USDJPY, GBPUSD, etc.
- **Files**: `backend/app/services/ib_service.py`, `backend/app/services/fx_data_service.py` (new)
- **Deps**: ib_insync WebSocket connection
- **Latency Target**: <100ms tick-to-display

#### 1.2 FX WebSocket Feed
- **Task**: Broadcast FX ticks to frontend via WebSocket
- **Output**: Live price updates on dashboard
- **Files**: `backend/app/main.py` (add WS endpoint), frontend updates
- **Deps**: FastAPI WebSocket support

#### 1.3 Spread Monitor
- **Task**: Track bid-ask spreads, alert on widening
- **Output**: Spread %, cost impact calculation
- **Files**: `backend/app/core_logic/analysis/fx/spread_analyzer.py` (new)
- **DB**: `gold.fx_spreads` table

**Phase 1 Deliverable**: Live FX prices streaming to UI, spread-aware execution

---

### Phase 2: Carry Trade & Macro Integration (Alpha Generation)
**Goal**: Institutional-grade FX signal generation with macro overlays

#### 2.1 Interest Rate Differential Engine
- **Task**: Fetch central bank rates (Fed, ECB, BoJ, BoE)
- **Output**: Real-time carry trade attractiveness score
- **Files**: `backend/app/core_logic/data/macro_rates.py` (new)
- **API**: Use FRED API or scrape central bank sites
- **Formula**: `Carry_Score = (Target_Rate - Base_Rate) / Volatility`

#### 2.2 DXY & Yield Integration
- **Task**: Factor DXY trend and yield spreads into FX scoring
- **Output**: Macro-adjusted FX signals
- **Files**: `backend/app/core_logic/analysis/fx/macro_overlay.py` (new)
- **DB**: Enhance `gold.fx_metrics` with macro columns

#### 2.3 FX Correlation Matrix
- **Task**: Calculate rolling correlations between FX pairs
- **Output**: Hedging suggestions, risk concentration alerts
- **Files**: `backend/app/core_logic/analysis/fx/correlation_matrix.py` (new)
- **DB**: `gold.fx_correlations` table

#### 2.4 Enhanced Strategy Templates
- **Task**: Add CARRY_FX, MOMENTUM_FX, RANGE_FX templates
- **Output**: 4 FX strategies with distinct logic
- **Files**: `backend/app/services/strategy_manager.py`

**Phase 2 Deliverable**: Macro-aware FX signals with carry trade optimization

---

### Phase 3: Execution & Risk Management (Production Hardening)
**Goal**: Trade-ready FX execution with institutional risk controls

#### 3.1 Smart Order Router
- **Task**: Route FX orders to best venue (IBKR vs alternative)
- **Output**: Best execution, minimal slippage
- **Files**: `backend/app/services/fx_execution_service.py` (new)

#### 3.2 Position Hedging
- **Task**: Auto-hedge FX exposure via correlated pairs
- **Output**: Delta-neutral option for risk-off mode
- **Files**: `backend/app/services/fx_hedge_service.py` (new)

#### 3.3 Multi-Currency PnL
- **Task**: Real-time PnL in base currency (USD, HKD, etc.)
- **Output**: Currency-adjusted returns
- **Files**: `backend/app/services/fx_pnl_service.py` (new)
- **DB**: `consumption.fx_positions` table

#### 3.4 FX Risk Limits
- **Task**: Per-pair exposure limits, total FX book limit
- **Output**: Hard stops on over-concentration
- **Files**: `backend/app/services/fx_risk_manager.py` (new)

**Phase 3 Deliverable**: Production-grade FX trading with full risk framework

---

## Recommended Starting Point

**Jacky - Which phase resonates most with your immediate needs?**

| Phase | Best For | Time Estimate | Risk |
|-------|----------|---------------|------|
| **Phase 1** | Live trading readiness, latency-sensitive | 2-3 days | Low |
| **Phase 2** | Alpha generation, systematic strategies | 4-5 days | Medium |
| **Phase 3** | Institutional deployment, risk management | 3-4 days | Low |

**My Recommendation**: Start with **Phase 1.1** (IBKR FX Streaming) — it's foundational and unlocks live trading capability immediately.

---

## Technical Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────┐
│                     IBKR Gateway (TWS)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  reqMktData(Forex('EURUSD'))                          │  │
│  │  reqMktData(Forex('USDJPY'))                          │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          │ WebSocket
┌─────────────────────────┼───────────────────────────────────┐
│              FX Data Service (NEW)                         │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │  - Aggregate ticks → OHLCV (1m, 5m, 1h)              │  │
│  │  - Calculate spreads                                 │  │
│  │  - Store to gold.fx_ticks (NEW table)                │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          │ Broadcast
┌─────────────────────────┼───────────────────────────────────┐
│              FastAPI WebSocket Endpoint                     │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │  ws://trade.jtcml.com/ws/fx                          │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   React Frontend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Live FX price grid, spread indicators               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Additions

### New Table: `gold.fx_ticks`
```sql
CREATE TABLE gold.fx_ticks (
    timestamp TIMESTAMPTZ PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    bid FLOAT NOT NULL,
    ask FLOAT NOT NULL,
    mid FLOAT GENERATED ALWAYS AS ((bid + ask) / 2) STORED,
    spread_bps FLOAT GENERATED ALWAYS AS ((ask - bid) / mid * 10000) STORED
);
CREATE INDEX idx_fx_ticks_ticker_time ON gold.fx_ticks(ticker, timestamp DESC);
```

### New Table: `gold.fx_carry_metrics`
```sql
CREATE TABLE gold.fx_carry_metrics (
    date DATE PRIMARY KEY,
    pair VARCHAR(10) NOT NULL,
    base_rate FLOAT NOT NULL,
    quote_rate FLOAT NOT NULL,
    rate_diff FLOAT NOT NULL,
    carry_yield_annual FLOAT NOT NULL,
    attractiveness_score FLOAT NOT NULL
);
```

---

## Questions for Jacky

1. **Data Priority**: Is real-time FX streaming critical, or are 1-minute bars sufficient?
2. **Currency Pairs**: Which pairs are priority? (Majors: EURUSD, USDJPY, GBPUSD, or exotics too?)
3. **Carry Trade**: Do you hold positions overnight to collect interest, or day-trading only?
4. **Risk Tolerance**: What's max FX exposure as % of portfolio?
5. **Broker Backup**: If IBKR FX fails, do you have backup broker (e.g., OANDA, Forex.com)?

---

*Awaiting Jacky's direction on Phase selection*
