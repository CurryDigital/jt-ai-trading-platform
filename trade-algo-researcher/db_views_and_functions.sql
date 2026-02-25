-- Database Views and Functions for Trade Algo Researcher
-- Schema: openclaw_researcher
-- Purpose: Helper views for backtesting and analysis

-- =====================================================
-- VIEWS FOR BACKTEST ANALYSIS
-- =====================================================

-- View: Latest backtest results with ranking
CREATE OR REPLACE VIEW openclaw_researcher.v_backtest_rankings AS
SELECT 
    hypothesis_name,
    MAX(sharpe_ratio) as best_sharpe,
    MAX(win_rate_pct) as best_win_rate,
    COUNT(*) as total_backtests,
    MAX(created_at) as last_run
FROM openclaw_researcher.backtest_results
WHERE status = 'completed'
GROUP BY hypothesis_name
ORDER BY best_sharpe DESC;

-- View: Hypotheses ready for promotion (Sharpe > 1.0)
CREATE OR REPLACE VIEW openclaw_researcher.v_promotion_candidates AS
SELECT 
    h.hypothesis_name,
    h.academic_basis,
    h.asset_class,
    h.target_sharpe,
    r.best_sharpe as achieved_sharpe,
    r.best_win_rate,
    r.total_backtests,
    h.backtest_count
FROM openclaw_researcher.hypothesis_registry h
LEFT JOIN openclaw_researcher.v_backtest_rankings r 
    ON h.hypothesis_name = r.hypothesis_name
WHERE r.best_sharpe > 1.0
  AND h.current_status = 'testing'
  AND h.backtest_count >= 3
ORDER BY r.best_sharpe DESC;

-- View: Trade-level performance analysis
CREATE OR REPLACE VIEW openclaw_researcher.v_trade_performance AS
SELECT 
    b.hypothesis_name,
    t.ticker,
    t.direction,
    COUNT(*) as total_trades,
    AVG(t.pnl_pct) as avg_pnl,
    SUM(CASE WHEN t.pnl_pct > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as win_rate,
    AVG(t.holding_days) as avg_hold_days,
    MIN(t.pnl_pct) as worst_trade,
    MAX(t.pnl_pct) as best_trade
FROM openclaw_researcher.backtest_trades t
JOIN openclaw_researcher.backtest_results b ON t.backtest_id = b.id
GROUP BY b.hypothesis_name, t.ticker, t.direction;

-- =====================================================
-- VIEWS USING GOLD SCHEMA (Read-Only Access)
-- =====================================================

-- View: Current RSI signals (combines with volume)
CREATE OR REPLACE VIEW openclaw_researcher.v_rsi_signals_today AS
SELECT 
    date,
    ticker,
    sector,
    close,
    volume,
    relative_vol_10d,
    rsi_14,
    CASE 
        WHEN rsi_14 < 30 AND relative_vol_10d > 1.3 THEN 'STRONG_BUY'
        WHEN rsi_14 < 30 THEN 'BUY'
        WHEN rsi_14 > 70 AND relative_vol_10d > 1.3 THEN 'STRONG_SELL'
        WHEN rsi_14 > 70 THEN 'SELL'
        ELSE 'NEUTRAL'
    END as signal,
    atr_14
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
ORDER BY rsi_14 ASC;

-- View: Momentum ranking
CREATE OR REPLACE VIEW openclaw_researcher.v_momentum_ranking AS
SELECT 
    date,
    ticker,
    sector,
    close,
    (close - sma_50) / sma_50 * 100 as distance_from_50d,
    (close - sma_200) / sma_200 * 100 as distance_from_200d,
    CASE 
        WHEN close > sma_50 AND sma_50 > sma_200 THEN 'STRONG_UPTREND'
        WHEN close > sma_50 THEN 'UPTREND'
        WHEN close < sma_50 AND sma_50 < sma_200 THEN 'STRONG_DOWNTREND'
        WHEN close < sma_50 THEN 'DOWNTREND'
        ELSE 'NEUTRAL'
    END as trend_regime,
    sharpe_ratio
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
ORDER BY distance_from_50d DESC;

-- View: Gold/Silver ratio strategy status
CREATE OR REPLACE VIEW openclaw_researcher.v_gold_silver_status AS
WITH latest_commodities AS (
    SELECT DISTINCT ON (ticker)
        ticker,
        date,
        close_price,
        rsi_14,
        prophet_forecast,
        candlestick_pattern
    FROM gold.commodity_metrics
    ORDER BY ticker, date DESC
)
SELECT 
    MAX(CASE WHEN ticker = 'GC=F' THEN close_price END) as gold_price,
    MAX(CASE WHEN ticker = 'SI=F' THEN close_price END) as silver_price,
    MAX(CASE WHEN ticker = 'GC=F' THEN close_price END) / 
    NULLIF(MAX(CASE WHEN ticker = 'SI=F' THEN close_price END), 0) as gold_silver_ratio,
    MAX(CASE WHEN ticker = 'GC=F' THEN rsi_14 END) as gold_rsi,
    MAX(CASE WHEN ticker = 'SI=F' THEN rsi_14 END) as silver_rsi,
    MAX(CASE WHEN ticker = 'GC=F' THEN date END) as last_update
FROM latest_commodities
WHERE ticker IN ('GC=F', 'SI=F');

-- View: AH Premium monitoring (FX as proxy)
CREATE OR REPLACE VIEW openclaw_researcher.v_ah_premium_fx AS
SELECT 
    date,
    ticker,
    close_price,
    rsi_14,
    interest_rate_diff,
    market_regime,
    CASE 
        WHEN ticker = 'USDJPY=X' THEN 'Safe_Haven'
        WHEN ticker LIKE '%CNH%' OR ticker LIKE '%CNY%' THEN 'CNY_Proxy'
        WHEN ticker LIKE '%HKD%' THEN 'HKD_Proxy'
        ELSE 'Other'
    END as fx_category
FROM gold.fx_metrics
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, ticker;

-- View: Earnings surprise opportunities
CREATE OR REPLACE VIEW openclaw_researcher.v_earnings_opportunities AS
SELECT 
    e.ticker,
    e.earnings_date,
    e.eps_estimate,
    e.eps_actual,
    e.surprise_pct * 100 as surprise_pct,
    s.close as current_price,
    s.rsi_14,
    CASE 
        WHEN e.surprise_pct > 0.1 AND s.rsi_14 < 50 THEN 'PEAD_LONG'
        WHEN e.surprise_pct < -0.1 AND s.rsi_14 > 50 THEN 'PEAD_SHORT'
        ELSE 'NEUTRAL'
    END as pead_signal
FROM gold.earnings_data e
LEFT JOIN gold.stock_metrics s 
    ON e.ticker = s.ticker AND s.date = CURRENT_DATE
WHERE e.earnings_date >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY ABS(e.surprise_pct) DESC
LIMIT 50;

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function: Calculate backtest statistics
CREATE OR REPLACE FUNCTION openclaw_researcher.calculate_backtest_stats(
    p_backtest_id INTEGER
)
RETURNS TABLE (
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate NUMERIC,
    avg_return NUMERIC,
    total_return NUMERIC,
    max_drawdown NUMERIC,
    sharpe_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_trades,
        SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END)::INTEGER as winning_trades,
        SUM(CASE WHEN pnl_pct <= 0 THEN 1 ELSE 0 END)::INTEGER as losing_trades,
        ROUND(SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) as win_rate,
        ROUND(AVG(pnl_pct), 4) as avg_return,
        ROUND(SUM(pnl_pct), 4) as total_return,
        ROUND(MIN(pnl_pct), 4) as max_drawdown,
        ROUND(AVG(pnl_pct) / NULLIF(STDDEV(pnl_pct), 0), 4) as sharpe_ratio
    FROM openclaw_researcher.backtest_trades
    WHERE backtest_id = p_backtest_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get best performing hypothesis in date range
CREATE OR REPLACE FUNCTION openclaw_researcher.get_top_hypothesis(
    p_start_date DATE,
    p_end_date DATE,
    p_min_trades INTEGER DEFAULT 10
)
RETURNS TABLE (
    hypothesis_name VARCHAR,
    avg_sharpe NUMERIC,
    avg_win_rate NUMERIC,
    total_backtests BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.hypothesis_name,
        ROUND(AVG(b.sharpe_ratio), 4) as avg_sharpe,
        ROUND(AVG(b.win_rate_pct), 2) as avg_win_rate,
        COUNT(*) as total_backtests
    FROM openclaw_researcher.backtest_results b
    WHERE b.created_at::DATE BETWEEN p_start_date AND p_end_date
      AND b.total_trades >= p_min_trades
      AND b.status = 'completed'
    GROUP BY b.hypothesis_name
    ORDER BY AVG(b.sharpe_ratio) DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- Function: Update hypothesis after backtest
CREATE OR REPLACE FUNCTION openclaw_researcher.record_backtest_completion()
RETURNS TRIGGER AS $$
BEGIN
    -- Update hypothesis registry
    UPDATE openclaw_researcher.hypothesis_registry
    SET backtest_count = backtest_count + 1,
        last_backtest_date = CURRENT_DATE,
        current_status = CASE 
            WHEN NEW.sharpe_ratio > 1.0 THEN 'validated'
            WHEN NEW.sharpe_ratio > 0.7 THEN 'testing'
            ELSE 'rejected'
        END
    WHERE hypothesis_name = NEW.hypothesis_name;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (optional - uncomment if desired)
-- CREATE TRIGGER trg_backtest_completion
-- AFTER INSERT ON openclaw_researcher.backtest_results
-- FOR EACH ROW
-- EXECUTE FUNCTION openclaw_researcher.record_backtest_completion();

-- =====================================================
-- MATERIALIZED VIEWS (for performance)
-- =====================================================

-- Materialized view: Daily signal summary
CREATE MATERIALIZED VIEW IF NOT EXISTS openclaw_researcher.mv_daily_signals AS
SELECT 
    CURRENT_DATE as analysis_date,
    'RSI_OVERSOLD' as signal_type,
    COUNT(*) as signal_count,
    STRING_AGG(ticker, ', ') as tickers
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
  AND rsi_14 < 30
  AND relative_vol_10d > 1.0

UNION ALL

SELECT 
    CURRENT_DATE,
    'RSI_OVERBOUGHT',
    COUNT(*),
    STRING_AGG(ticker, ', ')
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
  AND rsi_14 > 70
  AND relative_vol_10d > 1.0

UNION ALL

SELECT 
    CURRENT_DATE,
    'GOLDEN_CROSS' as signal_type,
    COUNT(*),
    STRING_AGG(ticker, ', ')
FROM gold.stock_metrics
WHERE date = CURRENT_DATE
  AND close > sma_50
  AND sma_50 > sma_200;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_daily_signals_date 
ON openclaw_researcher.mv_daily_signals(analysis_date);

-- Refresh function
CREATE OR REPLACE FUNCTION openclaw_researcher.refresh_daily_signals()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW openclaw_researcher.mv_daily_signals;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- QUERY EXAMPLES
-- =====================================================

/*
-- Example 1: Get today's RSI signals
SELECT * FROM openclaw_researcher.v_rsi_signals_today 
WHERE signal IN ('STRONG_BUY', 'BUY')
LIMIT 20;

-- Example 2: Check backtest performance
SELECT * FROM openclaw_researcher.v_backtest_rankings;

-- Example 3: Find promotion candidates
SELECT * FROM openclaw_researcher.v_promotion_candidates;

-- Example 4: Get trade statistics for a backtest
SELECT * FROM openclaw_researcher.calculate_backtest_stats(1);

-- Example 5: Top hypotheses this month
SELECT * FROM openclaw_researcher.get_top_hypothesis(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE
);

-- Example 6: Current Gold/Silver status
SELECT * FROM openclaw_researcher.v_gold_silver_status;

-- Example 7: Earnings opportunities
SELECT * FROM openclaw_researcher.v_earnings_opportunities 
WHERE pead_signal != 'NEUTRAL';
*/

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA openclaw_researcher IS 'Workspace for Trade Algo Researcher - backtesting and analysis';
COMMENT ON TABLE openclaw_researcher.backtest_results IS 'Stores backtest performance summaries';
COMMENT ON TABLE openclaw_researcher.backtest_trades IS 'Individual trade records from backtests';
COMMENT ON TABLE openclaw_researcher.hypothesis_registry IS 'Tracks all hypotheses and their validation status';
