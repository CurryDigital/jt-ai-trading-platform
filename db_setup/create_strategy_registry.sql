-- Strategy Registry - canonical source of truth from OpenClaw pipeline
-- Maps to StrategyRegistry model in backend/app/db/session.py
-- Run: psql -h $DB_HOST -U openclaw_user -d aitrading -f create_strategy_registry.sql

CREATE TABLE IF NOT EXISTS gold.strategy_registry (
    strategy_id VARCHAR(10) PRIMARY KEY,
    strategy_name VARCHAR(100),
    version VARCHAR(10),
    status VARCHAR(20) DEFAULT 'TESTING',
    priority VARCHAR(20) DEFAULT 'EXPERIMENTAL',
    win_rate DECIMAL(5,2),
    entry_logic TEXT,
    exit_logic TEXT,
    target_assets TEXT
);

ALTER TABLE gold.strategy_registry OWNER TO openclaw_user;

CREATE INDEX IF NOT EXISTS idx_strategy_registry_status ON gold.strategy_registry (status);
CREATE INDEX IF NOT EXISTS idx_strategy_registry_priority ON gold.strategy_registry (priority);
