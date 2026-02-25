-- SQL to Classify 14 Unclassified US Stocks
-- Run this to expand universe from 179 to 193 tickers
-- IMPORTANT: SMCI is classified but has no data - should be unclassified or data imported

-- First, remove SMCI from Tech (it has no data)
DELETE FROM gold.stock_metrics WHERE ticker = 'SMCI';

-- Tech Sector (7 tickers)
INSERT INTO gold.stock_metrics (ticker, sector, date, rsi_14) VALUES
('AVGO', 'Tech', CURRENT_DATE, NULL),
('MDB', 'Tech', CURRENT_DATE, NULL),
('NFLX', 'Tech', CURRENT_DATE, NULL),
('SHOP', 'Tech', CURRENT_DATE, NULL),
('TWLO', 'Tech', CURRENT_DATE, NULL),
('VEEV', 'Tech', CURRENT_DATE, NULL),
('ZM', 'Tech', CURRENT_DATE, NULL);

-- Equity Sector (7 tickers)
INSERT INTO gold.stock_metrics (ticker, sector, date, rsi_14) VALUES
('C', 'Equity', CURRENT_DATE, NULL),
('DOCU', 'Equity', CURRENT_DATE, NULL),
('IBM', 'Equity', CURRENT_DATE, NULL),
('LCID', 'Equity', CURRENT_DATE, NULL),
('LYFT', 'Equity', CURRENT_DATE, NULL),
('PINS', 'Equity', CURRENT_DATE, NULL),
('UBER', 'Equity', CURRENT_DATE, NULL);

-- Verify insert
SELECT sector, COUNT(*) as count 
FROM gold.stock_metrics 
WHERE sector IS NOT NULL
GROUP BY sector;

-- Expected result after fix:
-- Tech: 36 (was 30, removed SMCI, added 7 = 36)
-- Equity: 156 (was 149, added 7 = 156)
-- Total: 192 tickers

-- Note: If you want to keep SMCI, import its data first:
-- Request JT to import SMCI historical data
