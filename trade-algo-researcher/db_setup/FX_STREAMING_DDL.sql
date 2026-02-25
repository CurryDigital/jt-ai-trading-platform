-- FX Streaming Tables (Phase 1.1)
-- High-frequency FX tick data and 5-second bar aggregation

-- Raw FX ticks from IBKR (tick-by-tick)
CREATE TABLE IF NOT EXISTS gold.fx_ticks (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    ticker VARCHAR(10) NOT NULL,
    bid DOUBLE PRECISION NOT NULL,
    ask DOUBLE PRECISION NOT NULL,
    mid DOUBLE PRECISION GENERATED ALWAYS AS ((bid + ask) / 2.0) STORED,
    spread_bps DOUBLE PRECISION GENERATED ALWAYS AS ((ask - bid) / ((bid + ask) / 2.0) * 10000.0) STORED,
    source VARCHAR(20) DEFAULT 'IBKR'
);

CREATE INDEX IF NOT EXISTS idx_fx_ticks_time ON gold.fx_ticks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fx_ticks_ticker ON gold.fx_ticks(ticker);
CREATE INDEX IF NOT EXISTS idx_fx_ticks_ticker_time ON gold.fx_ticks(ticker, timestamp DESC);

-- 5-second aggregated FX bars (balanced frequency)
CREATE TABLE IF NOT EXISTS gold.fx_bars_5s (
    bucket TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    bid_open DOUBLE PRECISION NOT NULL,
    bid_high DOUBLE PRECISION NOT NULL,
    bid_low DOUBLE PRECISION NOT NULL,
    bid_close DOUBLE PRECISION NOT NULL,
    ask_open DOUBLE PRECISION NOT NULL,
    ask_high DOUBLE PRECISION NOT NULL,
    ask_low DOUBLE PRECISION NOT NULL,
    ask_close DOUBLE PRECISION NOT NULL,
    spread_avg_bps DOUBLE PRECISION NOT NULL,
    spread_min_bps DOUBLE PRECISION NOT NULL,
    spread_max_bps DOUBLE PRECISION NOT NULL,
    tick_count INTEGER NOT NULL,
    source VARCHAR(20) DEFAULT 'IBKR',
    PRIMARY KEY (bucket, ticker)
);

CREATE INDEX IF NOT EXISTS idx_fx_bars_time ON gold.fx_bars_5s(bucket DESC);
CREATE INDEX IF NOT EXISTS idx_fx_bars_ticker_time ON gold.fx_bars_5s(ticker, bucket DESC);

-- FX spread alerts (when spreads widen beyond threshold)
CREATE TABLE IF NOT EXISTS gold.fx_alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    ticker VARCHAR(10) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    spread_bps DOUBLE PRECISION NOT NULL,
    threshold_bps DOUBLE PRECISION NOT NULL,
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_fx_alerts_time ON gold.fx_alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fx_alerts_ticker ON gold.fx_alerts(ticker);

-- FX streaming service status tracking
CREATE TABLE IF NOT EXISTS gold.fx_streaming_status (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    service VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    ticker VARCHAR(10),
    message TEXT,
    tick_count_5s INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_fx_status_time ON gold.fx_streaming_status(timestamp DESC);

-- Add to asset registry (if not exists)
INSERT INTO gold.asset_registry (ticker, name, asset_class, market, horizon, is_active) VALUES
    ('EURUSD=X', 'EUR/USD', 'FX', 'GLOBAL', 'Short Term', TRUE),
    ('USDJPY=X', 'USD/JPY', 'FX', 'GLOBAL', 'Short Term', TRUE),
    ('GBPUSD=X', 'GBP/USD', 'FX', 'GLOBAL', 'Short Term', TRUE)
ON CONFLICT (ticker) DO UPDATE SET is_active = TRUE;
