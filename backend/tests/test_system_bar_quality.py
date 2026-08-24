import requests

BASE_URL = "http://localhost:8000"


def test_system_freshness_bar_quality():
    """GET /api/system/freshness carries a bar_quality section sourced from
    gold.v_us_equity_bar_quality (qr_etl, t_d97f3b82 / t_285be732).

    Contract: section present; when the view exists it reports quality
    GREEN/YELLOW (never a hard failure), latest_suspect_date, 30d row count,
    distinct tickers, and per-layer recent splits. Degrades to None only if
    the view is missing.
    """
    print("--- TESTING SYSTEM FRESHNESS BAR QUALITY ---")
    res = requests.get(f"{BASE_URL}/api/system/freshness", timeout=15)
    assert res.status_code == 200, f"status {res.status_code}"
    data = res.json()

    assert "bar_quality" in data, "bar_quality key missing from response"
    bq = data["bar_quality"]
    assert bq is not None, "bar_quality is None — view gold.v_us_equity_bar_quality missing?"

    assert bq["quality"] in ("GREEN", "YELLOW"), f"unexpected quality {bq['quality']}"
    assert isinstance(bq["total_rows"], int) and bq["total_rows"] >= 0
    assert isinstance(bq["recent_30d_rows"], int) and bq["recent_30d_rows"] >= 0
    assert isinstance(bq["distinct_tickers"], int) and bq["distinct_tickers"] >= 0
    assert isinstance(bq["recent_30d_tickers"], list)
    # Recent-row accounting must reconcile with the per-layer split.
    assert bq["recent_30d_gold_rows"] + bq["recent_30d_quarantined_rows"] == bq["recent_30d_rows"], (
        f"layer split {bq['recent_30d_gold_rows']}+{bq['recent_30d_quarantined_rows']} "
        f"!= recent_30d_rows {bq['recent_30d_rows']}"
    )
    # YELLOW iff unresolved suspects in the last 30d.
    assert (bq["quality"] == "YELLOW") == (bq["recent_30d_rows"] > 0)
    # Sources section still intact (may be None on degraded registry).
    assert "sources" in data
    print(f"[PASS] bar_quality: quality={bq['quality']} latest={bq['latest_suspect_date']} "
          f"total={bq['total_rows']} recent30d={bq['recent_30d_rows']} "
          f"tickers={bq['recent_30d_tickers']}")
