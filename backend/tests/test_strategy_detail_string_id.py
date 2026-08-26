"""Live-server test: /api/strategies/{strategy_id}/detail accepts string registry IDs.

Regression coverage for kanban t_c00cc5a0 — the route previously declared
`strategy_id: int`, rejecting gold.strategy_registry string IDs (422).
Run with the backend up: .venv/bin/python -m pytest tests/test_strategy_detail_string_id.py -v
"""
import requests

BASE_URL = "http://localhost:8000"
SID = "etf_tsmom_basket_07"


def test_detail_accepts_string_strategy_id():
    res = requests.get(f"{BASE_URL}/api/strategies/{SID}/detail", timeout=15)
    assert res.status_code == 200, f"status {res.status_code}: {res.text[:200]}"
    data = res.json()
    s = data["strategy"]
    assert s["id"] == SID, f"strategy id mismatch: {s['id']}"
    assert s["in_market_capital"] is not None, "in_market_capital missing"
    assert s["assigned_capital"] is not None, "assigned_capital missing"
    assert s["execution_mode"], "execution_mode missing"


def test_detail_surfaces_open_paper_legs():
    res = requests.get(f"{BASE_URL}/api/strategies/{SID}/detail", timeout=15)
    assert res.status_code == 200
    data = res.json()
    assert data["open_legs_source"] == "gold.paper_trades_synthetic"
    assert data["open_legs_count"] == len(data["open_legs"])
    assert data["open_legs_count"] > 0, "expected open legs for etf_tsmom_basket_07"
    for leg in data["open_legs"]:
        assert leg["ticker"] and leg["ticker"] != "CASH"
        assert leg["n_shares"] is not None and leg["n_shares"] > 0
        assert leg["entry_price"] is not None and leg["entry_date"]
        assert leg["direction"] in ("LONG", "SHORT")


def test_detail_unknown_string_id_404s():
    res = requests.get(f"{BASE_URL}/api/strategies/definitely_not_a_strategy_zz/detail", timeout=15)
    assert res.status_code == 404, f"status {res.status_code}"
