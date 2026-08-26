"""Tests for /api/performance/strategy summary honesty contract (t_2bf12279).

summary must return null (never placeholder 0) for metrics with no
portfolio-level measurement: sharpe, max_drawdown, total_return.
win_rate / total_trades come from real trade-weighted aggregates over
consumption.Performance_Strategy_Attribution; null when that source is absent.
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


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_summary_nulls_when_attribution_absent(mock_safe, mock_one):
    """Attribution table missing/empty -> every summary metric is None."""
    mock_safe.return_value = []
    mock_one.return_value = None

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200
    s = r.json()["summary"]
    assert s["win_rate"] is None
    assert s["total_trades"] is None
    assert s["sharpe"] is None
    assert s["max_drawdown"] is None
    assert s["total_return"] is None


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_summary_real_aggregates_when_present(mock_safe, mock_one):
    """Measured attribution -> win_rate/total_trades populated; the rest null."""
    mock_safe.return_value = []
    mock_one.return_value = _make_row(win_rate=0.5579, total_trades=2187)

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200
    s = r.json()["summary"]
    assert abs(s["win_rate"] - 0.5579) < 1e-9
    assert s["total_trades"] == 2187
    assert s["sharpe"] is None
    assert s["max_drawdown"] is None
    assert s["total_return"] is None


@patch("app.routes.performance.safe_query_one")
@patch("app.routes.performance.safe_query")
def test_summary_no_zero_placeholders(mock_safe, mock_one):
    """Regression guard: summary must never contain hardcoded 0 metrics."""
    mock_safe.return_value = []
    mock_one.return_value = _make_row(win_rate=None, total_trades=None)

    r = client.get("/api/performance/strategy")
    assert r.status_code == 200
    s = r.json()["summary"]
    for key in ("win_rate", "sharpe", "max_drawdown", "total_return", "total_trades"):
        assert s[key] is None or s[key] != 0, f"{key} is a placeholder zero"
