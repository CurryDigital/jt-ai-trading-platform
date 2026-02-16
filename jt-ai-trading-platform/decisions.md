# Decisions & ADRs

**Architectural Decision Records for JT AI Trading Platform**

---

## ADR-001: Multi-Broker Architecture (Deferred)

**Status**: Proposed  
**Date**: 2026-02-16  
**Context**: Jacky inquired about IBKR suitability for FX and Crypto in 2026.

### Decision
IBKR remains the primary broker for FX, but crypto self-custody requirement creates architectural tension. **Pattern B (IBKR + Coinbase)** recommended for future implementation.

### Rationale
- IBKR FX: Competitive spreads, deep liquidity
- IBKR Crypto: No on-chain withdrawal = paper-only exposure
- **Risk**: Counterparty risk for crypto holdings

### Consequences
- Current implementation: IBKR-only (4 coins: BTC, ETH, LTC, BCH)
- Future: Multi-broker abstraction layer needed

---

## ADR-002: Scheduler-Driven Architecture

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: Real-time vs batch processing trade-off for retail trading.

### Decision
Use async scheduler loop (30s check interval) with frequency map (1min/5min/1hr/1day) rather than event-driven or true real-time.

### Rationale
| Approach | Pros | Cons |
|----------|------|------|
| True Real-time | Sub-second latency | High infra cost, overkill for retail |
| Event-Driven | Efficient, reactive | Complex, harder to debug |
| **Scheduler (Chosen)** | Simple, predictable, cost-effective | 30s latency acceptable |

### Consequences
- Simplified debugging
- Lower AWS costs
- Acceptable latency for non-HFT strategies

---

## ADR-003: Dual IBKR Integration (Socket + Web)

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: IBKR offers TWS/Gateway (socket) and Client Portal (REST) APIs.

### Decision
Maintain both integrations:
- `ib_service.py`: Socket-based (ib_insync) for real-time streaming
- `ib_web_service.py`: REST-based for order execution flexibility

### Rationale
- Socket: Lower latency for market data
- REST: Easier cookie-based auth from browser session
- Fallback redundancy

### Consequences
- Duplicate maintenance
- Session synchronization complexity (handled via middleware)

---

## ADR-004: 4-Tier Data Architecture

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: Need to balance data quality with query performance.

### Decision
Implement Bronze → Silver → Gold → Consumption pattern on single RDS instance.

### Rationale
- **Bronze**: Raw ingestion (schema-on-read)
- **Silver**: Cleaned, typed data
- **Gold**: Computed metrics (RSI, Prophet, Alpha scores)
- **Consumption**: Pre-joined, UI-optimized (fast queries)

### Consequences
- Storage overhead (data duplicated 4x)
- Simplified frontend queries
- Easy to rebuild layers from Bronze

---

## ADR-005: FIFO PnL Accounting

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: Strategy manager needs accurate PnL for tax and performance reporting.

### Decision
Implement separate long/short queues with FIFO matching per strategy.

### Rationale
- **FIFO**: Tax-compliant in most jurisdictions
- **Separate queues**: Handles direction changes correctly
- **Realized vs Unrealized**: Clear distinction for reporting

### Implementation
```python
long_queue = []   # [qty, price] for LONG positions
short_queue = []  # [qty, price] for SHORT positions

# On close: match against appropriate queue
# On flip: consume queue, open new opposite position
```

### Consequences
- Memory overhead per strategy
- Complex reconciliation logic

---

## ADR-006: Simulation vs Live Mode Switching

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: Need safe environment for strategy testing.

### Decision
Three-tier execution model:
1. `SIMULATION`: Virtual trades, synthetic PnL
2. `PAPER`: IBKR paper account
3. `LIVE`: Production (not fully exposed)

### Rationale
- **Safety**: Mode stored in strategy params, not global state
- **Audit**: Every trade tagged with mode
- **Graduation**: Easy path from sim → paper → live

### Consequences
- Database bloat from simulation trades
- Need periodic cleanup job

---

## ADR-007: LangChain for LLM Orchestration

**Status**: Accepted  
**Date**: 2026-02-16  
**Context**: Multi-agent research swarm requires structured LLM calls.

### Decision
Use LangChain (AzureChatOpenAI) with custom ResearchSwarm wrapper.

### Rationale
| Option | Pros | Cons |
|--------|------|------|
| Raw OpenAI | Simple, no deps | Manual prompt management |
| **LangChain (Chosen)** | Structured output, chaining | Learning curve |
| Local LLM | No API costs | Inferior reasoning |

### Consequences
- Azure dependency
- Token costs scale with usage
- Rate limiting considerations

---

## ADR-008: yfinance as Primary Data Source

**Status**: Accepted with caveats  
**Date**: 2026-02-16  
**Context**: Free market data for retail trading.

### Decision
Use yfinance for EOD and intraday data. Cache aggressively. Fallback to IBKR for real-time.

### Rationale
- **Free**: No data fees
- **Comprehensive**: Stocks, FX, crypto, commodities
- **Limitations**: IP throttling, delayed data, no L2

### Risk Mitigation
- Cache in Gold layer to reduce calls
- 30s scheduler reduces burst patterns
- Monitor for 403 errors

### Consequences
- Data quality dependency on Yahoo
- Throttling risk during high volume

---

## Pending Decisions

| ID | Topic | Options | Blocked By |
|----|-------|---------|------------|
| ADR-009 | Time-series DB | TimescaleDB vs stay on RDS | Performance testing |
| ADR-010 | Message Queue | Redis/RabbitMQ for async | Scale requirements |
| ADR-011 | Frontend State | Redux vs React Query | Frontend refactor |
| ADR-012 | Deployment | Docker vs bare metal | Infra decision |

---

*End of Decisions Document*
