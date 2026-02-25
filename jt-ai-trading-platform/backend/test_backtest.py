#!/usr/bin/env python3
"""Test backtest engine"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

from app.services.backtest_engine import BacktestEngine
import asyncio

engine = BacktestEngine()

# Run backtest directly
result = asyncio.run(engine.run_backtest(
    strategy_id=22,
    start_date="2024-06-01",
    end_date="2024-07-01",
    initial_capital=10000
))

print("Result:", result)