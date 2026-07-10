"""Tests for /api/strategies/researcher OOS metric source of truth."""
import os
import sys

# Ensure backend package is importable from the test location
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy import text

from app.main_compact import app
from app.db import safe_query


client = TestClient(app)


def _make_row(**kwargs):
    """Return a lightweight object with attributes from kwargs."""
    return type("Row", (), kwargs)()


@patch("app.routes.strategies.safe_query")
@patch("app.routes.strategies.safe_query_one")
def test_researcher_uses_latest_backtest_for_oos(mock_one, mock_safe, monkeypatch):
    """OOS metrics should come from the latest strategy_backtest_runs row,
    not the stale strategy_registry snapshot."""
    # Registry row with stale/zero OOS values
    registry_row = _make_row(
        id="ETF_TEST",
        name="Test ETF",
        asset_class="EQUITY",
        universe_tickers="SPY,QQQ",
        execution_mode="SIMULATION",
        status="RESEARCH",
        sharpe_oos=0.10,
        max_drawdown_oos=-0.20,
        trade_count_oos=5,
        win_rate_oos=0.40,
        conviction_score=6.0,
        assigned_capital=None,
        in_market_capital=None,
        signal_logic="momentum",
        exit_logic="stop",
        priority="GOLDEN",
    )

    # Latest backtest row with different (newer) OOS values
    backtest_row = _make_row(
        strategy_id="ETF_TEST",
        pnl_2024=0.15,
        pnl_2025=0.22,
        pnl_2026=None,
        trade_count_oos=42,
        sharpe_oos=1.25,
        max_drawdown_oos=-0.08,
        win_rate_oos=0.62,
        returns_oos=0.19,
    )

    # No family signals needed for this assertion
    def _fake_safe_query(db, sql, params=None, label=None, fallback=None):
        sql_lower = sql.lower()
        if "strategy_registry" in sql_lower and "from gold.strategy_registry" in sql_lower:
            return [registry_row]
        if "strategy_backtest_runs" in sql_lower:
            return [backtest_row]
        if "strategy_signals" in sql_lower:
            return []
        if "strategy_families" in sql_lower:
            return []
        return fallback if fallback is not None else []

    mock_safe.side_effect = _fake_safe_query
    mock_one.return_value = None

    # Bypass cache so the mocked queries run
    response = client.get("/api/strategies/researcher?fresh=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    strat = data["strategies"][0]

    assert strat["id"] == "ETF_TEST"
    assert strat["trade_count_oos"] == 42
    assert strat["backtest_trades"] == 42
    assert strat["sharpe_ratio"] == 1.25
    assert strat["max_drawdown"] == -0.08
    assert strat["win_rate"] == 0.62
    assert strat["returns_oos"] == 0.19


@patch("app.routes.strategies.safe_query")
@patch("app.routes.strategies.safe_query_one")
def test_researcher_falls_back_to_registry_when_no_backtest(mock_one, mock_safe, monkeypatch):
    """If no backtest row exists, the endpoint should still return registry OOS values."""
    registry_row = _make_row(
        id="NO_BT",
        name="No Backtest Strategy",
        asset_class="EQUITY",
        universe_tickers="AAPL",
        execution_mode="SIMULATION",
        status="RESEARCH",
        sharpe_oos=0.55,
        max_drawdown_oos=-0.12,
        trade_count_oos=10,
        win_rate_oos=0.50,
        conviction_score=5.0,
        assigned_capital=None,
        in_market_capital=None,
        signal_logic="mean_rev",
        exit_logic="time",
        priority="NEAR_GOLDEN",
    )

    def _fake_safe_query(db, sql, params=None, label=None, fallback=None):
        sql_lower = sql.lower()
        if "strategy_registry" in sql_lower and "from gold.strategy_registry" in sql_lower:
            return [registry_row]
        if "strategy_backtest_runs" in sql_lower:
            return []
        if "strategy_signals" in sql_lower:
            return []
        if "strategy_families" in sql_lower:
            return []
        return fallback if fallback is not None else []

    mock_safe.side_effect = _fake_safe_query
    mock_one.return_value = None

    response = client.get("/api/strategies/researcher?fresh=1")
    assert response.status_code == 200
    data = response.json()
    strat = data["strategies"][0]

    assert strat["trade_count_oos"] == 10
    assert strat["sharpe_ratio"] == 0.55
    assert strat["max_drawdown"] == -0.12
    assert strat["win_rate"] == 0.50


@patch("app.routes.strategies.safe_query")
@patch("app.routes.strategies.safe_query_one")
def test_researcher_returns_priority_field(mock_one, mock_safe, monkeypatch):
    """The response should include the priority field from strategy_registry."""
    registry_row = _make_row(
        id="PRI_TEST",
        name="Priority Test",
        asset_class="EQUITY",
        universe_tickers="",
        execution_mode="SIMULATION",
        status="RESEARCH",
        sharpe_oos=0.0,
        max_drawdown_oos=0.0,
        trade_count_oos=0,
        win_rate_oos=0.0,
        conviction_score=None,
        assigned_capital=None,
        in_market_capital=None,
        signal_logic="",
        exit_logic="",
        priority="GOLDEN",
    )

    def _fake_safe_query(db, sql, params=None, label=None, fallback=None):
        sql_lower = sql.lower()
        if "strategy_registry" in sql_lower and "from gold.strategy_registry" in sql_lower:
            return [registry_row]
        if "strategy_backtest_runs" in sql_lower:
            return []
        if "strategy_signals" in sql_lower:
            return []
        if "strategy_families" in sql_lower:
            return []
        return fallback if fallback is not None else []

    mock_safe.side_effect = _fake_safe_query
    mock_one.return_value = None

    response = client.get("/api/strategies/researcher?fresh=1")
    assert response.status_code == 200
    strat = response.json()["strategies"][0]
    assert strat["priority"] == "GOLDEN"
