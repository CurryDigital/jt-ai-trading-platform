-- Migration: 2026-08-24_fix_v_paper_open_positions_perf.sql
-- Task: t_87ccf8a4 — Paper tab endpoints starve under concurrent mount fan-out
--
-- Root cause: gold.v_paper_open_positions computed latest prices via
--   SELECT DISTINCT ON (ticker) ... FROM silver.unified_prices (897MB, 2.2M rows)
-- which forces a seq scan + 66MB external disk sort (~11-20s per call) even
-- though only ~105 open-position tickers are needed. Two concurrent mounts of
-- this view (open-positions + open-positions-pnl) saturated the pool.
--
-- Fix: LEFT JOIN LATERAL per-position index lookup against the existing
-- unique index unified_prices_new_ticker_date_key (ticker, date).
-- Column list and order preserved exactly (CREATE OR REPLACE compatible).

CREATE OR REPLACE VIEW gold.v_paper_open_positions AS
SELECT p.strategy_id,
    p.ticker AS instrument,
    p.ticker,
    lower(p.direction) AS direction,
    p.n_shares AS size,
    p.n_shares::integer AS n_shares,
    p.entry_price,
    COALESCE(lp.latest_close, p.entry_price) AS current_price,
    CASE
        WHEN lower(p.direction) = 'long'::text AND p.entry_price > 0::numeric THEN (COALESCE(lp.latest_close, p.entry_price) - p.entry_price) / p.entry_price * 100::numeric
        WHEN lower(p.direction) = 'short'::text AND p.entry_price > 0::numeric THEN (p.entry_price - COALESCE(lp.latest_close, p.entry_price)) / p.entry_price * 100::numeric
        ELSE NULL::numeric
    END AS unrealised_pnl_pct,
    CASE
        WHEN p.n_shares IS NOT NULL AND p.entry_price > 0::numeric THEN (COALESCE(lp.latest_close, p.entry_price) - p.entry_price) * p.n_shares
        ELSE NULL::numeric
    END AS unrealised_pnl_usd,
    p.entry_date,
    CURRENT_DATE - p.entry_date AS days_held,
    p.status,
    CASE
        WHEN lp.latest_close IS NOT NULL THEN 'eod_proxy'::text
        ELSE 'live'::text
    END AS price_source,
    lp.price_date AS price_as_of
FROM gold.paper_trades_synthetic p
LEFT JOIN LATERAL (
    SELECT up.close AS latest_close,
           up.date  AS price_date
    FROM silver.unified_prices up
    WHERE up.ticker = p.ticker::character varying
      AND up.close IS NOT NULL
    ORDER BY up.date DESC
    LIMIT 1
) lp ON true
WHERE p.status = 'open'::text
  AND EXISTS (SELECT 1
              FROM gold.strategy_paper_monitoring pm
              WHERE pm.strategy_id = p.strategy_id AND pm.is_active = true);
