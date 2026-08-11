import requests
import sys

BASE_URL = "http://localhost:8000"

def test_strategy_evaluation_trades_expansion():
    print("--- TESTING STRATEGY TRADES ROUND-TRIP EXPANSION ---")
    sid = "HK_Quality_BlueChips"
    try:
        # Default limit (50) should still work.
        res = requests.get(f"{BASE_URL}/api/strategies/{sid}/evaluation", timeout=15)
        assert res.status_code == 200, f"status {res.status_code}"
        data = res.json()
        sides = [t.get("side") for t in data.get("recent_trades", [])]
        assert "BUY" in sides and "SELL" in sides, f"expected both BUY and SELL sides, got {set(sides)}"
        assert len(data["recent_trades"]) <= 50, "default trade_limit exceeded"

        # Request larger limit and confirm we can retrieve full history.
        res = requests.get(f"{BASE_URL}/api/strategies/{sid}/evaluation?trade_limit=500", timeout=15)
        assert res.status_code == 200, f"status {res.status_code}"
        data_large = res.json()
        assert len(data_large["recent_trades"]) >= len(data["recent_trades"]), "trade_limit did not increase coverage"
        # Every SELL should have a matching BUY ticker somewhere in the list.
        buy_tickers = {t["ticker"] for t in data_large["recent_trades"] if t.get("side") == "BUY"}
        sell_tickers = {t["ticker"] for t in data_large["recent_trades"] if t.get("side") == "SELL"}
        assert sell_tickers.issubset(buy_tickers), "a SELL ticker has no corresponding BUY in the ledger"
        print(f"[PASS] Trades expansion for {sid}: buy_tickers={len(buy_tickers)}, sell_tickers={len(sell_tickers)}, total_events={len(data_large['recent_trades'])}")
    except Exception as e:
        print(f"[FAIL] Trades expansion: {e}")


def test_strategy_evaluation():
    print("--- TESTING STRATEGY EVALUATION ---")
    sid = "HK_Quality_BlueChips"
    try:
        res = requests.get(f"{BASE_URL}/api/strategies/{sid}/evaluation", timeout=15)
        assert res.status_code == 200, f"status {res.status_code}"
        data = res.json()
        assert data.get("strategy_id") == sid, "strategy_id mismatch"
        assert data.get("name"), "name missing"
        assert data.get("entry_logic"), "entry_logic missing"
        assert data.get("exit_logic"), "exit_logic missing"
        assert len(data.get("universe", [])) > 0, "universe empty"
        assert len(data.get("recent_signals", [])) > 0, "signals empty"
        assert data.get("metrics", {}).get("backtest") is not None, "backtest metrics missing"
        assert data.get("metrics", {}).get("live") is not None, "live metrics missing"
        print(f"[PASS] Strategy evaluation for {sid}: {data['name']}, universe={len(data['universe'])}, signals={len(data['recent_signals'])}, trades={len(data['recent_trades'])}")
    except Exception as e:
        print(f"[FAIL] Strategy evaluation: {e}")

def test_news_outlook():
    print("--- TESTING NEWS OUTLOOK (LLM layer) ---")
    try:
        res = requests.get(f"{BASE_URL}/api/news/outlook", timeout=15)
        assert res.status_code == 200, f"status {res.status_code}"
        payload = res.json()
        data = payload.get("data", {})
        assert "outlooks" in data and "clusters" in data, "missing outlooks/clusters keys"
        # When the table is populated, expect the 5 category outlooks and
        # per-category cluster assessments keyed by cluster_key.
        if data.get("run_date"):
            outlooks = data["outlooks"]
            clusters = data["clusters"]
            assert set(outlooks) == {"US", "HK", "CRYPTO", "FX", "METAL"}, f"outlook categories: {set(outlooks)}"
            for cat, o in outlooks.items():
                assert o.get("bias") in ("bullish", "bearish", "neutral", "mixed"), f"{cat} bias: {o.get('bias')}"
                assert o.get("rationale"), f"{cat} missing rationale"
                assert o.get("horizon") in ("intraday", "1w", "1m"), f"{cat} horizon: {o.get('horizon')}"
                assert o.get("confidence") is None or 0 <= o["confidence"] <= 1, f"{cat} confidence out of range"
            for cat, by_key in clusters.items():
                for k, c in by_key.items():
                    assert len(k) == 16, f"cluster_key not sha1-16: {k}"
                    assert c.get("bias"), f"{cat}/{k} missing bias"
            # Join check: digest stories carry cluster_key and at least one LLM
            # cluster row joins onto a digest story.
            dg = requests.get(f"{BASE_URL}/api/news/digest?per_group=120&key_limit=8", timeout=30).json()
            joined = 0
            for cat, catdata in dg.get("categories", {}).items():
                assert all("cluster_key" in s for s in catdata.get("stories", [])), f"{cat} story missing cluster_key"
                keys = {s["cluster_key"] for s in catdata.get("stories", [])}
                joined += len(keys & set(clusters.get(cat, {}).keys()))
            assert joined > 0, "no LLM cluster row joins onto any digest story"
            print(f"[PASS] News outlook: run_date={data['run_date']}, outlooks={len(outlooks)}, cluster_rows={sum(len(v) for v in clusters.values())}, digest_joined={joined}")
        else:
            print("[PASS] News outlook: table empty/missing — degraded gracefully (empty maps, HTTP 200)")
    except Exception as e:
        print(f"[FAIL] News outlook: {e}")

def test_backend():
    print("--- TESTING BACKEND API ---")
    
    # 1. Test Status
    try:
        res = requests.get(f"{BASE_URL}/api/status")
        print(f"[PASS] Status: {res.json()}")
    except Exception as e:
        print(f"[FAIL] Status: {e}")
        return

    # 2. Test Projects
    try:
        res = requests.get(f"{BASE_URL}/api/projects")
        print(f"[PASS] Projects found: {len(res.json())}")
    except Exception as e:
        print(f"[FAIL] Projects: {e}")

    # 3. Test Deep Dive Analysis (Search)
    print("Testing AI Deep Dive (this may take 10s)...")
    try:
        res = requests.get(f"{BASE_URL}/api/analyze/0700.HK")
        if res.status_code == 200:
            print(f"[PASS] Analysis for 0700.HK: {res.json()['recommendation']} (Score: {res.json()['confidence']})")
        else:
            print(f"[FAIL] Analysis failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[FAIL] Analysis: {e}")

    # 4. Test Strategy Detail page data source
    test_strategy_evaluation()
    test_strategy_evaluation_trades_expansion()

    # 5. Test News outlook LLM layer
    test_news_outlook()

if __name__ == "__main__":
    test_backend()
