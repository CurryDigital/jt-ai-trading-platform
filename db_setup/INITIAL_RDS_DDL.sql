-- JT Trading Platform - Full RDS Schema DDL (v4.1)
-- Timezone: Asia/Hong_Kong

-- 1. SCHEMAS
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS consumption;

-- 2. BRONZE LAYER (Raw Ingestion)
CREATE TABLE IF NOT EXISTS bronze.raw_stock_data (
    date TIMESTAMP NOT NULL,
    id SERIAL,
    ticker VARCHAR(20) NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    ingested_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    asset_category VARCHAR(20),
    PRIMARY KEY (date, id)
);

-- 3. SILVER LAYER (Historical Archive)
CREATE TABLE IF NOT EXISTS silver.historical_stock_data (
    date TIMESTAMP NOT NULL,
    id SERIAL,
    ticker VARCHAR(20) NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    returns DOUBLE PRECISION,
    PRIMARY KEY (date, id)
);

-- 4. GOLD LAYER (Institutional Intelligence Mart)
CREATE TABLE IF NOT EXISTS gold.asset_registry (
    ticker VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    asset_class VARCHAR(20) NOT NULL,
    market VARCHAR(20),
    horizon VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

CREATE TABLE IF NOT EXISTS gold.stock_metrics (
    date TIMESTAMP NOT NULL,
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    sector VARCHAR(50),
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    rsi_14 DOUBLE PRECISION,
    pe_ratio_ttm DOUBLE PRECISION,
    free_cash_flow DOUBLE PRECISION,
    debt_to_equity DOUBLE PRECISION,
    prophet_forecast DOUBLE PRECISION,
    UNIQUE (ticker, date)
);

CREATE TABLE IF NOT EXISTS gold.fx_metrics (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    close_price DOUBLE PRECISION,
    log_return DOUBLE PRECISION,
    interest_rate_diff DOUBLE PRECISION,
    dxy_correlation DOUBLE PRECISION,
    volatility_24h DOUBLE PRECISION,
    rsi_14 DOUBLE PRECISION,
    prophet_forecast DOUBLE PRECISION,
    market_regime VARCHAR(20),
    UNIQUE (ticker, date)
);

CREATE TABLE IF NOT EXISTS gold.crypto_metrics (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    close_price DOUBLE PRECISION,
    log_return DOUBLE PRECISION,
    volume_24h BIGINT,
    market_cap_usd DOUBLE PRECISION,
    btc_dominance DOUBLE PRECISION,
    eth_gas_price_gwei DOUBLE PRECISION,
    hash_rate_th_s DOUBLE PRECISION,
    exchange_inflow_proxy DOUBLE PRECISION,
    exchange_outflow_proxy DOUBLE PRECISION,
    fear_greed_index INTEGER,
    stablecoin_supply_ratio DOUBLE PRECISION,
    funding_rate DOUBLE PRECISION,
    liquidations_24h_usd DOUBLE PRECISION,
    rsi_14 DOUBLE PRECISION,
    prophet_forecast DOUBLE PRECISION,
    lsd_divergence_score DOUBLE PRECISION,
    UNIQUE (ticker, date)
);

CREATE TABLE IF NOT EXISTS gold.commodity_metrics (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    close_price DOUBLE PRECISION,
    log_return DOUBLE PRECISION,
    volume BIGINT,
    us_10y_real_yield DOUBLE PRECISION,
    dxy_close DOUBLE PRECISION,
    gold_silver_ratio DOUBLE PRECISION,
    rsi_14 DOUBLE PRECISION,
    bollinger_width DOUBLE PRECISION,
    seasonality_score DOUBLE PRECISION,
    prophet_forecast DOUBLE PRECISION,
    UNIQUE (ticker, date)
);

CREATE TABLE IF NOT EXISTS gold.metric_definitions (
    id SERIAL PRIMARY KEY,
    asset_class VARCHAR(20),
    metric_name VARCHAR(50),
    formula_raw TEXT,
    description TEXT,
    weight_impact VARCHAR(20),
    source VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS gold.strategy_performance (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    strategy_return FLOAT,
    benchmark_return FLOAT,
    period VARCHAR(20),
    UNIQUE (date, period)
);

CREATE TABLE IF NOT EXISTS gold.backtest_curve_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    equity_value FLOAT,
    benchmark_value FLOAT
);

-- 5. CONSUMPTION LAYER (UI-Optimized)
CREATE TABLE IF NOT EXISTS consumption.global_state (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE,
    value TEXT,
    category VARCHAR(50),
    rationale TEXT,
    estimates JSONB,
    timestamp TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

CREATE TABLE IF NOT EXISTS consumption.inventory (
    id SERIAL PRIMARY KEY,
    purchase_date TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    ticker VARCHAR(20) NOT NULL,
    asset_class VARCHAR(20),
    quantity DOUBLE PRECISION,
    buy_price DOUBLE PRECISION,
    current_price DOUBLE PRECISION,
    win_loss VARCHAR(20),
    analysis JSONB,
    status VARCHAR(20) DEFAULT 'held',
    est_1d VARCHAR(20),
    est_7d VARCHAR(20),
    est_1m VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS consumption.stock (
    timestamp TIMESTAMP NOT NULL,
    id SERIAL,
    ticker VARCHAR(20) NOT NULL,
    market VARCHAR(10),
    horizon VARCHAR(20),
    close_price DOUBLE PRECISION,
    daily_change DOUBLE PRECISION,
    final_score DOUBLE PRECISION,
    est_1d VARCHAR(20),
    est_7d VARCHAR(20),
    est_1m VARCHAR(20),
    sparkline JSONB,
    logic_summary TEXT,
    metrics JSONB,
    trad_confidence DOUBLE PRECISION,
    swarm_confidence DOUBLE PRECISION,
    PRIMARY KEY (ticker, timestamp)
);

CREATE TABLE IF NOT EXISTS consumption.fx (
    timestamp TIMESTAMP NOT NULL,
    id SERIAL,
    pair VARCHAR(20),
    action VARCHAR(10),
    close_price DOUBLE PRECISION,
    daily_change DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    est_1d VARCHAR(20),
    est_7d VARCHAR(20),
    est_1m VARCHAR(20),
    reasoning TEXT,
    trad_confidence DOUBLE PRECISION,
    swarm_confidence DOUBLE PRECISION,
    sparkline JSONB,
    PRIMARY KEY (pair, timestamp)
);

CREATE TABLE IF NOT EXISTS consumption.crypto (
    timestamp TIMESTAMP NOT NULL,
    id SERIAL,
    asset VARCHAR(50),
    ticker VARCHAR(20),
    action VARCHAR(10),
    close_price DOUBLE PRECISION,
    daily_change DOUBLE PRECISION,
    est_1d VARCHAR(20),
    est_7d VARCHAR(20),
    est_1m VARCHAR(20),
    sparkline JSONB,
    reasoning TEXT,
    trad_confidence DOUBLE PRECISION,
    swarm_confidence DOUBLE PRECISION,
    mvrv_z_score DOUBLE PRECISION,
    nvt_ratio DOUBLE PRECISION,
    fear_greed_index INTEGER,
    funding_rate DOUBLE PRECISION,
    gas_price_gwei DOUBLE PRECISION,
    hash_rate_th_s DOUBLE PRECISION,
    PRIMARY KEY (ticker, timestamp)
);

CREATE TABLE IF NOT EXISTS consumption.commodities (
    timestamp TIMESTAMP NOT NULL,
    id SERIAL,
    asset VARCHAR(50),
    ticker VARCHAR(20),
    action VARCHAR(10),
    close_price DOUBLE PRECISION,
    daily_change DOUBLE PRECISION,
    est_1d VARCHAR(20),
    est_7d VARCHAR(20),
    est_1m VARCHAR(20),
    sparkline JSONB,
    reasoning TEXT,
    trad_confidence DOUBLE PRECISION,
    swarm_confidence DOUBLE PRECISION,
    PRIMARY KEY (ticker, timestamp)
);

CREATE TABLE IF NOT EXISTS consumption.hft_matrix (
    timestamp TIMESTAMP NOT NULL,
    id SERIAL,
    ticker VARCHAR(20),
    asset_class VARCHAR(20),
    liquidity_momentum VARCHAR(20),
    fusion_signal VARCHAR(20),
    shock_warning VARCHAR(20),
    pressure_value DOUBLE PRECISION,
    reasoning TEXT,
    PRIMARY KEY (ticker, timestamp)
);
