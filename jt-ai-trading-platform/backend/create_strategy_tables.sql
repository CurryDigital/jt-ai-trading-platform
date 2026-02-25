-- Strategy Screener Database Schema
-- Creates tables for storing strategy templates and backtest results

-- Strategy Templates (built-in and custom)
CREATE TABLE IF NOT EXISTS gold.strategy_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    asset_class VARCHAR(20) NOT NULL CHECK (asset_class IN ('STOCK', 'FX', 'CRYPTO', 'COMMODITY')),
    config_json JSONB NOT NULL,
    is_builtin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Strategy Backtest Results (per stock per strategy)
CREATE TABLE IF NOT EXISTS gold.strategy_backtests (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    strategy_id VARCHAR(50) NOT NULL REFERENCES gold.strategy_templates(id),
    
    -- Backtest metrics
    win_rate DECIMAL(5,4) NOT NULL,  -- 0.0 to 1.0
    sharpe_ratio DECIMAL(6,3),
    profit_factor DECIMAL(6,3),
    total_return DECIMAL(10,4),  -- percentage
    max_drawdown DECIMAL(10,4),  -- percentage
    avg_trade_return DECIMAL(10,4),  -- percentage
    num_trades INTEGER NOT NULL,
    winning_trades INTEGER,
    losing_trades INTEGER,
    
    -- Current signal
    current_signal VARCHAR(10) CHECK (current_signal IN ('BUY', 'SELL', 'HOLD')),
    signal_strength DECIMAL(4,3),  -- 0.0 to 1.0
    entry_price DECIMAL(15,4),
    stop_loss DECIMAL(15,4),
    target_price DECIMAL(15,4),
    
    -- Composite score for ranking
    strategy_score DECIMAL(6,4) NOT NULL,
    
    -- Metadata
    backtest_period VARCHAR(20),  -- '1y', '6m', etc.
    rationale TEXT,
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint: one backtest per stock per strategy
    UNIQUE(ticker, strategy_id)
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_backtests_strategy ON gold.strategy_backtests(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtests_asset_class ON gold.strategy_backtests(asset_class);
CREATE INDEX IF NOT EXISTS idx_backtests_score ON gold.strategy_backtests(strategy_score DESC);
CREATE INDEX IF NOT EXISTS idx_backtests_win_rate ON gold.strategy_backtests(win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_backtests_signal ON gold.strategy_backtests(current_signal) WHERE current_signal = 'BUY';
CREATE INDEX IF NOT EXISTS idx_backtests_calculated ON gold.strategy_backtests(calculated_at DESC);

-- Insert built-in strategy templates
INSERT INTO gold.strategy_templates (id, name, description, asset_class, config_json, is_builtin) VALUES
-- STOCK strategies
('mean_reversion', 'Mean Reversion', 'Buy oversold stocks (RSI < 30, below lower BB)', 'STOCK', 
 '{"entry_conditions": [{"type": "rsi_oversold", "period": 14, "threshold": 30}, {"type": "bb_lower_touch"}], "exit_conditions": [{"type": "rsi_reversion", "threshold": 70}, {"type": "bb_upper_touch"}], "stop_loss_type": "atr", "stop_loss_value": 2.0, "max_holding_days": 10}',
 TRUE),

('trend_following', 'Trend Following', 'Follow SMA crossovers with MACD confirmation', 'STOCK',
 '{"entry_conditions": [{"type": "sma_cross_up", "fast": 20, "slow": 50}, {"type": "macd_bullish"}], "exit_conditions": [{"type": "sma_cross_opposite"}], "stop_loss_type": "atr", "stop_loss_value": 3.0, "max_holding_days": 20}',
 TRUE),

('breakout_momentum', 'Breakout Momentum', 'Capture momentum on 20-day high breakouts', 'STOCK',
 '{"entry_conditions": [{"type": "breakout_high", "lookback": 20}, {"type": "volume_spike", "threshold": 1.5}], "exit_conditions": [{"type": "profit_target", "percent": 3.0}], "stop_loss_type": "fixed_percent", "stop_loss_value": 2.0, "max_holding_days": 5}',
 TRUE),

('earnings_momentum', 'Earnings Momentum', 'Trade post-earnings price drift', 'STOCK',
 '{"entry_conditions": [{"type": "gap_up", "percent": 5.0}, {"type": "volume_spike", "threshold": 2.0}], "exit_conditions": [{"type": "time_exit", "days": 3}], "stop_loss_type": "gap_fill", "max_holding_days": 5}',
 TRUE),

('value_play', 'Value Play', 'Fundamental value with technical entry', 'STOCK',
 '{"entry_conditions": [{"type": "pullback_to_sma", "period": 50}], "exit_conditions": [{"type": "profit_target", "percent": 10.0}], "stop_loss_type": "fixed_percent", "stop_loss_value": 10.0, "max_holding_days": 60}',
 TRUE),

('sector_rotation', 'Sector Rotation', 'Rotate into outperforming sectors', 'STOCK',
 '{"entry_conditions": [{"type": "relative_strength", "lookback": 90}, {"type": "sma_cross_up", "fast": 20, "slow": 50}], "exit_conditions": [{"type": "ranking_drop", "threshold": 5}], "stop_loss_type": "atr", "stop_loss_value": 2.5, "max_holding_days": 30}',
 TRUE),

-- FX strategies
('mean_reversion_fx', 'Mean Reversion FX', 'Exploit overextensions in currency pairs', 'FX',
 '{"entry_conditions": [{"type": "bb_extreme", "deviation": 2.5}, {"type": "rsi_extreme", "threshold": 20}], "exit_conditions": [{"type": "mean_reversion"}], "stop_loss_type": "fixed_pips", "stop_loss_value": 50, "max_holding_days": 2}',
 TRUE),

('trend_following_fx', 'Trend Following FX', 'Ride institutional order flow', 'FX',
 '{"entry_conditions": [{"type": "ema_cross_up", "fast": 8, "slow": 21}, {"type": "adx_strong", "threshold": 25}], "exit_conditions": [{"type": "ema_cross_opposite"}], "stop_loss_type": "atr", "stop_loss_value": 1.0, "max_holding_days": 10}',
 TRUE),

('carry_trade', 'Carry Trade', 'Earn interest rate differentials', 'FX',
 '{"entry_conditions": [{"type": "positive_swap"}], "exit_conditions": [{"type": "negative_swap_days", "days": 3}], "stop_loss_type": "fixed_percent", "stop_loss_value": 2.0, "max_holding_days": 90}',
 TRUE),

-- CRYPTO strategies
('mean_reversion_crypto', 'Mean Reversion Crypto', 'Capture volatility reversion', 'CRYPTO',
 '{"entry_conditions": [{"type": "rsi_oversold", "period": 14, "threshold": 25}, {"type": "bb_extreme", "deviation": 3.0}], "exit_conditions": [{"type": "rsi_reversion", "threshold": 50}], "stop_loss_type": "fixed_percent", "stop_loss_value": 4.0, "max_holding_days": 3}',
 TRUE),

('grid_trading', 'Grid Trading', 'Systematic buy low sell high', 'CRYPTO',
 '{"entry_conditions": [{"type": "grid_level"}], "exit_conditions": [{"type": "grid_target"}], "stop_loss_type": "range_break", "max_holding_days": 365}',
 TRUE),

('funding_arbitrage', 'Funding Rate Arb', 'Arbitrage funding rate differentials', 'CRYPTO',
 '{"entry_conditions": [{"type": "negative_funding", "threshold": -0.1}], "exit_conditions": [{"type": "funding_flip"}], "stop_loss_type": "funding_reversal", "max_holding_days": 30}',
 TRUE),

-- COMMODITY strategies
('trend_following_com', 'Trend Following Commodities', 'Ride commodity supercycles', 'COMMODITY',
 '{"entry_conditions": [{"type": "sma_cross_up", "fast": 20, "slow": 50}], "exit_conditions": [{"type": "sma_cross_opposite"}], "stop_loss_type": "atr", "stop_loss_value": 3.0, "max_holding_days": 60}',
 TRUE),

('seasonal_play', 'Seasonal Play', 'Trade seasonal commodity patterns', 'COMMODITY',
 '{"entry_conditions": [{"type": "seasonal_low"}], "exit_conditions": [{"type": "seasonal_peak"}], "stop_loss_type": "seasonal_break", "max_holding_days": 60}',
 TRUE)

ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    config_json = EXCLUDED.config_json;

-- Create view for strategy summary
CREATE OR REPLACE VIEW gold.strategy_summary AS
SELECT 
    strategy_id,
    asset_class,
    COUNT(*) as total_stocks,
    AVG(win_rate) as avg_win_rate,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(strategy_score) as avg_score,
    COUNT(*) FILTER (WHERE current_signal = 'BUY') as buy_signals,
    COUNT(*) FILTER (WHERE current_signal = 'SELL') as sell_signals,
    MAX(calculated_at) as last_updated
FROM gold.strategy_backtests
GROUP BY strategy_id, asset_class;

-- Add comment for documentation
COMMENT ON TABLE gold.strategy_backtests IS 'Stores backtest results for each stock/strategy combination. Updated daily by pipeline.';
COMMENT ON TABLE gold.strategy_templates IS 'Strategy configuration templates. Built-in strategies are marked with is_builtin=TRUE.';
