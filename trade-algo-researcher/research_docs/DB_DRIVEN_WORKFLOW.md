# Database-Driven Backtesting Workflow

**Date:** 2026-02-20  
**Status:** ✅ Implemented and Tested

---

## 🎯 OVERVIEW

Shifted from file-based to **database-centric** workflow using:
- **silver schema:** Raw OHLCV data for backtesting
- **gold schema:** Pre-calculated signals (RSI, MACD, metrics)
- **consumption schema:** JT platform output
- **openclaw_researcher schema:** My backtest storage and analysis

---

## 📁 NEW FILES CREATED

| File | Purpose |
|------|---------|
| `db_backtest_engine.py` | Python engine for DB-driven backtesting |
| `run_db_backtests.py` | CLI tool to run backtests |
| `db_views_and_functions.sql` | SQL views and helper functions |

---

## 🔌 CONNECTION METHOD

```python
from db_backtest_engine import TradeAlgoDB

db = TradeAlgoDB()
db.connect()  # IAM auth via EC2 instance profile

# Now connected to aitrading database with:
# - READ access to silver, gold, consumption
# - FULL access to openclaw_researcher
```

---

## 📊 DATA RETRIEVAL CLASSES

### 1. Silver Schema (Raw Data)

```python
from db_backtest_engine import DataRetrieval

data = DataRetrieval(db)

# Get OHLCV for backtesting
prices = data.get_ohlcv(
    tickers=['AAPL', 'MSFT', 'NVDA'],
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# Get historical news
news = data.get_historical_news(
    tickers=['AAPL'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### 2. Gold Schema (Signals)

```python
# Get technical indicators (KEY for RSI strategy)
metrics = data.get_stock_metrics(
    tickers=['AAPL', '0700.HK'],
    date='2026-02-20'  # None for latest
)

# Get RSI signals (RSI < 30 + volume confirmation)
rsi_signals = data.get_rsi_signals(
    rsi_threshold=30,
    volume_threshold=1.3
)

# Get FX data for AH Premium
fx = data.get_fx_metrics(
    pairs=['USDJPY=X', 'USDCNH=X']
)

# Get commodity data for Gold/Silver
commodities = data.get_commodity_metrics(
    tickers=['GC=F', 'SI=F']
)

# Get earnings data for PEAD
earnings = data.get_earnings_data(
    tickers=['AAPL', 'MSFT'],
    min_surprise=0.05
)

# Get SUE scores
sue = data.get_sue_scores(min_sue=2.0)

# Get market regimes (HMM)
regimes = data.get_market_regimes(lookback_days=30)
```

### 3. Consumption Schema (JT Output)

```python
# Get JT AI Trading recommendations
jt_signals = data.get_jt_stock_signals(
    market='HK',
    min_confidence=70,
    min_score=60
)

# Get executed trades
trades = data.get_jt_trades(
    start_date='2026-02-01'
)
```

---

## 🧪 BACKTEST ENGINE

### Run RSI Mean Reversion Backtest

```python
from db_backtest_engine import BacktestEngine

engine = BacktestEngine(db)

results = engine.run_rsi_backtest(
    tickers=['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN'],
    start_date='2020-01-01',
    end_date='2024-12-31',
    rsi_entry=30,
    rsi_exit=50,
    volume_threshold=1.3,
    max_hold_days=5
)

print(f"Sharpe: {results['sharpe']:.2f}")
print(f"Win Rate: {results['win_rate']:.1f}%")
print(f"Total Trades: {results['total_trades']}")
```

### Run Momentum Backtest

```python
results = engine.run_momentum_backtest(
    tickers=['AAPL', 'MSFT', 'NVDA'],
    start_date='2020-01-01',
    end_date='2024-12-31',
    lookback_days=20,
    hold_days=20
)
```

### Run PEAD Backtest

```python
results = engine.run_pead_backtest(
    tickers=['AAPL', 'MSFT', 'NVDA'],
    start_date='2023-01-01',
    end_date='2024-12-31',
    min_surprise=0.05,
    hold_days=5
)
```

---

## 💾 STORE RESULTS

```python
from db_backtest_engine import BacktestStorage

storage = BacktestStorage(db)

# Save backtest summary
backtest_id = storage.save_backtest_result(
    hypothesis_name='Accruals Quality',
    start_date='2020-01-01',
    end_date='2024-12-31',
    results=results,
    parameters={'rsi_entry': 30, 'volume_threshold': 1.3}
)

# Save individual trades
storage.save_trades(backtest_id, results['trades'])

# Update hypothesis status
storage.update_hypothesis_status(
    hypothesis_name='Accruals Quality',
    sharpe=results['sharpe'],
    status='validated' if results['sharpe'] > 1.0 else 'testing'
)
```

---

## 📈 SQL VIEWS (Pre-built Queries)

### 1. Backtest Rankings
```sql
SELECT * FROM openclaw_researcher.v_backtest_rankings;
```
Shows best Sharpe, win rate, total backtests per hypothesis.

### 2. Promotion Candidates
```sql
SELECT * FROM openclaw_researcher.v_promotion_candidates;
```
Shows hypotheses with Sharpe > 1.0 ready for promotion.

### 3. RSI Signals Today
```sql
SELECT * FROM openclaw_researcher.v_rsi_signals_today 
WHERE signal IN ('STRONG_BUY', 'BUY');
```
Live RSI oversold signals with volume confirmation.

### 4. Momentum Ranking
```sql
SELECT * FROM openclaw_researcher.v_momentum_ranking 
WHERE trend_regime = 'STRONG_UPTREND';
```
Stocks in strong uptrend (above 50d and 200d MA).

### 5. Gold/Silver Status
```sql
SELECT * FROM openclaw_researcher.v_gold_silver_status;
```
Current prices, ratio, and RSI for Gold/Silver strategy.

---

## 🚀 CLI USAGE

```bash
# Run single backtest
python3 run_db_backtests.py --mode accruals

# Run PEAD backtest
python3 run_db_backtests.py --mode pead

# Run momentum backtest
python3 run_db_backtests.py --mode momentum

# Get live signals
python3 run_db_backtests.py --mode live

# Run all Tier 1 backtests
python3 run_db_backtests.py --mode batch

# Run everything
python3 run_db_backtests.py --mode all
```

---

## 📋 WORKFLOW EXAMPLE

### Backtesting a New Hypothesis

```python
# 1. Get data from gold schema
metrics = data.get_stock_metrics(universe, start_date)

# 2. Run backtest using gold data (pre-calculated RSI, etc.)
results = engine.run_rsi_backtest(universe, start_date, end_date)

# 3. Store results in openclaw_researcher
backtest_id = storage.save_backtest_result(...)

# 4. Update hypothesis registry
storage.update_hypothesis_status(...)

# 5. Check rankings
rankings = db.query("SELECT * FROM openclaw_researcher.v_backtest_rankings")
```

---

## 🎯 BENEFITS OF DB-DRIVEN WORKFLOW

| Before (File-based) | After (DB-driven) |
|---------------------|-------------------|
| Download CSV files | Query live data |
| Manual RSI calculation | Use gold.stock_metrics.rsi_14 |
| Stale data | Real-time gold schema |
| Local storage | Cloud persistence |
| Single user | Multi-agent access |
| Manual tracking | Automated registry |

---

## 📊 LIVE DATA ACCESS

### Current Data Available (as of 2026-02-20)

```
Gold/Silver:
  Gold: $5,017.90 (RSI 56.1)
  Silver: $78.15 (RSI 46.9)
  Ratio: 64.20

Hypotheses in Testing:
  PEAD NLP Enhanced: Target Sharpe 1.45
  Accruals Quality: Target Sharpe 1.35
  CMV Multi-Factor: Target Sharpe 1.35
  ...13 total in testing
```

---

## 🔧 NEXT STEPS

1. **Run Tier 1 Backtests** using `run_db_backtests.py --mode batch`
2. **Query live signals** for HK Open analysis
3. **Validate hypotheses** and promote to Golden Strategies
4. **Create more SQL views** for specific strategies

---

**Files:**
- `db_backtest_engine.py` - Core engine
- `run_db_backtests.py` - CLI runner
- `db_views_and_functions.sql` - SQL helpers
- `research_docs/DB_SCHEMA_DOCUMENTATION.md` - Schema reference

**Status:** ✅ Database-driven workflow fully operational
