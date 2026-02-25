# JT AI Trading Platform - System Architecture

## Document Information
- **Version**: 1.0
- **Date**: 2026-02-16
- **Author**: Cheri (AI Trading Systems Engineer)
- **Scope**: Full-stack trading platform with IBKR integration

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Dashboard   │  │   Live       │  │  Simulation  │  │   Velocity      │ │
│  │  (Signals)   │  │   Trading    │  │     Lab      │  │   Trading       │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │
└─────────┼─────────────────┼─────────────────┼───────────────────┼──────────┘
          │                 │                 │                   │
          └─────────────────┴────────┬────────┴───────────────────┘
                                     │ HTTPS/WSS
┌────────────────────────────────────┴─────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
│                         FastAPI (Port 8000)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   REST API   │  │   CORS       │  │  Scheduler   │  │   Middleware │ │
│  │   Routes     │  │   Handler    │  │   Loop       │  │   (Cookies)  │ │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────┼────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER (Domain Logic)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Strategy   │  │   Trading    │  │  IBKR Web    │  │   IBKR Quant │ │
│  │   Manager    │  │   Service    │  │   Service    │  │   Service    │ │
│  │  (FX/Quant)  │  │  (Auto-Exec) │  │(Client Portal│  │(ib_insync)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │                  │         │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐│
│  │   Macro      │  │   Judge      │  │   Visual     │  │   Supervisor ││
│  │   Service    │  │   Service    │  │   Agent      │  │   Service    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────┼────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────────────┐
│                      CORE LOGIC LAYER (Agents & Analysis)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Swarm     │  │   Prophet    │  │   Technical  │  │   Backtest   │ │
│  │   (Research) │  │   Forecast   │  │   Indicators │  │   Engine     │ │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                                                                │
│  ┌──────┴───────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   Wholistic  │  │    Shock     │  │   Social     │  │   Wholistic  ││
│  │     Swarm    │  │    Watch     │  │   Media      │  │   Pipeline   ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────┼────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (Multi-Tier Schema)                      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     AWS RDS PostgreSQL                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │  │
│  │  │  BRONZE  │→ │  SILVER  │→ │   GOLD   │→ │   CONSUMPTION      │ │  │
│  │  │  (Raw)   │  │(Cleaned) │  │(Metrics) │  │   (UI-Optimized)   │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  External: yfinance │ Alternative.me (Fear & Greed) │ IBKR Gateway      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Backend Services (Python/FastAPI)

| Component | Responsibility | Key Technologies |
|-----------|---------------|------------------|
| `main.py` | FastAPI entry, route definitions, scheduler orchestration | FastAPI, SQLAlchemy, asyncio |
| `strategy_manager.py` | Quant strategy lifecycle (create/tick/PnL) | SQLAlchemy, FIFO accounting |
| `trading_service.py` | Automated signal execution | IB Web Service |
| `ib_service.py` | IBKR TWS/Gateway socket connection (ib_insync) | ib_insync |
| `ib_web_service.py` | IBKR Client Portal API wrapper | requests |
| `research_swarm.py` | Multi-agent LLM analysis (Azure OpenAI) | LangChain |
| `wholistic_pipeline.py` | Data ingestion & signal generation | yfinance, prophet, pandas-ta |

### 2.2 Frontend (React/Vite)

| Component | Responsibility |
|-----------|---------------|
| `App.jsx` | Main dashboard (signals, inventory, macro) |
| `ProfessionalLiveTrading.jsx` | Live trading interface |
| `ProfessionalSimulationLab.jsx` | Backtesting & simulation |
| `App_velocity.jsx` | High-frequency trading matrix |
| `CandlestickChart.jsx` | Technical charting |

### 2.3 Database Schema (4-Tier)

| Tier | Schema | Purpose |
|------|--------|---------|
| Bronze | `bronze` | Raw market data ingestion |
| Silver | `silver` | Cleaned, normalized data |
| Gold | `gold` | Computed metrics, strategies, configs |
| Consumption | `consumption` | UI-optimized denormalized views |

---

## 3. Data Flow

```
1. INGESTION (yfinance + external APIs)
   └─→ bronze.raw_stock_data / fx_metrics / crypto_metrics

2. TRANSFORMATION (wholistic_pipeline.py)
   └─→ Prophet forecasts, technical indicators, sentiment scoring
   └─→ gold.stock_metrics / fx_metrics / crypto_metrics

3. ENRICHMENT (Research Swarm)
   └─→ LLM-based market mood, rationale generation
   └─→ gold.llm_key_entities_config

4. CONSUMPTION (API Layer)
   └─→ Pre-joined tables for frontend consumption
   └─→ consumption.stock / fx / crypto / commodities / hft_matrix

5. EXECUTION (Strategy Manager + IBKR)
   └─→ Signal → Trade → Inventory Update
   └─→ consumption.trades / consumption.inventory
```

---

## 4. Key Design Patterns

### 4.1 Multi-Asset Class Support
- Unified pipeline with asset-specific metric handlers
- Registry pattern in `gold.asset_registry`
- Polymorphic consumption tables per asset class

### 4.2 Execution Modes
| Mode | Description | Use Case |
|------|-------------|----------|
| `SIMULATION` | Paper trading with virtual PnL | Strategy validation |
| `PAPER` | IBKR paper account execution | Live testing |
| `LIVE` | Production trading | Production (not fully implemented) |

### 4.3 Scheduler-Driven Architecture
- Async scheduler loop in `main.py`
- Frequency map: 1min/5min/1hr/1day
- Component triggers: indices, stocks, fx, crypto, commodities, hft

### 4.4 FIFO PnL Accounting
- Separate long/short position tracking
- Realized vs unrealized PnL calculation
- Per-strategy equity curves

---

## 5. External Dependencies

| Service | Purpose | Integration Point |
|---------|---------|-------------------|
| **IBKR Gateway** | Order execution | `ib_service.py` (socket) |
| **IBKR Client Portal** | Web-based trading | `ib_web_service.py` (REST) |
| **Azure OpenAI** | LLM analysis | `research_swarm.py` |
| **yfinance** | Market data | `wholistic_pipeline.py` |
| **AWS RDS** | Persistence | `session.py` |
| **Alternative.me** | Fear & Greed index | `wholistic_pipeline.py` |

---

## 6. Deployment Architecture

### 6.1 Infrastructure Stack
```
┌─────────────────────────────────────────────────────────────┐
│                        Cloudflare                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  SSL/TLS (Full Strict)                                  │ │
│  │  ├─ Edge Certificate: trade.jtcml.com                   │ │
│  │  └─ Origin Certificate: Cloudflare Origin CA            │ │
│  └───────────────────────┬─────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTPS (443)
┌──────────────────────────┼───────────────────────────────────┐
│                      AWS EC2                                 │
│  ┌───────────────────────┴─────────────────────────────────┐ │
│  │  Nginx (Reverse Proxy)                                   │ │
│  │  ├─ Port 80 → 443 Redirect                               │ │
│  │  ├─ Port 443 → SSL Termination                           │ │
│  │  └─ /api/* → FastAPI (localhost:8000)                    │ │
│  └───────────────────────┬─────────────────────────────────┘ │
│                          │                                    │
│  ┌───────────────────────┴─────────────────────────────────┐ │
│  │  FastAPI Backend (Python 3.12)                           │ │
│  │  ├─ Port 8000 (localhost only)                           │ │
│  │  ├─ Async scheduler loop                                 │ │
│  │  └─ IBKR integration (socket + web)                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │ PostgreSQL
┌──────────────────────────┴───────────────────────────────────┐
│                      AWS RDS                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL 15+                                         │ │
│  │  ├─ Bronze/Silver/Gold/Consumption schemas              │ │
│  │  └─ IAM auth token rotation                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Runtime Configuration
| Component | Host | Port | Notes |
|-----------|------|------|-------|
| Nginx | 0.0.0.0 | 80, 443 | Public-facing |
| FastAPI | 127.0.0.1 | 8000 | Localhost only (via nginx) |
| RDS | VPC | 5432 | Private subnet |

### 6.3 SSL/TLS Flow
1. **Client** → `https://trade.jtcml.com`
2. **Cloudflare** → SSL termination (Edge cert)
3. **Cloudflare** → Origin pull with Origin CA cert
4. **Nginx** → SSL verification + reverse proxy
5. **FastAPI** → HTTP (internal)

---

## 7. Security Considerations

| Layer | Mechanism |
|-------|-----------|
| Database | IAM auth token rotation (RDS) |
| IBKR | Cookie-based session sync (middleware) |
| API | CORS restricted to `trade.jtcml.com` |
| Secrets | Environment variables (Azure OpenAI) |

---

## 7. Known Architectural Debt

1. **Price Fetching**: Dual sources (yfinance real-time + GlobalState cache) creates consistency risk
2. **Scheduler Coupling**: Strategy ticks coupled to data refresh cycles
3. **IBKR Session**: No automatic reconnection logic for expired sessions
4. **Error Handling**: Silent try/except blocks in several pipeline stages
5. **Test Coverage**: Only `test_api.py` exists — no unit tests for core logic

---

## 8. Scalability Bottlenecks

| Component | Bottleneck | Mitigation Strategy |
|-----------|-----------|---------------------|
| Prophet Forecasts | CPU-bound, blocking | Cache + async batching |
| LLM Invocations | Rate limits, latency | Queue-based + fallback |
| yfinance | IP throttling | Proxy rotation or paid API |
| Database | Connection pool exhaustion | Connection pooling (50 max) |

---

*End of Architecture Document*
