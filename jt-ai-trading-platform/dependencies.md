# JT AI Trading Platform - Dependency Map

**Generated**: 2026-02-16  
**Scope**: Complete file-level dependency mapping for backend, frontend, and database

---

## Backend Dependencies

### Entry Point
| File | Responsibility | Depends On |
|------|---------------|------------|
| `main.py` | FastAPI app, route handlers, scheduler loop | `session.py`, `wholistic_pipeline.py`, `research_swarm.py`, `ib_service.py`, `ib_web_service.py`, `trading_service.py`, `strategy_manager.py` |

### Database Layer (`app/db/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `session.py` | SQLAlchemy engine, connection pooling, ORM models | `boto3` (RDS auth) | sqlalchemy, psycopg2-binary, boto3 |
| `models.py` | Additional model definitions (if any) | `session.py` | - |

### Service Layer (`app/services/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `strategy_manager.py` | Strategy lifecycle, PnL calc, backtesting | `session.py` (QuantStrategy, Trade, GlobalState), `ib_web_service.py` | sqlalchemy, yfinance (optional fallback) |
| `trading_service.py` | Automated signal-based execution | `session.py`, `ib_web_service.py` | - |
| `ib_service.py` | IBKR TWS socket connection | - | ib_insync |
| `ib_web_service.py` | IBKR Client Portal REST API | - | requests, urllib3 |
| `judge.py` | Strategy evaluation logic | - | - |
| `macro_service.py` | Macroeconomic data aggregation | - | - |
| `quant_service.py` | Quantitative analysis utilities | - | - |
| `supervisor.py` | System health monitoring | - | - |
| `visual_agent.py` | Chart/visual generation | - | - |

### Core Logic Layer (`app/core_logic/`)

#### Agents (`agents/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `research_swarm.py` | Multi-agent LLM orchestration | `search.py` (tools) | langchain_openai, python-dotenv |
| `wholistic_swarm.py` | Market regime analysis | - | - |
| `shock_watch.py` | Geopolitical shock detection | - | - |
| `social_media_analyst.py` | Sentiment analysis | - | - |

#### Analysis (`analysis/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `prophet_forecast.py` | Time-series forecasting | - | prophet |
| `research_prophet.py` | Prophet model research utilities | - | prophet |
| `analyze_sentiment.py` | Text sentiment scoring | - | - |
| `expert_interpretation.py` | LLM-based signal interpretation | - | - |
| `enhance_alpha.py` | Alpha signal enhancement | - | - |
| `hybrid_alpha.py` | Multi-factor alpha combination | - | - |
| `final_alpha_report.py` | Alpha reporting | - | - |

#### Backtesting (`backtesting/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `backtest_strategy.py` | Strategy backtesting | - | - |
| `backtester.py` | Core backtesting engine | - | pandas |
| `reflective_backtester.py` | Self-analyzing backtester | - | - |
| `strategy_sim.py` | Strategy simulation | - | - |
| `swarm_backtester.py` | Multi-agent backtesting | - | - |

#### Data (`data/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `wholistic_pipeline.py` | Main ETL pipeline (stocks, fx, crypto, commodities) | `session.py`, `prophet_forecast.py`, `research_swarm.py` | yfinance, pandas, pandas-ta, numpy, prophet |
| `ingest_stocks.py` | Stock data ingestion | - | yfinance |
| `ingest_to_rds.py` | RDS data loader | - | - |
| `discover_tickers.py` | Ticker universe discovery | - | - |
| `alpha_vantage_fundamentals.py` | Fundamental data fetch | - | - |
| `build_gold_layer.py` | Gold layer construction | - | - |
| `sentiment_pipeline.py` | Sentiment data pipeline | - | - |

#### Tools (`tools/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `search.py` | Web search for market news | - | requests |
| `technical_indicators_tools.py` | TA calculation utilities | - | pandas-ta |

### Schemas (`app/schemas/`)
| File | Responsibility | Depends On |
|------|---------------|------------|
| `project.py` | Pydantic request/response models | pydantic |

### Scripts (Root `backend/`)
| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `run_rds_pipeline.py` | Standalone RDS pipeline runner | - | - |
| `trading_pipeline_hkt.py` | HKT-timezone trading pipeline | - | - |
| `enrich_commodities.py` | Commodity data enrichment | - | - |
| `enrich_crypto.py` | Crypto data enrichment | - | - |
| `enrich_fx.py` | FX data enrichment | - | - |
| `enrich_hkd.py` | HKD-specific enrichment | - | - |
| `fix_sequence.py` | Database sequence repair | - | - |

### Tests
| File | Responsibility | Depends On |
|------|---------------|------------|
| `test_api.py` | API endpoint tests | FastAPI TestClient |

---

## Frontend Dependencies

| File | Responsibility | Depends On | External Libraries |
|------|---------------|------------|-------------------|
| `App.jsx` | Main dashboard component | API: `/api/signals/1`, `/api/inventory/evaluate`, `/api/macro/pulse` | React, axios/fetch |
| `App_part2.jsx` | Dashboard extension | Same as App.jsx | React |
| `App_velocity.jsx` | HFT matrix view | API: `/api/hft/matrix`, `/api/velocity/trades` | React |
| `ProfessionalLiveTrading.jsx` | Live trading UI | API: `/api/velocity/ib/*`, `/api/quant/*` | React |
| `ProfessionalSimulationLab.jsx` | Simulation interface | API: `/api/quant/*` | React |
| `main.jsx` | React entry point | All components | ReactDOM |
| `LiveTradingStyles.js` | CSS-in-JS styles | - | - |
| `CandlestickChart.jsx` | Chart component | API data | Charting library |

---

## Database Schema Dependencies

### Schema: `bronze` (Raw Data)
| Table | Populated By | Consumed By |
|-------|-------------|-------------|
| `raw_stock_data` | `ingest_stocks.py` | `wholistic_pipeline.py` |

### Schema: `silver` (Cleaned Data)
| Table | Populated By | Consumed By |
|-------|-------------|-------------|
| `historical_stock_data` | Pipeline | Gold layer |

### Schema: `gold` (Metrics & Config)
| Table | Populated By | Consumed By |
|-------|-------------|-------------|
| `stock_metrics` | `wholistic_pipeline.py` | `consumption.stock` |
| `fx_metrics` | `wholistic_pipeline.py` | `consumption.fx` |
| `crypto_metrics` | `wholistic_pipeline.py` | `consumption.crypto` |
| `commodity_metrics` | `wholistic_pipeline.py` | `consumption.commodities` |
| `quant_strategies` | `strategy_manager.py` | Trading execution |
| `strategy_thresholds` | Manual config | Backtest engine |
| `strategy_configs` | Manual config | Signal scoring |
| `metric_definitions` | Manual config | Formula display |
| `sync_schedules` | `main.py` | Scheduler loop |
| `asset_registry` | Manual/admin | All pipelines |
| `llm_key_entities_config` | Admin | Research swarm |
| `strategy_performance` | Backtester | Performance API |
| `backtest_curve_data` | Backtester | Charting |

### Schema: `consumption` (UI Layer)
| Table | Populated By | Consumed By |
|-------|-------------|-------------|
| `stock` | `refresh_stock_layer()` | `/api/signals/1` |
| `fx` | `refresh_fx_layer()` | `/api/fx/pairs` |
| `crypto` | `refresh_crypto_layer()` | `/api/crypto/pairs` |
| `commodities` | `refresh_commodity_layer()` | `/api/commodities/all` |
| `market` | `refresh_indices_and_mood()` | `/api/market/outlook` |
| `contrarian` | Research swarm | Contrarian signals |
| `inventory` | Trading service | `/api/inventory/*` |
| `trades` | Strategy manager | `/api/velocity/trades` |
| `hft_matrix` | `refresh_hft_layer()` | `/api/hft/matrix` |
| `swarm_logs` | Research swarm | Logging |
| `global_state` | Multiple | System state API |

---

## External Service Dependencies

### Critical Path (System won't function without)
| Service | Usage | Fallback |
|---------|-------|----------|
| AWS RDS PostgreSQL | All persistence | None — system halts |
| yfinance | Market data | None — stale data |

### Functional Path (Degraded mode possible)
| Service | Usage | Fallback |
|---------|-------|----------|
| IBKR Gateway | Live trading | Simulation mode |
| IBKR Client Portal | Web trading | Manual trading |
| Azure OpenAI | LLM analysis | Static responses |
| Alternative.me | Fear & Greed | RSI proxy |

### Development/Build
| Tool | Purpose |
|------|---------|
| uvicorn | ASGI server |
| vite | Frontend build |
| eslint | JS/TS linting |
| tailwindcss | CSS framework |

---

## Dependency Graph Visualization

```
                    ┌─────────────────────────────────────┐
                    │           main.py                   │
                    │  (FastAPI Entry + Scheduler)        │
                    └─────────────┬───────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Services    │       │   Core Logic    │       │      DB         │
│               │       │                 │       │                 │
│ strategy_mgr  │◄─────▶│ wholistic_pipe  │◄─────▶│  session.py     │
│ trading_svc   │◄─────▶│ research_swarm  │       │    (ORM)        │
│ ib_service    │       │ prophet_fcst    │       │                 │
│ ib_web_svc    │       │ backtester      │       │  RDS PostgreSQL │
└───────┬───────┘       └────────┬────────┘       └─────────────────┘
        │                        │
        │         ┌──────────────┴──────────────┐
        │         │                             │
        ▼         ▼                             ▼
┌───────────────┐                     ┌─────────────────┐
│  IBKR Gateway │                     │   yfinance      │
│  (ib_insync)  │                     │   (market data) │
└───────────────┘                     └─────────────────┘
        │                                      │
        ▼                                      ▼
┌───────────────┐                     ┌─────────────────┐
│  Azure OpenAI │                     │  Alternative.me │
│  (LangChain)  │                     │  (Fear/Greed)   │
└───────────────┘                     └─────────────────┘
```

---

## Circular Dependency Check

**Status**: ✅ No circular dependencies detected

**Notable patterns**:
- `session.py` is a leaf dependency (only depends on boto3/sqlalchemy)
- `main.py` is the root orchestrator (depends on everything)
- Services depend on `session.py` but not on each other (good)
- `ib_web_service` is standalone (can be mocked easily)

---

## Version Constraints

| Package | Constraint | Reason |
|---------|-----------|--------|
| python | >=3.12, <3.13 | Type hint compatibility |
| numpy | >=2.2, <2.3 | Prophet compatibility |
| sqlalchemy | >=2.0.46 | Modern ORM features |
| fastapi | >=0.128.0 | Latest security patches |
| ib-insync | >=0.9.86 | IBKR API stability |

---

*End of Dependency Map*
