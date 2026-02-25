-- Backtest Results Table
CREATE TABLE IF NOT EXISTS gold.backtest_runs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES gold.quant_strategies(id),
    run_date TIMESTAMPTZ DEFAULT NOW(),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return_pct FLOAT,
    sharpe_ratio FLOAT,
    max_drawdown_pct FLOAT,
    win_rate FLOAT,
    total_trades INTEGER,
    avg_trade_return FLOAT,
    raw_results JSONB,
    UNIQUE(strategy_id, start_date, end_date)
);

CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON gold.backtest_runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_date ON gold.backtest_runs(run_date DESC);

-- Strategy Performance Comparison View
CREATE OR REPLACE VIEW gold.strategy_performance_comparison AS
SELECT 
    s.id as strategy_id,
    s.name as strategy_name,
    s.target_ticker,
    s.current_pnl as live_pnl,
    s.total_trades as live_trades,
    CASE WHEN s.total_trades > 0 THEN (s.winning_trades::float / s.total_trades * 100) ELSE 0 END as live_win_rate,
    b.total_return_pct as backtest_return,
    b.sharpe_ratio as backtest_sharpe,
    b.max_drawdown_pct as backtest_dd,
    b.win_rate as backtest_win_rate,
    b.total_trades as backtest_trades,
    b.run_date as backtest_date
FROM gold.quant_strategies s
LEFT JOIN LATERAL (
    SELECT * FROM gold.backtest_runs 
    WHERE strategy_id = s.id 
    ORDER BY run_date DESC 
    LIMIT 1
) b ON true;
