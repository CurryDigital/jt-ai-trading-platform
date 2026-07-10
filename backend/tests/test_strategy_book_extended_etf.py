import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient
from app.main_compact import app


client = TestClient(app)


def _has_realistic_metrics(s, context):
    """Assert a strategy has non-null OOS metrics and realistic ranges."""
    errors = []
    for field in ["sharpe_ratio", "returns", "win_rate", "max_drawdown", "trade_count", "profit_factor"]:
        if s.get(field) is None:
            errors.append(f"{context}.{field} is null")
    if s.get("profit_factor") is not None and s["profit_factor"] <= 0:
        errors.append(f"{context}.profit_factor non-positive: {s['profit_factor']}")
    if s.get("sharpe_ratio") is not None and s["sharpe_ratio"] < 0:
        errors.append(f"{context}.sharpe_ratio negative: {s['sharpe_ratio']}")
    if s.get("win_rate") is not None and not (0 <= s["win_rate"] <= 1):
        errors.append(f"{context}.win_rate out of range: {s['win_rate']}")
    return errors


def test_paper_strategy_book_extended_returns_realistic_etf_metrics():
    """Real DB endpoint: all approved ETF strategies must have non-null, realistic OOS metrics."""
    response = client.get("/api/paper/strategy-book-extended")
    assert response.status_code == 200, f"status={response.status_code}"
    data = response.json()
    assert "strategies" in data
    etfs = [s for s in data["strategies"] if s.get("asset_class") == "ETF" and s.get("status") == "approved"]
    assert len(etfs) >= 10, f"expected >=10 approved ETF strategies, got {len(etfs)}"

    all_errors = []
    for s in etfs:
        all_errors.extend(_has_realistic_metrics(s, f"{s.get('strategy_id')}({s.get('name')})"))
    assert not all_errors, "\n".join(all_errors)


def test_paper_strategy_book_extended_payload_contains_new_fields():
    """The extended payload must include returns, max_drawdown, trade_count, profit_factor, live fields."""
    response = client.get("/api/paper/strategy-book-extended")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    s = data["strategies"][0]
    for field in [
        "returns", "max_drawdown", "trade_count", "turnover", "profit_factor", "cvar_95",
        "live_pnl", "live_win_rate", "live_trades",
    ]:
        assert field in s, f"missing field {field}"
