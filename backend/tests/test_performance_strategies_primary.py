"""Tests for /api/performance/strategy strategies[] primary path (t_f25d9ea5).

The primary query on consumption.Performance_Strategy_Attribution must:
  1. match portfolio_type case-insensitively (table stores lowercase 'paper';
     the old `= 'PAPER'` predicate matched zero rows and silently forced the
     registry fallback forever);
  2. exclude junk/test rows (TEST_*, dummy_test_always_buy, manual_close) and
     zero-trade placeholder rows (their 0.000 metrics are ETL placeholders,
     not measured values);
  3. preserve None for absent metrics (e.g. contribution_pct is NULL for
     every row) instead of coercing to placeholder 0.0;
  4. expose `strategies_source` provenance ('attribution' | 'registry_fallback').
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_row(**kwargs):
    return type("Row", (), kwargs)()


def _route_by_label(rows_by_label):
    """safe_query side_effect: return rows for the given label, [] otherwise."""
    def fake(db, sql, params=None, label=None):
        return rows_by_label.get(label, [])
    return fake


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_primary_query_case_insensitive_and_junk_filtered(mock_safe, mock_one):
    """The primary SQL must LOWER() the portfolio_type predicate and carry
    the junk-row exclusions (regression guard against re-introducing
    `= 'PAPER'` or dropping the test-row filters)."""
    captured = {}

    def fake(db, sql, params=None, label=None):
        captured[label] = sql
        return []

    mock_safe.side_effect = fake
    mock_one.return_value = None

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200

    sql = captured["perf_attribution"]
    assert "LOWER(portfolio_type) = 'paper'" in sql
    assert "portfolio_type = 'PAPER'" not in sql.replace("LOWER(", "")
    assert "num_trades > 0" in sql
    assert "manual_close" in sql
    assert "dummy_test_always_buy" in sql
    assert "NOT ILIKE 'test%'" in sql


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_primary_rows_preserve_nulls_and_provenance(mock_safe, mock_one):
    """Attribution rows with NULL contribution/sharpe keep None (never 0.0),
    and the response marks strategies_source='attribution'."""
    attribution_rows = [
        _make_row(strategy_id="S001", strategy_name="High Vol Pullback",
                  allocation=5.26, contribution=None, returns=16.2938,
                  num_trades=365, win_rate=0.542, sharpe_ratio=0.586),
        _make_row(strategy_id="S019", strategy_name="SMA 50/200 Golden Cross",
                  allocation=50.0, contribution=None, returns=52.1,
                  num_trades=429, win_rate=0.559, sharpe_ratio=None),
    ]
    mock_safe.side_effect = _route_by_label({"perf_attribution": attribution_rows})
    mock_one.return_value = _make_row(win_rate=0.55, total_trades=794)

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200
    body = r.json()

    assert body["strategies_source"] == "attribution"
    assert len(body["strategies"]) == 2

    s0 = body["strategies"][0]
    assert s0["strategy_id"] == "S001"
    assert s0["contribution"] is None          # NULL stays NULL, not 0.0
    assert s0["returns"] == 16.2938
    assert s0["num_trades"] == 365
    assert abs(s0["win_rate"] - 0.542) < 1e-9
    assert s0["sharpe_ratio"] == 0.586

    s1 = body["strategies"][1]
    assert s1["sharpe_ratio"] is None          # NULL sharpe stays NULL
    assert s1["live_win_rate"] is None         # no live_stats join match
    assert s1["current_signal"] is None        # no signals join match
    assert s1["backtest_win_rate"] is None     # no backtests join match


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_fallback_marks_provenance_and_nulls(mock_safe, mock_one):
    """Empty primary -> registry fallback serves rows, marked
    strategies_source='registry_fallback', with null (not fabricated-zero)
    allocation/contribution/returns/sharpe."""
    fallback_rows = [
        _make_row(strategy_id="REG1", strategy_name="Registry Strat",
                  allocation=None, contribution=None, returns=None,
                  num_trades=0, win_rate=0.61, sharpe_ratio=None),
    ]
    mock_safe.side_effect = _route_by_label({"perf_attribution_fallback": fallback_rows})
    mock_one.return_value = None

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200
    body = r.json()

    assert body["strategies_source"] == "registry_fallback"
    assert len(body["strategies"]) == 1
    s = body["strategies"][0]
    assert s["allocation"] is None
    assert s["contribution"] is None
    assert s["returns"] is None
    assert s["sharpe_ratio"] is None
    assert abs(s["win_rate"] - 0.61) < 1e-9
