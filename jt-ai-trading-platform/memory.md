# JT AI Trading Platform - Memory Log

---

## 2026-02-16

### Session Summary
Initial codebase ingestion from GitHub repository. Generated core documentation architecture.

### Completed
- [x] Cloned `jt-ai-trading-platform` repository
- [x] Scanned 60+ Python files, 8 frontend files
- [x] Generated `architecture.md` - Full system diagram and component breakdown
- [x] Generated `dependencies.md` - File-level dependency mapping
- [x] Generated `decisions.md` - ADR records for key architectural choices

### Key Findings

#### System Overview
- **Stack**: Python FastAPI + React + AWS RDS PostgreSQL
- **Broker**: Interactive Brokers (dual integration: socket + web)
- **AI**: Azure OpenAI via LangChain
- **Data**: yfinance (primary) + Alternative.me (sentiment)

#### Architecture Strengths
1. **4-tier data architecture**: Bronze → Silver → Gold → Consumption
2. **Multi-asset support**: Stocks, FX, Crypto, Commodities unified pipeline
3. **Execution modes**: SIMULATION → PAPER → LIVE graduation path
4. **FIFO PnL accounting**: Separate long/short queues per strategy

#### Identified Technical Debt
1. **Silent exception handling**: Multiple `try/except: pass` patterns
2. **Price source duality**: yfinance real-time + cached GlobalState inconsistency risk
3. **No test coverage**: Only `test_api.py`, no unit tests for core logic
4. **Scheduler coupling**: Strategy execution tightly coupled to data refresh

#### IBKR Assessment (for Jacky)
| Aspect | FX | Crypto |
|--------|-----|--------|
| Spreads | Competitive | Wide |
| Assets | All majors | 4 only (BTC, ETH, LTC, BCH) |
| Custody | N/A | **No withdrawal** (paper only) |
| Verdict | ✅ Good | ⚠️ Limited |

### File Inventory Created
```
/workspace/jt-ai-trading-platform/
├── architecture.md       # System architecture + data flow
├── dependencies.md       # File-level dependency map
├── decisions.md          # ADR records
└── [existing codebase]
```

### Next Steps (Pending Jacky's Direction)
1. Review ADR-001: Implement multi-broker abstraction for crypto?
2. Address technical debt: Add error handling rigor?
3. Feature development: Specific module enhancement?
4. Testing: Implement core logic unit tests?

---

*End of Memory Log*
