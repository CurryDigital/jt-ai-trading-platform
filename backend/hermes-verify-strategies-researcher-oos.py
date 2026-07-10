"""Ad-hoc verification for /api/strategies/researcher OOS response shape."""
import sys

BACKEND_DIR = "/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend"
sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main_compact import app


def main():
    client = TestClient(app)
    r = client.get("/api/strategies/researcher?fresh=1")
    assert r.status_code == 200, f"expected 200, got {r.status_code}"
    payload = r.json()
    strategies = payload.get("strategies", [])
    count = payload.get("count", 0)
    assert len(strategies) == count, "count mismatch"
    assert count > 0, "expected at least one strategy"

    for strat in strategies:
        assert "trade_count_oos" in strat, f"missing trade_count_oos in {strat.get('id')}"
        assert "returns_oos" in strat, f"missing returns_oos in {strat.get('id')}"
        assert "sharpe_ratio" in strat, f"missing sharpe_ratio in {strat.get('id')}"
        assert "max_drawdown" in strat, f"missing max_drawdown in {strat.get('id')}"
        assert "win_rate" in strat, f"missing win_rate in {strat.get('id')}"

    print(f"OK: {count} strategies, all contain top-level OOS fields")


if __name__ == "__main__":
    main()
