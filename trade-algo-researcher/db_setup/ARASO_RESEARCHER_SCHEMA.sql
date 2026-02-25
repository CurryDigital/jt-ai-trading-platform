-- ARASO Factor Model Schema (Researcher Sandbox)
-- Phase 2 Implementation: Dynamic PCA + HMM Regime Detection
-- Created: 2026-02-16

-- Create researcher schema for backtesting and strategy development
CREATE SCHEMA IF NOT EXISTS researcher;

-- ============================================================================
-- 1. UNIVERSE DEFINITION
-- ============================================================================

CREATE TABLE IF NOT EXISTS researcher.universe (
    ticker VARCHAR(20) PRIMARY KEY,
    sector VARCHAR(50),
    industry VARCHAR(100),
    market_cap_bucket VARCHAR(20), -- Large, Mid, Small
    avg_daily_volume DOUBLE PRECISION, -- 30-day average
    beta_spy DOUBLE PRECISION,
    is_active BOOLEAN DEFAULT TRUE,
    added_date TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    removed_date TIMESTAMP,
    removal_reason VARCHAR(100)
);

-- S&P 500 + liquid mid-caps for initial universe
INSERT INTO researcher.universe (ticker, sector, market_cap_bucket, is_active) VALUES
    ('AAPL', 'Technology', 'Large', TRUE),
    ('MSFT', 'Technology', 'Large', TRUE),
    ('NVDA', 'Technology', 'Large', TRUE),
    ('GOOGL', 'Technology', 'Large', TRUE),
    ('AMZN', 'Consumer Discretionary', 'Large', TRUE),
    ('META', 'Communication Services', 'Large', TRUE),
    ('TSLA', 'Consumer Discretionary', 'Large', TRUE),
    ('JPM', 'Financials', 'Large', TRUE),
    ('V', 'Financials', 'Large', TRUE),
    ('JNJ', 'Healthcare', 'Large', TRUE),
    ('UNH', 'Healthcare', 'Large', TRUE),
    ('XOM', 'Energy', 'Large', TRUE),
    ('WMT', 'Consumer Staples', 'Large', TRUE),
    ('PG', 'Consumer Staples', 'Large', TRUE),
    ('HD', 'Consumer Discretionary', 'Large', TRUE),
    ('MA', 'Financials', 'Large', TRUE),
    ('BAC', 'Financials', 'Large', TRUE),
    ('ABBV', 'Healthcare', 'Large', TRUE),
    ('PFE', 'Healthcare', 'Large', TRUE),
    ('KO', 'Consumer Staples', 'Large', TRUE)
ON CONFLICT (ticker) DO NOTHING;

-- ============================================================================
-- 2. FACTOR MODEL TABLES
-- ============================================================================

-- Factor returns (eigenportfolios from PCA)
CREATE TABLE IF NOT EXISTS researcher.factor_returns (
    date TIMESTAMP NOT NULL,
    factor_id INTEGER NOT NULL, -- 1-15 (top 15 eigenportfolios)
    return DOUBLE PRECISION NOT NULL,
    eigenvalue DOUBLE PRECISION, -- Explained variance
    cumulative_variance_explained DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    PRIMARY KEY (date, factor_id)
);

-- Factor loadings (betas) for each stock
CREATE TABLE IF NOT EXISTS researcher.factor_loadings (
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    factor_id INTEGER NOT NULL,
    beta DOUBLE PRECISION NOT NULL,
    decay_factor DOUBLE PRECISION DEFAULT 0.94,
    lookback_days INTEGER DEFAULT 63,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    PRIMARY KEY (date, ticker, factor_id)
);

-- Residual returns (stock returns - factor exposure)
CREATE TABLE IF NOT EXISTS researcher.residual_returns (
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    actual_return DOUBLE PRECISION NOT NULL,
    predicted_return DOUBLE PRECISION NOT NULL,
    residual DOUBLE PRECISION NOT NULL,
    residual_zscore DOUBLE PRECISION, -- Standardized residual
    n_factors_used INTEGER DEFAULT 15,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    PRIMARY KEY (date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_residuals_ticker_date ON researcher.residual_returns(ticker, date DESC);
CREATE INDEX IF NOT EXISTS idx_residuals_date ON researcher.residual_returns(date DESC);

-- ============================================================================
-- 3. HMM REGIME DETECTION TABLES
-- ============================================================================

-- HMM state probabilities for each stock
CREATE TABLE IF NOT EXISTS researcher.hmm_states (
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    p_random_walk DOUBLE PRECISION NOT NULL, -- P(State=0)
    p_mean_reverting DOUBLE PRECISION NOT NULL, -- P(State=1)
    current_state INTEGER, -- 0=RW, 1=MR (based on max probability)
    transition_prob_00 DOUBLE PRECISION, -- P(0→0)
    transition_prob_01 DOUBLE PRECISION, -- P(0→1)
    transition_prob_10 DOUBLE PRECISION, -- P(1→0)
    transition_prob_11 DOUBLE PRECISION, -- P(1→1)
    residual_volatility DOUBLE PRECISION,
    mean_reversion_speed DOUBLE PRECISION, -- Theta in OU process
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    PRIMARY KEY (date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_hmm_ticker_date ON researcher.hmm_states(ticker, date DESC);
CREATE INDEX IF NOT EXISTS idx_hmm_date ON researcher.hmm_states(date DESC);

-- HMM model parameters (updated periodically)
CREATE TABLE IF NOT EXISTS researcher.hmm_parameters (
    ticker VARCHAR(20) NOT NULL,
    training_start_date TIMESTAMP NOT NULL,
    training_end_date TIMESTAMP NOT NULL,
    mu_0 DOUBLE PRECISION, -- Mean in RW state
    mu_1 DOUBLE PRECISION, -- Mean in MR state
    sigma_0 DOUBLE PRECISION, -- Vol in RW state
    sigma_1 DOUBLE PRECISION, -- Vol in MR state
    theta_1 DOUBLE PRECISION, -- Mean reversion speed
    transition_matrix JSONB, -- Full 2x2 matrix
    log_likelihood DOUBLE PRECISION,
    aic DOUBLE PRECISION,
    bic DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    PRIMARY KEY (ticker, training_end_date)
);

-- ============================================================================
-- 4. SIGNAL GENERATION TABLES
-- ============================================================================

-- Trading signals from ARASO strategy
CREATE TABLE IF NOT EXISTS researcher.signals (
    signal_id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- ENTRY, EXIT, HOLD
    direction INTEGER NOT NULL, -- -1=SHORT, 0=FLAT, 1=LONG
    residual_zscore DOUBLE PRECISION,
    hmm_mr_probability DOUBLE PRECISION,
    sentiment_zscore DOUBLE PRECISION,
    macro_regime VARCHAR(50),
    position_scale DOUBLE PRECISION DEFAULT 1.0,
    target_position_value DOUBLE PRECISION, -- Dollar value
    entry_threshold DOUBLE PRECISION DEFAULT 1.5,
    exit_threshold DOUBLE PRECISION DEFAULT 0.3,
    confidence_score DOUBLE PRECISION, -- Combined signal strength
    reason TEXT, -- Why this signal was generated
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

CREATE INDEX IF NOT EXISTS idx_signals_date ON researcher.signals(date DESC);
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON researcher.signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_type ON researcher.signals(signal_type);

-- ============================================================================
-- 5. BACKTEST EXECUTION TABLES
-- ============================================================================

-- Simulated positions
CREATE TABLE IF NOT EXISTS researcher.positions (
    position_id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    exit_date TIMESTAMP,
    direction INTEGER NOT NULL, -- -1 or 1
    entry_price DOUBLE PRECISION NOT NULL,
    exit_price DOUBLE PRECISION,
    shares INTEGER,
    entry_residual_zscore DOUBLE PRECISION,
    exit_residual_zscore DOUBLE PRECISION,
    entry_signal_id INTEGER REFERENCES researcher.signals(signal_id),
    exit_signal_id INTEGER REFERENCES researcher.signals(signal_id),
    pnl DOUBLE PRECISION,
    return_pct DOUBLE PRECISION,
    hold_days INTEGER,
    exit_reason VARCHAR(50), -- mean_reversion, regime_change, stop_loss, max_hold
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

CREATE INDEX IF NOT EXISTS idx_positions_ticker ON researcher.positions(ticker);
CREATE INDEX IF NOT EXISTS idx_positions_status ON researcher.positions(status);

-- Daily portfolio snapshot
CREATE TABLE IF NOT EXISTS researcher.portfolio_daily (
    date TIMESTAMP NOT NULL PRIMARY KEY,
    total_equity DOUBLE PRECISION NOT NULL,
    cash DOUBLE PRECISION NOT NULL,
    long_exposure DOUBLE PRECISION,
    short_exposure DOUBLE PRECISION,
    gross_exposure DOUBLE PRECISION,
    net_exposure DOUBLE PRECISION,
    num_positions INTEGER,
    daily_pnl DOUBLE PRECISION,
    daily_return_pct DOUBLE PRECISION,
    cumulative_return_pct DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    beta_to_spy DOUBLE PRECISION,
    sector_exposure JSONB, -- {sector: exposure_value}
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

-- Trade-level performance metrics
CREATE TABLE IF NOT EXISTS researcher.trade_metrics (
    trade_id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    exit_date TIMESTAMP NOT NULL,
    direction INTEGER NOT NULL,
    pnl DOUBLE PRECISION,
    return_pct DOUBLE PRECISION,
    entry_zscore DOUBLE PRECISION,
    exit_zscore DOUBLE PRECISION,
    max_drawdown_trade DOUBLE PRECISION,
    max_profit_trade DOUBLE PRECISION,
    mfe DOUBLE PRECISION, -- Maximum favorable excursion
    mae DOUBLE PRECISION, -- Maximum adverse excursion
    hold_days INTEGER,
    exit_reason VARCHAR(50),
    regime_at_entry VARCHAR(50),
    sentiment_at_entry DOUBLE PRECISION
);

-- ============================================================================
-- 6. PERFORMANCE ANALYSIS TABLES
-- ============================================================================

-- Strategy performance summary (updated daily)
CREATE TABLE IF NOT EXISTS researcher.performance_summary (
    as_of_date TIMESTAMP NOT NULL PRIMARY KEY,
    total_return_pct DOUBLE PRECISION,
    annualized_return_pct DOUBLE PRECISION,
    volatility_ann DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    calmar_ratio DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    avg_trade_return_pct DOUBLE PRECISION,
    avg_win_pct DOUBLE PRECISION,
    avg_loss_pct DOUBLE PRECISION,
    avg_hold_days DOUBLE PRECISION,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    beta_neutral_deviation DOUBLE PRECISION, -- How far from beta=0
    sector_neutral_deviation DOUBLE PRECISION,
    dollar_neutral_deviation DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);

-- Rolling performance metrics (30-day, 90-day windows)
CREATE TABLE IF NOT EXISTS researcher.rolling_metrics (
    date TIMESTAMP NOT NULL,
    window_days INTEGER NOT NULL,
    return_pct DOUBLE PRECISION,
    volatility DOUBLE PRECISION,
    sharpe DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    PRIMARY KEY (date, window_days)
);

-- Factor attribution analysis
CREATE TABLE IF NOT EXISTS researcher.factor_attribution (
    date TIMESTAMP NOT NULL,
    factor_id INTEGER NOT NULL,
    factor_return DOUBLE PRECISION,
    portfolio_exposure DOUBLE PRECISION,
    attribution_pnl DOUBLE PRECISION,
    PRIMARY KEY (date, factor_id)
);

-- ============================================================================
-- 7. MACRO REGIME TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS researcher.macro_regime (
    date TIMESTAMP NOT NULL PRIMARY KEY,
    vix_close DOUBLE PRECISION,
    vix_percentile_30d DOUBLE PRECISION,
    yield_10y DOUBLE PRECISION,
    yield_2y DOUBLE PRECISION,
    yield_spread_10y_2y DOUBLE PRECISION,
    cpi_yoy DOUBLE PRECISION,
    cpi_surprise DOUBLE PRECISION,
    fed_funds_rate DOUBLE PRECISION,
    regime_classification VARCHAR(50), -- expansion, contraction, high_uncertainty, recovery
    position_scale DOUBLE PRECISION DEFAULT 1.0,
    trading_enabled BOOLEAN DEFAULT TRUE,
    reason TEXT
);

-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- Active signals view
CREATE OR REPLACE VIEW researcher.v_active_signals AS
SELECT 
    s.*,
    u.sector,
    r.residual,
    h.p_mean_reverting as hmm_confidence
FROM researcher.signals s
JOIN researcher.universe u ON s.ticker = u.ticker
LEFT JOIN researcher.residual_returns r ON s.ticker = r.ticker AND s.date = r.date
LEFT JOIN researcher.hmm_states h ON s.ticker = h.ticker AND s.date = h.date
WHERE s.date >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY s.date DESC, s.confidence_score DESC;

-- Open positions view
CREATE OR REPLACE VIEW researcher.v_open_positions AS
SELECT 
    p.*,
    u.sector,
    r.residual_zscore as current_zscore,
    h.p_mean_reverting as current_hmm_confidence
FROM researcher.positions p
JOIN researcher.universe u ON p.ticker = u.ticker
LEFT JOIN LATERAL (
    SELECT residual_zscore 
    FROM researcher.residual_returns r 
    WHERE r.ticker = p.ticker AND r.date <= CURRENT_TIMESTAMP 
    ORDER BY r.date DESC LIMIT 1
) r ON true
LEFT JOIN LATERAL (
    SELECT p_mean_reverting 
    FROM researcher.hmm_states h 
    WHERE h.ticker = p.ticker AND h.date <= CURRENT_TIMESTAMP 
    ORDER BY h.date DESC LIMIT 1
) h ON true
WHERE p.status = 'OPEN';

-- Performance summary view (latest)
CREATE OR REPLACE VIEW researcher.v_latest_performance AS
SELECT * FROM researcher.performance_summary
ORDER BY as_of_date DESC LIMIT 1;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON SCHEMA researcher IS 'Sandbox schema for ARASO strategy backtesting and research';
COMMENT ON TABLE researcher.factor_returns IS 'PCA eigenportfolio returns (top 15 factors)';
COMMENT ON TABLE researcher.residual_returns IS 'Stock returns minus factor exposure (pure alpha)';
COMMENT ON TABLE researcher.hmm_states IS 'Hidden Markov Model state probabilities per stock';
COMMENT ON TABLE researcher.signals IS 'ARASO trading signals with all components';
COMMENT ON TABLE researcher.positions IS 'Backtest position tracking';
