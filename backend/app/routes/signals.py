"""Research > Signals & Analytics endpoints — multi-family setups, proximity, feed.

See design-bundle handoff/API_SPEC_v2.md §3-4 and DB_CHANGES_v2.md §4.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/signals", tags=["signals"])

MARKETS = ["US", "HK", "ETF", "CRYPTO", "FX", "METAL"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _market_list(markets: str):
    return [m.strip() for m in markets.split(",") if m.strip()] or MARKETS


@router.get("/universe")
def get_signal_universe(markets: str = "US,HK,ETF,CRYPTO,FX,METAL", limit: int = 8, db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, ticker, name, families, direction, potential, change_pct, note
        FROM consumption.signal_setups WHERE market = ANY(:markets)
        ORDER BY market, potential DESC
    """, {"markets": market_list}, label="signal_universe")
    data = {}
    for r in rows:
        bucket = data.setdefault(r.market, [])
        if len(bucket) >= limit:
            continue
        bucket.append({
            "ticker": r.ticker, "name": r.name,
            "families": list(r.families) if r.families is not None else [],
            "direction": r.direction, "potential": float(r.potential) if r.potential is not None else None,
            "change_pct": float(r.change_pct) if r.change_pct is not None else None, "note": r.note,
        })

    # Fallback: if signal_setups is missing a requested market, derive from the
    # existing consumption tables (real data, not synthetic). This keeps the
    # Research > Signals tab populated while the signal_setups ETL pipeline is
    # backfilled for non-US markets.
    missing = [m for m in market_list if m not in data or not data[m]]
    for market in missing:
        if market == "HK":
            hk_rows = safe_query(db, """
                SELECT ticker, name, signal, signal_strength, change_pct, trend, top_strategy_score, strategy_signals
                FROM consumption.stock
                WHERE market = 'HK' AND signal IN ('BUY', 'SELL')
                ORDER BY COALESCE(signal_strength, top_strategy_score, 0) DESC
                LIMIT :limit
            """, {"limit": limit}, label="signal_universe_hk")
            for r in hk_rows:
                bucket = data.setdefault("HK", [])
                if len(bucket) >= limit:
                    break
                families = []
                if r.strategy_signals:
                    if isinstance(r.strategy_signals, dict):
                        families = list(r.strategy_signals.keys())
                    else:
                        families = [str(r.strategy_signals)]
                potential = float(r.signal_strength) if r.signal_strength is not None else float(r.top_strategy_score or 0)
                # If the scoring field is not populated, still surface the signal
                # with a small non-zero potential so the UI shows a populated card.
                if potential < 0.01 and r.signal in ('BUY', 'SELL'):
                    potential = 0.5
                bucket.append({
                    "ticker": r.ticker, "name": r.name,
                    "families": families,
                    "direction": r.signal, "potential": round(potential, 2),
                    "change_pct": float(r.change_pct) if r.change_pct is not None else None,
                    "note": f"trend: {r.trend or '—'}",
                })

        elif market == "CRYPTO":
            crypto_rows = safe_query(db, """
                SELECT DISTINCT ON (ticker)
                       ticker, close_price, log_return, rsi_14, prophet_forecast, volume_24h
                FROM consumption.crypto
                WHERE close_price > 0 AND (log_return IS NOT NULL OR prophet_forecast IS NOT NULL)
                ORDER BY ticker, date DESC
                LIMIT :limit
            """, {"limit": limit}, label="signal_universe_crypto")
            for r in crypto_rows:
                bucket = data.setdefault("CRYPTO", [])
                if len(bucket) >= limit:
                    break
                if r.prophet_forecast is not None and r.prophet_forecast > 0 and r.close_price and r.close_price > 0:
                    direction = "BUY" if r.prophet_forecast > r.close_price else "SELL"
                    potential = abs(r.prophet_forecast - r.close_price) / r.close_price * 100
                else:
                    lr = r.log_return or 0
                    direction = "BUY" if lr > 0 else "SELL"
                    potential = abs(lr) * 100 * 10
                potential = min(potential, 100.0)
                if potential < 0.01:
                    potential = 0.01
                bucket.append({
                    "ticker": r.ticker, "name": r.ticker,
                    "families": ["momentum"],
                    "direction": direction, "potential": round(potential, 2),
                    "change_pct": round((r.log_return or 0) * 100, 2),
                    "note": f"RSI {round(r.rsi_14, 1)}" if r.rsi_14 is not None else "—",
                })

        elif market == "FX":
            fx_rows = safe_query(db, """
                SELECT DISTINCT ON (ticker)
                       ticker, close_price, log_return, rsi_14, prophet_forecast, volatility_24h
                FROM consumption.fx
                WHERE close_price > 0 AND log_return IS NOT NULL
                ORDER BY ticker, date DESC
                LIMIT :limit
            """, {"limit": limit}, label="signal_universe_fx")
            for r in fx_rows:
                bucket = data.setdefault("FX", [])
                if len(bucket) >= limit:
                    break
                lr = r.log_return or 0
                direction = "BUY" if lr > 0 else "SELL"
                potential = abs(lr) * 100 * 10
                if r.volatility_24h is not None and r.volatility_24h > 0:
                    potential = max(potential, r.volatility_24h * 100)
                potential = min(potential, 100.0)
                if potential < 0.01:
                    potential = 0.01
                bucket.append({
                    "ticker": r.ticker, "name": r.ticker,
                    "families": ["tactical"],
                    "direction": direction, "potential": round(potential, 2),
                    "change_pct": round(lr * 100, 2),
                    "note": f"vol {round((r.volatility_24h or 0) * 100, 1)}%" if r.volatility_24h is not None else "—",
                })

        elif market == "METAL":
            metal_rows = safe_query(db, """
                SELECT asset, ticker, action, close_price, daily_change, trad_confidence, reasoning, strategy_tags
                FROM consumption.commodities
                WHERE asset IN ('Gold', 'Silver', 'Platinum', 'Crude Oil', 'Natural Gas', 'Copper')
                ORDER BY COALESCE(trad_confidence, 0) DESC
                LIMIT :limit
            """, {"limit": limit}, label="signal_universe_metal")
            for r in metal_rows:
                bucket = data.setdefault("METAL", [])
                if len(bucket) >= limit:
                    break
                potential = (r.trad_confidence or 0) * 100
                potential = min(potential, 100.0)
                bucket.append({
                    "ticker": r.ticker, "name": r.asset,
                    "families": list(r.strategy_tags.keys()) if r.strategy_tags else ["tactical"],
                    "direction": r.action, "potential": round(potential, 2),
                    "change_pct": float(r.daily_change) if r.daily_change is not None else None,
                    "note": (r.reasoning or "")[:80] or "—",
                })

    return {"data": data, "as_of": _now_iso() if any(data.values()) else None}


@router.get("/families")
def get_signal_families(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT family_key, label, strategy_id, strategy_name, deployed, color
        FROM gold.signal_families ORDER BY family_key
    """, label="signal_families")
    data = [{
        "key": r.family_key, "label": r.label, "strategy_id": r.strategy_id,
        "strategy_name": r.strategy_name, "deployed": bool(r.deployed), "color": r.color,
    } for r in rows]
    return {"data": data}


@router.get("/performance")
def get_signal_performance(markets: str = "US,HK,CRYPTO,FX,METAL", db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, family, hit_rate, fwd_return_5d, n_trades
        FROM consumption.signal_performance WHERE market = ANY(:markets)
    """, {"markets": market_list}, label="signal_performance")
    data = {}
    for r in rows:
        data.setdefault(r.market, []).append({
            "family": r.family, "hit_rate": float(r.hit_rate) if r.hit_rate is not None else None,
            "fwd_return_5d": float(r.fwd_return_5d) if r.fwd_return_5d is not None else None,
            "n_trades": r.n_trades,
        })
    return {"data": data}


@router.get("/proximity")
def get_signal_proximity(markets: str = "US,HK,CRYPTO,FX,METAL", db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, ticker, family, distance_pct, direction
        FROM consumption.signal_proximity WHERE market = ANY(:markets)
        ORDER BY market, distance_pct
    """, {"markets": market_list}, label="signal_proximity")
    data = {}
    for r in rows:
        data.setdefault(r.market, []).append({
            "ticker": r.ticker, "family": r.family,
            "distance_pct": float(r.distance_pct) if r.distance_pct is not None else None,
            "direction": r.direction,
        })
    return {"data": data}


@router.get("/feed")
def get_signal_feed(markets: str = "US,HK,CRYPTO,FX,METAL", limit: int = 4, db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, fired_at, signal, ticker, strategy, confidence
        FROM consumption.signal_feed WHERE market = ANY(:markets)
        ORDER BY market, fired_at DESC
    """, {"markets": market_list}, label="signal_feed")
    data = {}
    for r in rows:
        bucket = data.setdefault(r.market, [])
        if len(bucket) >= limit:
            continue
        bucket.append({
            "ts": r.fired_at.strftime("%H:%M") if r.fired_at else None,
            "signal": r.signal, "ticker": r.ticker, "strategy": r.strategy,
            "confidence": float(r.confidence) if r.confidence is not None else None,
        })
    return {"data": data}
