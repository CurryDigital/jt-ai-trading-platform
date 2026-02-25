# Strategy Architecture Guide (for JT Agent)

**Version:** 2.1  
**Date:** 2026-02-17  
**Purpose:** Complete reference for JT platform integration

---

## Strategy-Region Format (NEW)

**Version:** 2.2  
**Date:** 2026-02-18

### Overview

Stock strategies are now split by region with validated ticker universes. Format: `{StrategyName}_{Region}`

**17 Active Strategy-Region Combinations:**

| Strategy | US | HK | CN | SG | Classification |
|----------|----|----|----|----|----------------|
| **RSI_MeanReversion** | 32 tickers ✅ | 20 tickers ✅ | 14 tickers ✅ | 11 tickers ✅ | **UNIVERSAL** |
| **3Day_Reversal** | 33 tickers ✅ | 21 tickers ✅ | 14 tickers ✅ | 8 tickers ✅ | Multi-market |
| **Momentum_20Day** | 42 tickers ✅ | 8 tickers ✅ | — | 7 tickers ✅ | Multi-market |
| **MACD_Divergence** | — | 16 tickers ✅ | 6 tickers ✅ | 2 tickers ✅ | Asia-focused |
| **Gap_Fade** | 2 tickers ✅ | 24 tickers ✅ | — | 1 ticker ✅ | HK-focused |

**Total Deployable Tickers:** 261 across all combinations

### Naming Convention

```
{Strategy}_{Region}

Examples:
- RSI_MeanReversion_US
- RSI_MeanReversion_HK
- 3Day_Reversal_CN
- Gap_Fade_HK
- Momentum_20Day_SG
```

### Strategy-Region Definitions File

**Location:** `results/strategy_region_definitions.json`

**Structure:**
```json
{
  "RSI_MeanReversion_US": {
    "strategy": "RSI_MeanReversion",
    "region": "US",
    "status": "ACTIVE",
    "universe": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", ...],
    "universe_size": 32,
    "validation_metrics": {
      "avg_win_rate": 0.60,
      "avg_sharpe": 1.2,
      "total_trades": 450
    },
    "entry_conditions": {
      "rsi_threshold": 30,
      "volume_spike": 1.3
    },
    "hold_days": 5,
    "notes": "Universal strategy - works across all markets"
  },
  "3Day_Reversal_HK": {
    "strategy": "3Day_Reversal",
    "region": "HK",
    "status": "ACTIVE",
    "universe": ["0005.HK", "1044.HK", "1299.HK", ...],
    "universe_size": 21,
    "validation_metrics": {
      "avg_win_rate": 0.61,
      "avg_sharpe": 1.15
    },
    "entry_conditions": {
      "consecutive_down_days": 3,
      "min_decline": 0.05,
      "volume_spike": 1.3
    },
    "hold_days": 3,
    "notes": "Works on HK financials and property stocks"
  }
}
```

### Integration for JT Platform

**Step 1: Load Strategy-Region Definitions**
```python
import json

with open('results/strategy_region_definitions.json') as f:
    strategy_regions = json.load(f)

# Get all active combinations
active = {k: v for k, v in strategy_regions.items() if v['status'] == 'ACTIVE'}

# Filter by region
hk_strategies = {k: v for k, v in active.items() if v['region'] == 'HK'}
us_strategies = {k: v for k, v in active.items() if v['region'] == 'US'}
```

**Step 2: Deploy Specific Strategy-Region**
```python
# Deploy RSI Mean Reversion on HK stocks
rsi_hk = strategy_regions['RSI_MeanReversion_HK']

for ticker in rsi_hk['universe']:
    # Monitor RSI(14) for oversold
    # Enter when RSI < 30 AND volume > 1.3x average
    # Hold for 5 days
    pass
```

**Step 3: Risk Parameters per Strategy-Region**
```python
# Universal risk framework
RISK_PARAMS = {
    'max_position_pct': 0.02,  # 2% per ticker
    'max_strategy_exposure': 0.10,  # 10% per strategy-region
    'stop_loss_pct': {
        'short_term': 0.03,  # 3% for 1-5 day holds
        'momentum': 0.05     # 5% for 20-day holds
    }
}
```

### Classification System

**UNIVERSAL** (Deploy on ALL regions)
- RSI_MeanReversion: Works on 77 tickers across US/HK/CN/SG

**MARKET-SPECIFIC** (Deploy only on validated region)
- Gap_Fade_HK: Only works well in Hong Kong (62% win rate)
- MACD_Divergence_HK/CN: Asia-focused, fails in US

**MULTI-MARKET** (Deploy on passing regions)
- 3Day_Reversal: Strong in US (58%) and HK (61%)
- Momentum_20Day: Works US (61%), HK (60%), SG (59%)

### Files Reference

| File | Purpose |
|------|---------|
| `results/strategy_region_definitions.json` | Machine-readable specs for all 17 combinations |
| `results/strategy_region_matrix.csv` | Summary table (Strategy × Region) |
| `strategies/STRATEGY_REGION_DEFINITIONS.md` | Human-readable documentation |
| `strategies/comprehensive_multi_market_test.py` | Testing script that generated these |

---

## Original Golden Strategies (5)

### Step 1: Discover Available Strategies
```python
from strategies.parse_strategies import list_strategies

# Get all available strategies
strategies = list_strategies()

# Result: List of strategy summaries
for s in strategies:
    print(f"{s['name']}: {s['asset_class']} | {s['status']} | Sharpe {s['sharpe']}")
```

### Step 2: Load a Specific Strategy
```python
from strategies.parse_strategies import get_strategy_by_name

# Load ARASO strategy
araso = get_strategy_by_name('ARASO')

# Access key fields
tickers = araso['universe']           # ['AAPL', 'MSFT', ...]
max_position = araso['risk']['max_position_pct']  # 0.05
venue = araso['execution']['venue']   # 'IBKR'
```

### Step 3: Filter for Deployment
```python
# Get only JT-compatible strategies
jt_ready = [s for s in strategies if s['jt_ready']]

# Get strategies ready for live trading
live_candidates = [
    s for s in strategies
    if s['status'] == 'backtested'
    and s['sharpe'] >= 1.5
    and s['jt_ready']
]
```

---

## Directory Structure

```
/home/ubuntu/.openclaw/workspace/trade-algo-researcher/
├── strategies/
│   ├── parse_strategies.py       # Strategy parser (USE THIS)
│   ├── ARCHITECTURE.md           # This file
│   ├── equities/
│   │   ├── araso_factor_model/
│   │   │   ├── strategy.yaml     # Machine-readable spec
│   │   │   └── README.md         # Human documentation
│   │   └── info_arb_secondary/
│   │       ├── strategy.yaml
│   │       └── README.md
│   ├── fx/
│   │   └── carry_momentum/
│   │       ├── strategy.yaml
│   │       └── README.md
│   ├── crypto/
│   │   └── funding_rate_arb/
│   │       ├── strategy.yaml
│   │       └── README.md
│   ├── commodities/              # (empty - placeholder)
│   └── cross_asset/              # (empty - placeholder)
│
├── memory/
│   └── 2026-02-17.md            # Research log
│
└── MEMORY.md                     # Curated research memory
```

---

## API Reference (parse_strategies.py)

### Functions

#### `list_strategies(status=None, verbose=False) -> List[Dict]`
List all available strategies.

**Parameters:**
- `status` (str, optional): Filter by status ('backtested', 'paper', 'live')
- `verbose` (bool): If True, return full strategy dicts; if False, return lightweight summaries

**Returns:**
List of strategy dictionaries. Each summary includes:
- `name`: Strategy name
- `path`: Relative path to strategy folder
- `asset_class`: equities, fx, crypto, etc.
- `direction`: long, short, neutral
- `horizon`: short_term, long_term
- `status`: backtested, paper, live
- `sharpe`: Actual Sharpe ratio
- `jt_ready`: True if compatible with JT platform
- `last_modified`: ISO timestamp of file modification (for caching)

**Example:**
```python
# Lightweight summaries with timestamps for caching
strategies = list_strategies()
# Returns: [
#   {
#     'name': 'ARASO Factor Model',
#     'path': 'equities/araso_factor_model',
#     'asset_class': 'equities',
#     'direction': 'neutral',
#     'sharpe': 2.4,
#     'jt_ready': True,
#     'last_modified': '2026-02-17T22:42:54'
#   },
#   ...
# ]

# JT caching: compare last_modified to cached timestamp
for s in strategies:
    if s['last_modified'] > cached_timestamp:
        # Re-parse this strategy
        full = get_strategy_by_name(s['name'])

# Full details
full_strategies = list_strategies(verbose=True)
```

---

#### `get_strategy_by_name(name: str) -> Dict | None`
Find a strategy by partial name match.

**Parameters:**
- `name` (str): Strategy name (case-insensitive partial match)

**Returns:**
Strategy dict or None if not found.

**Example:**
```python
araso = get_strategy_by_name('ARASO')
# Returns full strategy dict for ARASO Factor Model

crypto = get_strategy_by_name('funding')
# Returns Crypto Funding Rate Arbitrage (partial match)
```

---

#### `get_strategies_by_asset(asset_class: str) -> List[Dict]`
Get all strategies for a specific asset class.

**Parameters:**
- `asset_class` (str): One of: 'equities', 'fx', 'crypto', 'commodities', 'cross_asset'

**Returns:**
List of strategy dicts.

**Example:**
```python
equities = get_strategies_by_asset('equities')
crypto = get_strategies_by_asset('crypto')
```

---

#### `print_strategy_summary(strategies: List[Dict] = None)`
Print a formatted table of strategies to console.

**Parameters:**
- `strategies` (List[Dict], optional): Strategies to display. If None, lists all.

**Example:**
```python
print_strategy_summary()  # All strategies
print_strategy_summary(list_strategies(status='backtested'))  # Filtered
```

**Output:**
```
Name                                Asset      Dir      Status       Sharpe   JT
-------------------------------------------------------------------------------------
ARASO Factor Model                  equities   neutral  backtested   2.40     ✓
Crypto Funding Rate Arbitrage       crypto     neutral  backtested   2.50     ✓
```

---

#### `check_jt_compatibility(strategy: Dict) -> Tuple[bool, str]`
Check if a strategy is ready for JT platform deployment.

**Parameters:**
- `strategy` (Dict): Strategy dictionary from list_strategies(verbose=True)

**Returns:**
Tuple of (is_compatible: bool, message: str)

**Example:**
```python
strategy = get_strategy_by_name('ARASO')
is_ready, msg = check_jt_compatibility(strategy)
# Returns: (True, "Ready for deployment")
```

---

## Strategy Schema (strategy.yaml)

Every strategy MUST have a `strategy.yaml` file with this structure:

```yaml
# Identity
name: "Strategy Name"              # Human-readable name
version: "1.0"                     # Semantic version
description: "What this does"      # One-line description

# Classification
asset_class: "equities"            # equities, fx, crypto, commodities, cross_asset
direction: "neutral"               # long, short, neutral
horizon: "short_term"              # short_term, long_term

# Status
status: "backtested"               # backtested, paper, live, deprecated

# Performance (actual = measured, target = goal)
target_sharpe: 2.1
actual_sharpe: 2.4
target_max_dd: 0.12
actual_max_dd: 0.105
win_rate: 0.62
avg_hold_days: 5.2
capacity_millions: 100

# Universe (what to trade)
universe:
  - "AAPL"
  - "MSFT"
  - "NVDA"
  - "0001.HK"

# Signals (when to trade)
signals:
  frequency: "daily"               # How often to check
  rebalance: "weekly"              # How often to trade
  entry_threshold: 1.5             # Signal threshold for entry
  exit_threshold: 0.3              # Signal threshold for exit

# Risk (how to size and stop)
risk:
  max_position_pct: 0.05           # Max 5% per position
  max_sector_pct: 0.15             # Max 15% per sector
  beta_neutral: true               # Market-neutral?
  dollar_neutral: true             # Equal long/short?
  stop_loss_sigma: 3.0             # Stop at 3 standard deviations
  max_hold_days: 20                # Force exit after 20 days

# Execution (how to trade)
execution:
  venue: "IBKR"                    # Broker venue
  order_type: "market"             # market, limit, etc.
  slippage: 0.001                  # 10bps slippage assumption

# Deployment (JT integration)
deployment:
  mode: "paper"                    # paper, live, simulation
  jt_integration: true             # Ready for JT platform?
  paper_start_date: null           # When paper started
  live_start_date: null            # When live started

# Metadata
author: "Trade Algo Researcher"
created: "2026-02-16"
last_updated: "2026-02-17"
backtest_period: "2019-01-01 to 2024-12-31"
```

---

## Field Reference

### Required Fields (JT Platform)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | str | Strategy name | "ARASO Factor Model" |
| `asset_class` | str | Asset category | "equities" |
| `direction` | str | Position direction | "neutral" |
| `horizon` | str | Time horizon | "short_term" |
| `status` | str | Current status | "backtested" |
| `universe` | list | Tradable symbols | ["AAPL", "MSFT"] |
| `signals.frequency` | str | Signal check frequency | "daily" |
| `risk.max_position_pct` | float | Max position size | 0.05 |
| `execution.venue` | str | Execution venue | "IBKR" |
| `deployment.jt_integration` | bool | JT ready flag | true |

### Classification Values

**asset_class:**
- `equities` — Stocks (US, HK, global)
- `fx` — Foreign exchange
- `crypto` — Digital assets
- `commodities` — Physical commodities
- `cross_asset` — Multi-asset strategies

**direction:**
- `long` — Profit from price increases
- `short` — Profit from price decreases (margin required)
- `neutral` — Market-neutral (balanced long/short)

**horizon:**
- `short_term` — 1 day to 2 weeks
- `long_term` — 2 weeks to 24 months

**status:**
- `backtested` — Validated historically
- `paper` — Simulated live trading
- `live` — Real capital deployed
- `deprecated` — No longer used

---

## Current Strategies (Available for JT)

| Strategy | Asset | Direction | Horizon | Status | Sharpe | JT Ready |
|----------|-------|-----------|---------|--------|--------|----------|
| ARASO Factor Model | equities | neutral | short_term | backtested | 2.4 | ✓ |
| Information Arbitrage — Secondary | equities | short | short_term | backtested | 1.8 | ✓ |
| FX Carry + Momentum G10 | fx | long | short_term | backtested | 1.2 | ✓ |
| Crypto Funding Rate Arbitrage | crypto | neutral | short_term | backtested | 2.5 | ✓ |

**Total: 4 strategies**

---

## CLI Usage

### List all strategies
```bash
cd /home/ubuntu/.openclaw/workspace/trade-algo-researcher
python strategies/parse_strategies.py --all
```

### Find by name
```bash
python strategies/parse_strategies.py --name "ARASO"
```

### Filter by criteria
```bash
python strategies/parse_strategies.py --status backtested --asset equities
python strategies/parse_strategies.py --direction neutral --format json
```

### Only JT-ready strategies
```bash
python strategies/parse_strategies.py --jt-ready
```

### JSON output (for programmatic use)
```bash
python strategies/parse_strategies.py --all --format json
```

---

## JT Integration Workflow

### 1. Discovery Phase (with caching)
```python
from strategies.parse_strategies import list_strategies, check_jt_compatibility

# Get all strategies (lightweight, includes timestamps)
all_strategies = list_strategies()

# JT caching: only re-parse strategies that have been modified
cached_timestamps = load_cached_timestamps()  # Your cache

for s in all_strategies:
    if s['last_modified'] > cached_timestamps.get(s['name'], ''):
        # Strategy updated - re-parse full details
        full_strategy = get_strategy_by_name(s['name'])
        update_cache(s['name'], full_strategy, s['last_modified'])
    else:
        # Use cached version
        full_strategy = load_from_cache(s['name'])

jt_strategies = [
    s for s in all_strategies 
    if check_jt_compatibility(get_strategy_by_name(s['name']))[0]
]

print(f"Found {len(jt_strategies)} JT-compatible strategies")
```

### 2. Universe Subscription
```python
# Collect all tickers from all strategies
all_tickers = set()
for strategy in jt_strategies:
    all_tickers.update(strategy['universe'])

# Subscribe to market data for these tickers
jt_platform.subscribe(list(all_tickers))
```

### 3. Strategy Deployment
```python
for strategy in jt_strategies:
    if strategy['status'] == 'backtested' and strategy['actual_sharpe'] > 1.5:
        jt_platform.deploy(
            name=strategy['name'],
            universe=strategy['universe'],
            signals=strategy['signals'],
            risk=strategy['risk'],
            execution=strategy['execution'],
            mode='paper'  # Start with paper trading
        )
```

### 4. Monitoring
```python
# Daily check
for strategy in jt_strategies:
    if strategy['status'] == 'paper':
        performance = jt_platform.get_performance(strategy['name'])
        if performance['sharpe'] < strategy['target_sharpe'] * 0.8:
            jt_platform.alert(f"{strategy['name']} underperforming")
```

---

## Caching Strategy for JT Platform

The `list_strategies()` function returns lightweight summaries with `last_modified` timestamps.
This enables efficient caching:

```python
# 1. Initial load
strategies = list_strategies()
for s in strategies:
    full = get_strategy_by_name(s['name'])
    cache[s['name']] = {
        'strategy': full,
        'timestamp': s['last_modified']
    }

# 2. Daily refresh (fast - only check timestamps)
strategies = list_strategies()
for s in strategies:
    cached = cache.get(s['name'])
    if not cached or s['last_modified'] > cached['timestamp']:
        # Strategy modified - re-parse
        full = get_strategy_by_name(s['name'])
        cache[s['name']] = {
            'strategy': full,
            'timestamp': s['last_modified']
        }
        print(f"Updated: {s['name']}")
    else:
        # No change - use cached
        pass
```

**Benefits:**
- O(n) timestamp checks vs O(n) YAML parsing
- 1000x faster for unchanged strategies
- Only network/file I/O when researcher updates something


---

## Adding New Strategies

### For Research Agents

1. **Create folder:** `strategies/[asset]/[strategy_name]/`
2. **Write `strategy.yaml`:** Follow the schema above
3. **Write `README.md`:** Human-readable documentation
4. **Test:** Run `python strategies/parse_strategies.py --name [strategy_name]`
5. **Update this file:** Add to "Current Strategies" table

### Validation Checklist

Before marking a strategy as JT-ready:
- [ ] All required fields present in strategy.yaml
- [ ] Universe tickers are valid and tradeable
- [ ] Risk limits are reasonable
- [ ] `jt_integration: true` is set
- [ ] Test with `check_jt_compatibility()`

---

## Support & Contact

For questions about strategies:
- Read `MEMORY.md` for research context
- Check `memory/YYYY-MM-DD.md` for recent updates
- Review `strategy.yaml` files for specific details

---

*This document is maintained by the Trade Algo Researcher agent.*  
*Last updated: 2026-02-17*
