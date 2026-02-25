-- Hypothesis Rejection Workflow
-- Add rejected hypotheses to registry with reasons

-- Insert known rejected hypotheses from history
INSERT INTO openclaw_researcher.hypothesis_registry 
(hypothesis_name, hypothesis_file, academic_basis, asset_class, direction, 
 target_sharpe, target_win_rate, current_status, 
 rejection_reason, rejected_date, backtest_sharpe_actual, backtest_win_rate_actual, notes)
VALUES 
('MACD_Divergence', 'hypotheses/rejected/macd_divergence.md', 'Technical Analysis', 'Equities', 'Long/Short',
 1.0, 55, 'rejected',
 'Failed validation: 46% win rate below 50% threshold', '2026-02-15', 0.65, 46.0, 
 'Tested on 50+ tickers across 4 markets. Win rate consistently below random. Rejected per methodology.'),

('3Day_Reversal_Generic', 'hypotheses/rejected/3day_reversal.md', 'Technical Analysis', 'Equities', 'Long',
 1.0, 55, 'rejected',
 'Failed validation: 48% win rate, not viable as universal strategy', '2026-02-15', 0.72, 48.0,
 'Individual market tests showed 48-61% win rates. Only HK variant viable (promoted to strategy-region combo).'),

('Gap_Fade_Universal', 'hypotheses/rejected/gap_fade.md', 'Technical Analysis', 'Equities', 'Long',
 1.0, 55, 'rejected',
 'Failed validation: 47% win rate as universal, only HK works', '2026-02-15', 0.68, 47.0,
 'Universal approach failed. Gap Fade HK (3.45 Sharpe) promoted as market-specific strategy.'),

('Peer_Firm_Lag_Simple', 'hypotheses/rejected/peer_firm_lag.md', 'Cohen/Frazzini 2008', 'Equities', 'Long/Short',
 1.5, 60, 'rejected',
 'Zero lag found in cross-sector analysis: 0.7-0.8 correlation but no predictive lag', '2026-02-10', 0.45, 52.0,
 'Pivoted to Supply Chain Information Diffusion hypothesis. Original concept rejected after oil sector testing.'),

('VIX_Contango_VXX', 'hypotheses/rejected/vix_contango_vxx.md', 'VIX Term Structure', 'Options', 'Short Vol',
 1.2, 58, 'rejected',
 'VXX delisted in 2024, strategy no longer viable', '2026-02-01', NULL, NULL,
 'VXX ETN delisted by Barclays. Strategy requires VIX futures directly (new hypothesis created).'),

('Asian_Session_FX_Daily_Proxy', 'hypotheses/rejected/asian_session_daily.md', 'FX Microstructure', 'FX', 'Short',
 1.3, 60, 'rejected',
 'Daily overnight gap proxy failed: 24-47% win rate. Needs real hourly FX data', '2026-02-10', 0.35, 35.5,
 'Simplified proxy inadequate. True Asian Session edge requires TrueFX or IBKR hourly data.'),

('Crypto_Funding_Rate_Proxy', 'hypotheses/rejected/crypto_funding_proxy.md', 'Perpetual Funding', 'Crypto', 'Long/Short',
 2.0, 65, 'rejected',
 '3-day price move proxy failed: 50% win rate. Needs actual exchange funding rate data', '2026-02-10', 0.60, 50.0,
 'Funding rate pressure not captured by simple price moves. Requires Binance/Bybit API.'),

('Random_Walk_Breakout', 'hypotheses/rejected/random_walk_breakout.md', 'Technical Analysis', 'Equities', 'Long',
 0.8, 52, 'rejected',
 'No edge found: indistinguishable from random', '2026-01-20', 0.42, 48.5,
 'Extensive testing showed no statistical significance. Abandoned early.'),

('Social_Media_Sentiment_Levels', 'hypotheses/rejected/social_levels.md', 'Alternative Data', 'Equities', 'Long/Short',
 1.0, 55, 'rejected',
 'Sentiment levels not predictive; momentum of sentiment works but not levels', '2026-01-25', 0.55, 51.0,
 'Refined to Retail Order Flow Imbalance (sentiment changes, not levels).'),

('IPO_First_Day_Momentum', 'hypotheses/rejected/ipo_first_day.md', 'IPO Underpricing', 'Equities', 'Long',
 1.5, 60, 'rejected',
 'Data availability issues; high borrow costs; execution impossible at scale', '2026-01-15', NULL, NULL,
 'Practical constraints prevent systematic implementation. Rejected before full backtest.')

ON CONFLICT (hypothesis_name) DO UPDATE SET
    current_status = 'rejected',
    rejection_reason = EXCLUDED.rejection_reason,
    rejected_date = EXCLUDED.rejected_date,
    backtest_sharpe_actual = EXCLUDED.backtest_sharpe_actual,
    backtest_win_rate_actual = EXCLUDED.backtest_win_rate_actual,
    notes = EXCLUDED.notes;

-- Create view for rejected hypotheses
CREATE OR REPLACE VIEW openclaw_researcher.v_rejected_hypotheses AS
SELECT 
    hypothesis_name,
    academic_basis,
    asset_class,
    target_sharpe,
    target_win_rate,
    backtest_sharpe_actual,
    backtest_win_rate_actual,
    rejection_reason,
    rejected_date,
    notes
FROM openclaw_researcher.hypothesis_registry
WHERE current_status = 'rejected'
ORDER BY rejected_date DESC;

-- Create view for hypothesis lifecycle summary
CREATE OR REPLACE VIEW openclaw_researcher.v_hypothesis_lifecycle AS
SELECT 
    current_status,
    COUNT(*) as count,
    ROUND(AVG(target_sharpe), 2) as avg_target_sharpe,
    MIN(target_sharpe) as min_target_sharpe,
    MAX(target_sharpe) as max_target_sharpe
FROM openclaw_researcher.hypothesis_registry
GROUP BY current_status
ORDER BY 
    CASE current_status
        WHEN 'idea' THEN 1
        WHEN 'testing' THEN 2
        WHEN 'validated' THEN 3
        WHEN 'rejected' THEN 4
        WHEN 'promoted' THEN 5
    END;

-- Create function to reject a hypothesis
CREATE OR REPLACE FUNCTION openclaw_researcher.reject_hypothesis(
    p_hypothesis_name VARCHAR,
    p_reason TEXT,
    p_actual_sharpe DECIMAL DEFAULT NULL,
    p_actual_win_rate DECIMAL DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE openclaw_researcher.hypothesis_registry
    SET current_status = 'rejected',
        rejection_reason = p_reason,
        rejected_date = CURRENT_DATE,
        backtest_sharpe_actual = p_actual_sharpe,
        backtest_win_rate_actual = p_actual_win_rate
    WHERE hypothesis_name = p_hypothesis_name;
    
    RAISE NOTICE 'Hypothesis % rejected: %', p_hypothesis_name, p_reason;
END;
$$ LANGUAGE plpgsql;

-- Create function to get rejection statistics
CREATE OR REPLACE FUNCTION openclaw_researcher.get_rejection_analysis()
RETURNS TABLE (
    total_rejected BIGINT,
    avg_target_sharpe NUMERIC,
    avg_actual_sharpe NUMERIC,
    common_reasons TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_rejected,
        ROUND(AVG(target_sharpe), 2) as avg_target_sharpe,
        ROUND(AVG(backtest_sharpe_actual), 2) as avg_actual_sharpe,
        STRING_AGG(DISTINCT 
            CASE 
                WHEN rejection_reason LIKE '%win rate%' THEN 'Low Win Rate'
                WHEN rejection_reason LIKE '%delisted%' THEN 'Data Unavailable'
                WHEN rejection_reason LIKE '%zero lag%' THEN 'No Edge Found'
                WHEN rejection_reason LIKE '%proxy failed%' THEN 'Proxy Inadequate'
                ELSE 'Other'
            END, ', '
        ) as common_reasons
    FROM openclaw_researcher.hypothesis_registry
    WHERE current_status = 'rejected';
END;
$$ LANGUAGE plpgsql;
