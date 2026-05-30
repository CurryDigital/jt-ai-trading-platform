"""
Tests for the backtest engine and endpoints.

Run with:
    cd jt-ai-trading-platform/backend
    python -m pytest tests/test_backtest.py -v
"""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# We need to import the app; handle path issues
import sys
sys.path.insert(0, "/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend")

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_backtest_engine():
    """Patch the backtest engine singleton."""
    with patch("app.services.backtest_engine.backtest_engine") as mock:
        yield mock


@pytest.fixture(autouse=True)
def patch_imports():
    """Ensure routes module can import backtest_engine."""
    with patch.dict("sys.modules", {"app.services.backtest_engine": MagicMock()}):
        yield


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

def test_backtest_request_endpoint(mock_backtest_engine):
    """POST /api/backtest/request should accept a backtest request."""
    mock_backtest_engine.request_backtest.return_value = {
        "request_id": "bt-test123",
        "strategy_id": "S-20260227-004",
        "strategy_name": "DEFENSIVE_ROTATION_RISK_OFF",
        "status": "REQUESTED",
        "message": "Backtest request accepted.",
    }

    payload = {
        "strategy_id": "S-20260227-004",
        "strategy_name": "DEFENSIVE_ROTATION_RISK_OFF",
        "asset_class": "Equity",
        "direction": "LONG",
        "time_horizon": "SHORT_TERM",
        "venue": "US_EQUITY",
    }

    response = client.post("/api/backtest/request", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REQUESTED"
    assert data["strategy_id"] == "S-20260227-004"
    mock_backtest_engine.request_backtest.assert_called_once()


def test_backtest_status_endpoint(mock_backtest_engine):
    """GET /api/backtest/{request_id}/status should return status."""
    mock_backtest_engine.get_request_status.return_value = {
        "request_id": "bt-test123",
        "strategy_id": "S-20260227-004",
        "status": "COMPLETED",
        "result": {"aggregated": {"avg_win_rate": 0.62}},
    }

    response = client.get("/api/backtest/bt-test123/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["request_id"] == "bt-test123"


def test_backtest_status_not_found(mock_backtest_engine):
    """GET /api/backtest/{request_id}/status should 404 for unknown IDs."""
    mock_backtest_engine.get_request_status.return_value = None

    response = client.get("/api/backtest/bt-unknown/status")
    assert response.status_code == 404


def test_backtest_history_endpoint(mock_backtest_engine):
    """GET /api/backtest/strategy/{strategy_id}/history should return history."""
    mock_backtest_engine.get_backtest_history.return_value = [
        {
            "request_id": "bt-1",
            "strategy_id": "S-20260227-004",
            "status": "COMPLETED",
            "result": {},
        }
    ]

    response = client.get("/api/backtest/strategy/S-20260227-004/history")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "S-20260227-004"
    assert data["backtest_count"] == 1


def test_backtest_vs_live_endpoint(mock_backtest_engine):
    """GET /api/backtest/strategy/{strategy_id}/vs-live should return comparison."""
    mock_backtest_engine.compare_backtest_vs_live.return_value = {
        "strategy_id": "S-20260227-004",
        "backtest": {"avg_win_rate": 0.62},
        "live": {"total_pnl": 1250.0, "active_positions": 3},
    }

    response = client.get("/api/backtest/strategy/S-20260227-004/vs-live")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "S-20260227-004"
    assert "backtest" in data
    assert "live" in data


def test_legacy_backtest_endpoint(mock_backtest_engine):
    """POST /api/strategies/{strategy_id}/backtest should queue a backtest."""
    mock_backtest_engine.run_backtest.return_value = {"status": "COMPLETED"}

    with patch("app.routes.backtest.safe_query_one") as mock_query:
        mock_row = MagicMock()
        mock_row.name = "DEFENSIVE_ROTATION_RISK_OFF"
        mock_query.return_value = mock_row

        payload = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000,
            "commission_rate": 0.001,
        }
        response = client.post("/api/strategies/S-20260227-004/backtest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["strategy_id"] == "S-20260227-004"


# ---------------------------------------------------------------------------
# Engine unit tests
# ---------------------------------------------------------------------------

def test_aggregate_results_empty():
    """_aggregate_results should return empty dict for no results."""
    from app.services.backtest_engine import BacktestEngine
    engine = BacktestEngine.__new__(BacktestEngine)
    assert engine._aggregate_results({}) == {}


def test_aggregate_results_with_data():
    """_aggregate_results should compute averages correctly."""
    from app.services.backtest_engine import BacktestEngine
    engine = BacktestEngine.__new__(BacktestEngine)
    results = {
        "AAPL": {
            "total_return": 10.0,
            "sharpe_ratio": 1.5,
            "win_rate": 0.6,
            "max_drawdown": 5.0,
            "num_trades": 20,
        },
        "MSFT": {
            "total_return": 20.0,
            "sharpe_ratio": 2.0,
            "win_rate": 0.7,
            "max_drawdown": 3.0,
            "num_trades": 30,
        },
    }
    agg = engine._aggregate_results(results)
    assert agg["tickers_tested"] == 2
    assert agg["avg_total_return"] == 15.0
    assert agg["avg_sharpe_ratio"] == 1.75
    assert agg["avg_win_rate"] == 0.65
    assert agg["total_trades"] == 50


def test_serialize_backtest_result():
    """_serialize_backtest_result should produce a JSON-safe dict."""
    from app.services.backtest_engine import BacktestEngine
    from app.core_logic.backtesting.strategy_backtester import BacktestResult

    engine = BacktestEngine.__new__(BacktestEngine)
    result = BacktestResult(
        total_return=12.5,
        sharpe_ratio=1.8,
        max_drawdown=3.2,
        win_rate=0.65,
        profit_factor=2.1,
        avg_trade_return=1.2,
        num_trades=50,
        winning_trades=32,
        losing_trades=18,
        trades=[],
        equity_curve=[100000, 101000],
        monthly_returns={},
    )
    serialized = engine._serialize_backtest_result(result, "mean_reversion")
    assert serialized["strategy_name"] == "mean_reversion"
    assert serialized["total_return"] == 12.5
    assert serialized["num_trades"] == 50
    # Verify JSON serializable
    json.dumps(serialized)
