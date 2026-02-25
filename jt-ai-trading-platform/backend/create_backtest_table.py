#!/usr/bin/env python3
"""Create backtest table in database"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

from app.db.session import engine, Base, DB_HOST, DB_NAME, DB_USER, DB_PORT, get_auth_token
import psycopg2

# Create table using raw SQL (more reliable)
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=get_auth_token(),
    database=DB_NAME,
    sslmode='require'
)

cur = conn.cursor()

# Create table
cur.execute("""
CREATE TABLE IF NOT EXISTS gold.backtest_runs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER,
    run_date TIMESTAMPTZ DEFAULT NOW(),
    start_date DATE,
    end_date DATE,
    total_return_pct FLOAT,
    sharpe_ratio FLOAT,
    max_drawdown_pct FLOAT,
    win_rate FLOAT,
    total_trades INTEGER,
    avg_trade_return FLOAT,
    raw_results JSONB
);
""")

# Create indexes
cur.execute("CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON gold.backtest_runs(strategy_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_backtest_date ON gold.backtest_runs(run_date DESC);")

conn.commit()
cur.close()
conn.close()

print("✅ Backtest table created successfully")