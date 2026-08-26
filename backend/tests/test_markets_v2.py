"""Smoke tests for the redesigned market-status endpoints.

Run with:
    cd jt-ai-trading-platform/backend
    python -m pytest tests/test_markets_v2.py -v
"""
import pytest
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, "/home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend")

from app.main import app

client = TestClient(app)


REQUIRED_INDEX_FIELDS = {
    "sym", "name", "region", "last", "change_pct", "spark",
    "change_1d", "change_1w", "change_1m", "change_ytd",
    "est_1d", "est_1w", "est_1m",
}


def test_markets_overview_smoke():
    """GET /api/markets/overview?regions=US,HK must return the new index fields."""
    response = client.get("/api/markets/overview?regions=US,HK")
    assert response.status_code == 200, response.text
    data = response.json()

    assert "indices" in data
    assert "breadth" in data
    assert "sentiment" in data
    assert "movers" in data
    assert "as_of" in data

    indices = data["indices"]
    assert "data" in indices
    assert isinstance(indices["data"], list)
    assert len(indices["data"]) >= 1, "expected at least one US/HK index row"

    regions_seen = set()
    for idx in indices["data"]:
        missing = REQUIRED_INDEX_FIELDS - set(idx.keys())
        assert not missing, f"index row {idx.get('sym')} missing fields: {missing}"
        regions_seen.add(idx.get("region"))

    assert {"US", "HK"}.issubset(regions_seen), f"expected US and HK regions, got {regions_seen}"


def test_markets_overview_single_region():
    """Single-region query must still return a valid index list."""
    response = client.get("/api/markets/overview?regions=US")
    assert response.status_code == 200, response.text
    data = response.json()
    assert all(i.get("region") == "US" for i in data["indices"]["data"])


def test_markets_indices_required_fields():
    """Direct /api/markets/indices must also include multi-timeframe fields."""
    response = client.get("/api/markets/indices?regions=US,HK")
    assert response.status_code == 200, response.text
    for idx in response.json()["data"]:
        missing = REQUIRED_INDEX_FIELDS - set(idx.keys())
        assert not missing, f"direct indices row {idx.get('sym')} missing: {missing}"
