"""CNN Fear & Greed Index fetcher.

CNN publishes a public JSON endpoint:
  https://production.dataviz.cnn.io/index/fearandgreed/graphdata

Response shape (truncated):
{
  "fear_and_greed": {
    "score": 55.0,
    "rating": "Neutral",
    "previous_close": 52.0,
    "previous_1_week": 48.0,
    "previous_1_month": 60.0,
    "previous_1_year": 45.0
  },
  "market_momentum_sp500": { "score": 52, "rating": "Neutral" },
  ...
}

We cache the result for 15 minutes to avoid hammering the endpoint.
"""
import time
import requests
from typing import Optional, Dict, Any

CNN_FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
CACHE_TTL_SECONDS = 900  # 15 minutes

# In-memory cache
_cache: Dict[str, Any] = {"data": None, "ts": 0}


def fetch_cnn_fear_greed(timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """Fetch latest CNN Fear & Greed Index. Returns dict with score/rating or None on failure."""
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < CACHE_TTL_SECONDS:
        return _cache["data"]

    try:
        resp = requests.get(CNN_FEAR_GREED_URL, timeout=timeout, headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; JTCML/1.0)"
        })
        resp.raise_for_status()
        payload = resp.json()

        fg = payload.get("fear_and_greed", {})
        result = {
            "score": int(fg.get("score", 50)),
            "rating": fg.get("rating", "Neutral"),
            "previous_close": fg.get("previous_close"),
            "previous_1_week": fg.get("previous_1_week"),
            "previous_1_month": fg.get("previous_1_month"),
            "previous_1_year": fg.get("previous_1_year"),
            "raw": payload,  # pass through full payload for extensibility
        }
        _cache["data"] = result
        _cache["ts"] = now
        return result
    except Exception:
        # Silently fail — caller should fall back to VIX-derived proxy
        return None


def get_fear_greed_label(score: int) -> str:
    """Map CNN-style score to sentiment label."""
    if score >= 75:
        return "Extreme Greed"
    if score >= 55:
        return "Greed"
    if score >= 45:
        return "Neutral"
    if score >= 25:
        return "Fear"
    return "Extreme Fear"
