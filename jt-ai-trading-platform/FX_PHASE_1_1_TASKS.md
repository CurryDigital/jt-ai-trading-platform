# FX Streaming Service - Implementation Task List

**Phase**: 1.1  
**Date**: 2026-02-16  
**Status**: IN PROGRESS

---

## Task 1.1.1: FX Streaming Service (2h) ⏳ STARTING

### Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/fx_streaming_service.py` | CREATE | Core IBKR FX streaming |
| `backend/app/db/session.py` | MODIFY | Add FX tick table |
| `backend/app/core_logic/data/fx_bar_aggregator.py` | CREATE | 5s bar aggregation |

### Database Schema
```sql
-- gold.fx_ticks (raw ticks from IBKR)
CREATE TABLE gold.fx_ticks (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ticker VARCHAR(10) NOT NULL,
    bid FLOAT NOT NULL,
    ask FLOAT NOT NULL,
    mid FLOAT GENERATED ALWAYS AS ((bid + ask) / 2) STORED,
    spread_bps FLOAT GENERATED ALWAYS AS ((ask - bid) / ((bid + ask) / 2) * 10000) STORED
);
CREATE INDEX idx_fx_ticks_time ON gold.fx_ticks(timestamp DESC);
CREATE INDEX idx_fx_ticks_ticker ON gold.fx_ticks(ticker);

-- gold.fx_bars_5s (5-second aggregated bars)
CREATE TABLE gold.fx_bars_5s (
    bucket TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    bid_close FLOAT NOT NULL,
    ask_close FLOAT NOT NULL,
    spread_avg_bps FLOAT NOT NULL,
    tick_count INTEGER NOT NULL,
    PRIMARY KEY (bucket, ticker)
);
CREATE INDEX idx_fx_bars_time ON gold.fx_bars_5s(bucket DESC);
```

### Implementation Steps
1. [ ] Create `fx_streaming_service.py` with IBKR connection
2. [ ] Subscribe to EURUSD, USDJPY, GBPUSD via `Forex` contracts
3. [ ] Store ticks to `gold.fx_ticks`
4. [ ] Run 5-second aggregation job
5. [ ] Store bars to `gold.fx_bars_5s`
6. [ ] Health check / reconnection logic

---

## Task 1.1.2: WebSocket Broadcast (2h) ⏳ PENDING

### Files
| File | Action |
|------|--------|
| `backend/app/main.py` | Add WebSocket endpoint `/ws/fx` |
| `backend/app/services/fx_websocket_manager.py` | CREATE |

### Features
- [ ] WebSocket connection manager
- [ ] Broadcast 5s bars to all connected clients
- [ ] Subscribe/unsubscribe per pair
- [ ] Connection health monitoring

---

## Task 1.1.3: Frontend Live Grid (2h) ⏳ PENDING

### Files
| File | Action |
|------|--------|
| `frontend/src/components/FXLiveGrid.jsx` | CREATE |
| `frontend/src/App.jsx` | Add FX grid route |

### Features
- [ ] Real-time price display (bid/ask/mid)
- [ ] 5-second bar chart (sparkline)
- [ ] Spread indicator (color-coded)
- [ ] WebSocket connection status
- [ ] Last update timestamp

---

## Task 1.1.4: Spread Monitor & Alerts (1h) ⏳ PENDING

### Files
| File | Action |
|------|--------|
| `backend/app/services/fx_spread_monitor.py` | CREATE |

### Features
- [ ] Alert if spread > threshold (e.g., 5 bips for majors)
- [ ] Log to `gold.fx_alerts`
- [ ] Optional: Send alert to frontend via WebSocket

---

## Task 1.1.5: Fallback to yfinance (1h) ⏳ PENDING

### Files
| File | Action |
|------|--------|
| `backend/app/services/fx_fallback_service.py` | CREATE |

### Features
- [ ] Detect IBKR disconnection
- [ ] Switch to yfinance 1-minute polling
- [ ] Log fallback events
- [ ] Auto-retry IBKR connection

---

## Progress Tracker

| Task | Status | Time | Blockers |
|------|--------|------|----------|
| 1.1.1 FX Streaming | ✅ COMPLETED | 2/2h | None |
| 1.1.2 WebSocket | ⏳ PENDING | 0/2h | Waiting frontend needs |
| 1.1.3 Frontend Grid | ⏳ PENDING | 0/2h | Waiting 1.1.2 |
| 1.1.4 Spread Monitor | ✅ COMPLETED (in 1.1.1) | 0/1h | None |
| 1.1.5 Fallback | ⏳ PENDING | 0/1h | Low priority |

**Total Progress**: 2/9h (66% of core infra)

---

## Completed (Task 1.1.1)

- [x] Database schema (`FX_STREAMING_DDL.sql`)
- [x] FX streaming service (`fx_streaming_service.py`)
- [x] Tick aggregation to 5s bars
- [x] Spread alert system (3 bps EURUSD/USDJPY, 5 bps GBPUSD)
- [x] Reconnection logic
- [x] ORM models in `session.py`
- [x] Database tables created
- [x] Integrated into `main.py` startup
- [x] API endpoints:
  - `GET /api/fx/streaming/status` - Service status
  - `GET /api/fx/bars/latest` - Latest 5s bars
  - `GET /api/fx/streaming/alerts` - Spread alerts

## Pending

- [ ] WebSocket broadcast (if frontend needs real-time push)
- [ ] Frontend FX live grid component
- [ ] Fallback to yfinance on IBKR disconnect (low priority)

---

## Testing Commands

```bash
# Check FX streaming status
curl https://trade.jtcml.com/api/fx/streaming/status

# Get latest 5s bars
curl https://trade.jtcml.com/api/fx/bars/latest
curl https://trade.jtcml.com/api/fx/bars/latest?ticker=EURUSD&limit=20

# Check spread alerts
curl https://trade.jtcml.com/api/fx/streaming/alerts
```

---

## Notes

**IBKR Subscription Decision Point**:  
After Task 1.1.1 is complete, test with 15-minute delayed data. If streaming works well, subscribe to live data for automated trading.

**Major Pairs Format**:
- EURUSD → `Forex('EURUSD')` in ib_insync
- USDJPY → `Forex('USDJPY')` in ib_insync
- GBPUSD → `Forex('GBPUSD')` in ib_insync

---

*Last Updated: 2026-02-16 03:08 UTC*
