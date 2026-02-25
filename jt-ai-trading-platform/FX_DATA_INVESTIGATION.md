# FX Data Source Investigation Report

**Date**: 2026-02-16  
**Scope**: Real-time FX data sources for frequency >1-minute  
**Account Type**: Dedicated FX account (100% exposure)  
**Pairs**: Majors only (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF)

---

## Data Source Options

### 1. Interactive Brokers (IBKR) - RECOMMENDED ⭐

**Frequency**: Tick-by-tick (every price change)  
**Latency**: ~50-200ms  
**Cost**: FREE (with account)  
**API**: ib_insync `reqMktData()`

**Pros**:
- ✅ FREE with IBKR account
- ✅ Tick-by-tick (no aggregation)
- ✅ Direct execution path (same data = execution)
- ✅ No rate limits
- ✅ Already integrated in codebase
- ✅ Historical tick data available

**Cons**:
- ❌ Requires IB Gateway/TWS running
- ❌ Paper trading has delayed data (15 min) unless subscribed
- ❌ Live account needs market data subscription (~$10-20/month for FX)

**Implementation**:
```python
from ib_insync import IB, Forex
ib = IB()
contract = Forex('EURUSD')
ib.reqMktData(contract, '', False, False)
# Callback: ticker.updateEvent
```

**Verdict**: **PRIMARY SOURCE** - Best for automated trading

---

### 2. Alpha Vantage

**Frequency**: 1-minute (free tier), tick (paid - $600+/month)  
**Latency**: ~1-5 seconds  
**Cost**: FREE (5 calls/min, 500/day), Paid tiers available  
**API**: REST API

**Pros**:
- ✅ Free tier available
- ✅ No socket connection needed
- ✅ Historical data available

**Cons**:
- ❌ Free tier: 1-minute only, 5 calls/min rate limit
- ❌ Real-time tick data: $600+/month (expensive)
- ❌ REST API = polling overhead
- ❌ Different data source than execution venue (IBKR)

**Implementation**:
```python
import requests
url = "https://www.alphavantage.co/query"
params = {
    "function": "FX_INTRADAY",
    "from_symbol": "EUR",
    "to_symbol": "USD",
    "interval": "1min",
    "apikey": "YOUR_API_KEY"
}
```

**Verdict**: **BACKUP ONLY** - Too slow/expensive for primary

---

### 3. Polygon.io

**Frequency**: Real-time WebSocket  
**Latency**: ~10-50ms  
**Cost**: $49/month (real-time FX)  
**API**: WebSocket + REST

**Pros**:
- ✅ Real-time WebSocket
- ✅ Low latency
- ✅ Good for stocks + FX combo

**Cons**:
- ❌ $49/month cost
- ❌ Separate from execution (IBKR)
- ❌ Need to reconcile prices between data and execution

**Verdict**: **OPTIONAL ENHANCEMENT** - Good for redundancy, not primary

---

### 4. OANDA (via v20 API)

**Frequency**: Tick-by-tick  
**Latency**: ~100-300ms  
**Cost**: FREE with OANDA account  
**API**: REST + Streaming

**Pros**:
- ✅ FREE with account
- ✅ Tick-by-tick
- ✅ Good FX specialist
- ✅ Can execute on OANDA if IBKR fails

**Cons**:
- ❌ Requires OANDA account
- ❌ Different venue from IBKR
- ❌ Need multi-broker logic

**Verdict**: **BACKUP BROKER** - Good for redundancy

---

### 5. TrueFX / Integral

**Frequency**: Tick-by-tick  
**Latency**: ~50-100ms  
**Cost**: FREE (non-commercial), $$$ (commercial)  
**API**: FIX or proprietary

**Pros**:
- ✅ Institutional-grade
- ✅ Interbank pricing

**Cons**:
- ❌ Complex FIX protocol
- ❌ Licensing for automated trading
- ❌ Overkill for this setup

**Verdict**: **NOT RECOMMENDED** - Too complex

---

## Data Source Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRIMARY: IBKR (Tick)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  - Real-time bid/ask from IB Gateway                      │  │
│  │  - Tick-by-tick updates (every price change)              │  │
│  │  - Direct execution path (no slippage from data lag)      │  │
│  │  - Free with market data subscription (~$15/month)        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
┌───────────────────▼─────────┐  ┌──────▼──────────────────┐
│   BACKUP: OANDA (Tick)      │  │   FALLBACK: yfinance    │
│  ┌────────────────────────┐ │  │  ┌────────────────────┐ │
│  │ - If IBKR disconnects  │ │  │  │ - 1-minute bars    │ │
│  │ - Tick data            │ │  │  │ - Free, no account │ │
│  │ - Multi-broker hedge   │ │  │  │ - Last resort only │ │
│  └────────────────────────┘ │  │  └────────────────────┘ │
└─────────────────────────────┘  └─────────────────────────┘
```

---

## Phase 1.1 Implementation Plan

### Task Breakdown

| # | Task | Output | Time |
|---|------|--------|------|
| 1.1.1 | IBKR FX streaming service | `fx_streaming_service.py` | 2h |
| 1.1.2 | Tick aggregation (1s, 5s, 1m bars) | `fx_bar_aggregator.py` | 2h |
| 1.1.3 | WebSocket broadcast | WS endpoint `/ws/fx` | 2h |
| 1.1.4 | Frontend FX live grid | React component update | 2h |
| 1.1.5 | Spread monitor & alerts | Alert on spread > X pips | 1h |
| **Total** | | | **9h** |

---

## Major Currency Pairs (Majors)

| Pair | IBKR Symbol | Typical Spread | Priority |
|------|-------------|----------------|----------|
| EURUSD | EUR.USD | 0.1-0.3 pips | 🔴 Critical |
| USDJPY | USD.JPY | 0.1-0.3 pips | 🔴 Critical |
| GBPUSD | GBP.USD | 0.3-0.5 pips | 🔴 Critical |
| AUDUSD | AUD.USD | 0.3-0.6 pips | 🟡 High |
| USDCAD | USD.CAD | 0.3-0.6 pips | 🟡 High |
| USDCHF | USD.CHF | 0.3-0.6 pips | 🟡 High |

**Phase 1.1 Scope**: Start with EURUSD, USDJPY, GBPUSD (top 3)  
**Phase 1.2**: Add AUDUSD, USDCAD, USDCHF

---

## Decision Required

**Jacky, confirm to proceed with Phase 1.1 using IBKR as primary source:**

| Decision | My Recommendation | Status |
|----------|-------------------|--------|
| **Primary Data Source** | IBKR (tick-by-tick) | ⏳ Awaiting confirmation |
| **Backup Source** | yfinance 1-min (for now) | ⏳ Awaiting confirmation |
| **Initial Pairs** | EURUSD, USDJPY, GBPUSD | ⏳ Awaiting confirmation |
| **Target Frequency** | Tick (every price change) → 1s bars | ⏳ Awaiting confirmation |
| **IBKR Market Data** | Need FX subscription (~$15/month) | ⏳ Awaiting confirmation |

**Note on IBKR Market Data**:  
For live (non-delayed) FX data, you need:
- IBKR Pro account (you have this)
- FX market data subscription (~$15/month)
- Without subscription: 15-minute delayed data (unsuitable for automated trading)

**Alternative if no IBKR subscription**: Use OANDA as primary (free real-time)

**Ready to implement once confirmed.**
