# Database Access Documentation - Trade Algo Researcher

**Date:** 2026-02-20  
**Database:** aitrading (PostgreSQL 17.6)  
**Host:** openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com  
**User:** openclaw_user (IAM authenticated via EC2 instance profile)  
**Access Level:** READ-ONLY on silver, gold, consumption schemas; FULL on openclaw_researcher

---

## Connection Method

```python
import boto3
import subprocess
import os

def get_token():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    return rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    )

def query(sql):
    env = os.environ.copy()
    env['PGPASSWORD'] = get_token()
    result = subprocess.run([
        'psql', '-h', 'openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        '-U', 'openclaw_user', '-d', 'aitrading',
        '-c', sql
    ], capture_output=True, text=True, env=env)
    return result.stdout, result.stderr
```

---

## SCHEMA: SILVER (Raw/Cleaned Data) - READ ONLY

### Tables

#### 1. historical_stock_data
**Purpose:** OHLCV price data for backtesting

| Column | Type | Description |
|--------|------|-------------|
| date | timestamp | Trading date |
| id | integer | Primary key |
| ticker | varchar | Stock symbol (e.g., AAPL, 0700.HK) |
| open | double | Opening price |
| high | double | High price |
| low | double | Low price |
| close | double | Closing price |
| volume | double | Trading volume |
| returns | double | Daily return |

**Sample Query:**
```sql
SELECT * FROM silver.historical_stock_data 
WHERE ticker = 'AAPL' 
AND date >= '2024-01-01'
ORDER BY date DESC;
```

#### 2. historical_news
**Purpose:** News sentiment data for NLP strategies

---

## SCHEMA: GOLD (Signals/Marts) - READ ONLY

### Key Tables for Strategies

#### 1. stock_metrics
**Purpose:** Pre-calculated technical indicators for all stocks

| Column | Type | Description |
|--------|------|-------------|
| date | timestamp | Date |
| ticker | varchar | Stock symbol |
| sector | varchar | Sector classification |
| close | double | Closing price |
| volume | bigint | Volume |
| vwap | double | Volume-weighted average price |
| relative_vol_10d | double | Volume relative to 10-day avg |
| rsi_14 | double | RSI(14) - key for RSI Mean Reversion |
| macd_hist | double | MACD histogram |
| sma_50 | double | 50-day moving average |
| sma_200 | double | 200-day moving average |
| dist_from_52w_high | double | % distance from 52-week high |
| atr_14 | double | Average true range (volatility) |
| beta | double | Market beta |
| sharpe_ratio | double | Rolling Sharpe ratio |

**Use for RSI Mean Reversion:**
```sql
-- Find oversold stocks
SELECT ticker, close, rsi_14, sector
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
AND rsi_14 < 30
AND relative_vol_10d > 1.3
ORDER BY rsi_14 ASC;
```

#### 2. fx_metrics
**Purpose:** Forex data for AH Premium and FX strategies

| Column | Type | Description |
|--------|------|-------------|
| date | timestamp | Date |
| ticker | varchar | FX pair (e.g., USDJPY=X) |
| close_price | double | Closing rate |
| rsi_14 | double | RSI indicator |
| interest_rate_diff | double | Carry differential |
| market_regime | varchar | Trend/mean-reversion regime |
| prophet_forecast | double | ML forecast |

**Use for AH Premium (HKD/CNY proxy):**
```sql
-- Monitor USD strength (affects HKD via peg)
SELECT ticker, close_price, rsi_14
FROM gold.fx_metrics
WHERE ticker IN ('USDJPY=X', 'USDCNY=X', 'USDCNH=X')
AND date >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY date DESC;
```

#### 3. commodity_metrics
**Purpose:** Gold/Silver and other commodity data

| Column | Type | Description |
|--------|------|-------------|
| date | timestamp | Date |
| ticker | varchar | GC=F (Gold), SI=F (Silver), etc. |
| close_price | double | Price |
| rsi_14 | double | RSI |
| prophet_forecast | double | Forecast return |
| candlestick_pattern | varchar | Pattern detected |

**Use for Gold/Silver Ratio Strategy:**
```sql
-- Current Gold/Silver data
SELECT ticker, close_price, rsi_14, prophet_forecast
FROM gold.commodity_metrics
WHERE ticker IN ('GC=F', 'SI=F')
ORDER BY date DESC
LIMIT 2;
```

#### 4. strategy_performance
**Purpose:** Track deployed strategy performance

#### 5. strategy_signals
**Purpose:** Live trading signals from JT platform

#### 6. sentiment_mart
**Purpose:** Aggregated sentiment data

#### 7. market_regimes
**Purpose:** HMM regime detection output

#### 8. earnings_data
**Purpose:** Earnings calendar and surprises

**Use for PEAD Strategy:**
```sql
-- Upcoming earnings
SELECT ticker, earnings_date, surprise_pct
FROM gold.earnings_data
WHERE earnings_date >= CURRENT_DATE
ORDER BY earnings_date
LIMIT 10;
```

#### 9. sue_scores
**Purpose:** Standardized unexpected earnings

#### 10. Views (v_ prefix)
- v_commodities_coverage
- v_earnings_coverage
- v_latest_sue_scores
- v_seasonal_opportunities

---

## SCHEMA: CONSUMPTION (JT Platform Output) - READ ONLY

### Tables

#### 1. stock
**Purpose:** JT AI Trading platform stock analysis output

| Column | Type | Description |
|--------|------|-------------|
| timestamp | timestamp | Analysis timestamp |
| ticker | varchar | Stock symbol |
| market | varchar | Market (US, HK, etc.) |
| final_score | double | Composite score (-100 to +100) |
| est_1d/7d/1m | varchar | Forecast direction |
| metrics | jsonb | Detailed metrics |
| trad_confidence | double | Confidence 0-100 |
| swarm_confidence | double | Swarm AI confidence |
| win_rate | double | Historical win rate |
| strategy_tags | jsonb | Applicable strategies |
| candlestick_pattern | varchar | Detected pattern |

**Use for Signal Confirmation:**
```sql
-- JT platform recommendations
SELECT ticker, final_score, trad_confidence, win_rate, strategy_tags
FROM consumption.stock
WHERE market = 'HK'
AND timestamp >= CURRENT_DATE
ORDER BY final_score DESC
LIMIT 10;
```

#### 2. trades
**Purpose:** Executed trades log

#### 3. market
**Purpose:** Market-level indicators

#### 4. fx
**Purpose:** FX analysis output

#### 5. commodities
**Purpose:** Commodity analysis output

#### 6. crypto
**Purpose:** Crypto analysis output

---

## SCHEMA: OPENCLAW_RESEARCHER (My Workspace) - FULL ACCESS

### Tables Created

#### 1. hypothesis_registry
**Purpose:** Track all hypotheses and their status

| Column | Type | Description |
|--------|------|-------------|
| hypothesis_name | varchar | Unique name |
| hypothesis_file | varchar | Path to markdown file |
| academic_basis | varchar | Source paper |
| asset_class | varchar | Equities/FX/etc. |
| direction | varchar | Long/Short/etc. |
| target_sharpe | decimal | Expected Sharpe |
| target_win_rate | decimal | Expected win rate |
| current_status | varchar | idea/testing/validated |
| backtest_count | int | Number of backtests run |
| best_sharpe | decimal | Best achieved Sharpe |
| promoted_to_strategy | boolean | If moved to Golden |

**Current Entries (13 new hypotheses):**
```
PEAD NLP Enhanced       | testing | 1.45 | 67%
Accruals Quality        | testing | 1.35 | 64%
CMV Multi-Factor        | testing | 1.35 | 62%
Volatility Risk Premium | testing | 1.25 | 62%
Quality Value QARP      | testing | 1.25 | 62%
Momentum Lifecycle      | testing | 1.25 | 62%
Retail Order Flow       | testing | 1.25 | 60%
LLM NLP Sentiment       | testing | 1.20 | 62%
Inflation Regime Switch | testing | 1.15 | 70%
Time-Series Momentum    | testing | 1.15 | 58%
Limits to Arbitrage     | testing | 1.15 | 62%
Supply Chain Reshoring  | testing | 1.05 | 62%
ESG Improvers           | testing | 0.90 | 58%
```

#### 2. backtest_results
**Purpose:** Store backtest performance summaries

| Column | Type | Description |
|--------|------|-------------|
| id | serial | Primary key |
| hypothesis_name | varchar | Link to registry |
| start_date | date | Backtest start |
| end_date | date | Backtest end |
| total_return_pct | decimal | Total return |
| sharpe_ratio | decimal | Risk-adjusted return |
| max_drawdown_pct | decimal | Worst peak-to-trough |
| win_rate_pct | decimal | % winning trades |
| status | varchar | running/completed/failed |
| parameters | jsonb | Strategy parameters |

#### 3. backtest_trades
**Purpose:** Individual trade records from backtests

| Column | Type | Description |
|--------|------|-------------|
| backtest_id | int | Reference to results |
| ticker | varchar | Stock symbol |
| entry_date | timestamp | Entry timestamp |
| exit_date | timestamp | Exit timestamp |
| entry_price | decimal | Entry price |
| exit_price | decimal | Exit price |
| direction | varchar | LONG/SHORT |
| pnl_pct | decimal | Trade return % |
| exit_reason | varchar | Signal/stop/time |
| holding_days | int | Days held |

---

## BACKTEST WORKFLOW

### Step 1: Query Silver/Gold for Data
```sql
-- Get price data for backtest
SELECT date, ticker, close, volume, rsi_14
FROM gold.stock_metrics
WHERE ticker IN ('AAPL', 'MSFT', 'NVDA')
AND date BETWEEN '2020-01-01' AND '2024-12-31'
ORDER BY ticker, date;
```

### Step 2: Run Backtest (Python)
```python
# Process data, generate signals, calculate P&L
# ... backtest logic ...
```

### Step 3: Store Results
```sql
INSERT INTO openclaw_researcher.backtest_results 
(hypothesis_name, start_date, end_date, total_return_pct, 
 sharpe_ratio, max_drawdown_pct, win_rate_pct, status)
VALUES ('Accruals Quality', '2020-01-01', '2024-12-31', 
        15.5, 1.35, -8.2, 64.0, 'completed');
```

### Step 4: Update Registry
```sql
UPDATE openclaw_researcher.hypothesis_registry
SET backtest_count = backtest_count + 1,
    best_sharpe = 1.35,
    last_backtest_date = CURRENT_DATE
WHERE hypothesis_name = 'Accruals Quality';
```

---

## KEY DATA SOURCES FOR STRATEGIES

| Strategy | Primary Schema | Key Tables |
|----------|----------------|------------|
| RSI Mean Reversion | gold | stock_metrics (rsi_14) |
| AH Premium | gold | fx_metrics (HKD/CNY proxy) |
| Gold/Silver | gold | commodity_metrics |
| PEAD | gold | earnings_data, sue_scores |
| ESG | gold | institutional_holdings |
| Accruals | silver | historical_stock_data + calculations |
| Momentum | gold | stock_metrics (sma_50/200) |
| Time-Series | gold | fx_metrics, commodity_metrics |

---

## NOTES

1. **Silver/Gold/Consumption:** READ ONLY - Use for queries, not modifications
2. **openclaw_researcher:** FULL ACCESS - Build tables for backtests
3. **Token expires:** 15 minutes - Regenerate for long queries
4. **Connection:** Via IAM auth - No password stored
5. **Latency:** ~10-50ms within same AWS region

---

**Last Updated:** 2026-02-20
