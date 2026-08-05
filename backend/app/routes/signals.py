"""Research > Signals & Analytics endpoints — multi-family setups, proximity, feed.

See design-bundle handoff/API_SPEC_v2.md §3-4 and DB_CHANGES_v2.md §4.
"""
import json
import re

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/signals", tags=["signals"])

MARKETS = ["US", "HK", "ETF", "CRYPTO", "FX", "METAL"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _market_list(markets: str):
    return [m.strip() for m in markets.split(",") if m.strip()] or MARKETS


def _human_note(note):
    """Some ETL rows ship raw JSON blobs in note/reasoning — render them readable."""
    if not note or not note.strip().startswith("{"):
        return note
    try:
        d = json.loads(note)
    except (ValueError, TypeError):
        return note[:80]
    if not isinstance(d, dict):
        return note[:80]
    parts = [f"{k.replace('_', ' ')}: {v}" for k, v in d.items() if v is not None]
    return (" · ".join(parts) or "—")[:80]


def _crypto_base(ticker: str) -> str:
    """ADAUSDT / ADA-USD / ADAUSD all refer to the same asset — dedupe key."""
    t = (ticker or "").upper()
    for suf in ("USDT", "-USD", "USD"):
        if t.endswith(suf) and len(t) > len(suf):
            return t[: -len(suf)]
    return t


# --- Rotation-engine exit semantics (t_d44e5d60) -----------------------------
# build_rotation_signals SELL = "zero target weight / exit to CASH", never
# short conviction (verified by qr_research, t_ab8f7d94). The UI needs to tell
# those rows apart from genuine sell calls, so we surface the engine metadata
# embedded in `note` as structured fields.
_ROTATION_ENGINE = "build_rotation_signals"
# Notes can be truncated mid-JSON (~80-char ETL writes), so regex instead of
# json.loads. engine/config_rank/config_filter all appear early in the blob.
_CONFIG_FILTER_RE = re.compile(r'config_filter[\\"]*\s*:\s*[\\"]*([A-Za-z0-9_]+)')


def _rotation_filters(note):
    """Regime-filter names referenced by a rotation-engine note.

    Returns a set like {'hk2800_126d'}, {'None'} for an unfiltered rotation
    config, or None when the row did not come from the rotation engine.
    """
    if not note or _ROTATION_ENGINE not in note:
        return None
    return set(_CONFIG_FILTER_RE.findall(note)) or {"None"}


@router.get("/universe")
def get_signal_universe(markets: str = "US,HK,ETF,CRYPTO,FX,METAL", limit: int = 8, db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    # Forecast horizons (fwd_5d / fwd_20d / fwd_1q, signed percent) are a pending
    # qr_etl backfill on consumption.signal_setups — select them opportunistically
    # and degrade to the base columns until they exist (DB_CHANGES_v2.md §4).
    has_horizons = True
    try:
        rows = db.execute(text("""
            SELECT market, ticker, name, families, direction, potential, change_pct, note,
                   price, fwd_5d, fwd_20d, fwd_1q
            FROM consumption.signal_setups WHERE market = ANY(:markets)
            ORDER BY market, potential DESC
        """), {"markets": market_list}).fetchall()
    except ProgrammingError:
        db.rollback()
        has_horizons = False
        rows = safe_query(db, """
            SELECT market, ticker, name, families, direction, potential, change_pct, note, price
            FROM consumption.signal_setups WHERE market = ANY(:markets)
            ORDER BY market, potential DESC
        """, {"markets": market_list}, label="signal_universe")
    data = {}
    # --- Exit-to-cash / regime-off detection (t_d44e5d60) -------------------
    # Ground truth lives in gold.strategy_ticker_scores: rotation SELL rows
    # carry score = 0 (zero target weight = exit to cash), and a strategy whose
    # regime filter fails holds CASH score ~= 1.0 with no positive BUY weights.
    # Notes on signal_setups are unreliable (some ETL refreshes write NULL), so
    # detect structurally via the family -> strategy join instead.
    ts_rows = safe_query(db, """
        SELECT strategy_id, ticker, signal_action, score
        FROM gold.strategy_ticker_scores
    """, label="signal_universe_scores")
    zero_by_ticker = {}      # ticker -> {strategy_id, ...} with SELL at zero target weight
    strat_has_buy = set()    # strategies with at least one positive BUY weight
    strat_cash_full = set()  # strategies with CASH weight ~= 1.0
    for t in ts_rows:
        score = float(t.score) if t.score is not None else None
        if t.ticker == "CASH":
            if score is not None and score >= 0.99:
                strat_cash_full.add(t.strategy_id)
        elif t.signal_action == "BUY" and score is not None and score > 0:
            strat_has_buy.add(t.strategy_id)
        elif t.signal_action == "SELL" and (score is None or score == 0):
            zero_by_ticker.setdefault(t.ticker, set()).add(t.strategy_id)
    regime_off_strats = strat_cash_full - strat_has_buy
    for r in rows:
        # qr_etl misclassifies some HK-listed tickers (e.g. 2800.HK) as US —
        # reclassify by suffix until fixed upstream (knowledge/research_signals.md).
        market = r.market
        if market == "US" and (r.ticker or "").upper().endswith(".HK"):
            market = "HK"
        if market not in market_list:
            continue
        bucket = data.setdefault(market, [])
        if len(bucket) >= limit:
            continue
        # Family tags on signal_setups are imprecise (a 'trend'-tagged ticker
        # may come from a different strategy), so match on the ticker itself:
        # any strategy holding it at SELL/zero-weight makes this an exit row.
        zero_strats = zero_by_ticker.get(r.ticker, set())
        exit_to_cash = r.direction == "SELL" and bool(zero_strats)
        cash_strats = sorted(s for s in zero_strats if s in regime_off_strats)
        regime_off = exit_to_cash and bool(cash_strats)
        # Regime-filter name is a bonus when the engine note survives ETL.
        filters = _rotation_filters(r.note) or set()
        regime_filter = sorted(f for f in filters if f != "None")
        bucket.append({
            "ticker": r.ticker, "name": r.name,
            "families": list(r.families) if r.families is not None else [],
            "direction": r.direction, "potential": float(r.potential) if r.potential is not None else None,
            "change_pct": float(r.change_pct) if r.change_pct is not None else None,
            "price": float(r.price) if getattr(r, "price", None) is not None else None,
            "note": _human_note(r.note),
            "exit_to_cash": exit_to_cash,
            "regime_off": regime_off,
            "regime_filter": regime_filter[0] if (regime_off and regime_filter) else None,
            "cash_strategy": cash_strats if regime_off else [],
            "fwd_5d": float(r.fwd_5d) if has_horizons and r.fwd_5d is not None else None,
            "fwd_20d": float(r.fwd_20d) if has_horizons and r.fwd_20d is not None else None,
            "fwd_1q": float(r.fwd_1q) if has_horizons and r.fwd_1q is not None else None,
        })

    # Fallback: if signal_setups is missing a requested market, derive from the
    # existing consumption tables (real data, not synthetic). This keeps the
    # Research > Signals tab populated while the signal_setups ETL pipeline is
    # backfilled for non-US markets.
    missing = [m for m in market_list if m not in data or not data[m]]
    for market in missing:
        if market == "HK":
            hk_rows = safe_query(db, """
                SELECT ticker, name, signal, signal_strength, change_pct, trend, top_strategy_score, strategy_signals, price
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
                # No fake scores: when the scoring field isn't populated, send null —
                # the UI shows the row without a score rather than a misleading 0.50.
                if potential < 0.01:
                    potential = None
                bucket.append({
                    "ticker": r.ticker, "name": r.name,
                    "families": families,
                    "direction": r.signal,
                    "potential": round(potential, 2) if potential is not None else None,
                    "change_pct": float(r.change_pct) if r.change_pct is not None else None,
                    "price": float(r.price) if getattr(r, "price", None) is not None else None,
                    "note": f"trend: {r.trend or '—'}",
                })

        elif market == "CRYPTO":
            # Over-fetch then dedupe: consumption.crypto mixes ticker formats
            # (ADAUSDT vs ADA-USD) — keep the strongest row per base asset so the
            # card never shows conflicting BUY/SELL for the same coin.
            crypto_rows = safe_query(db, """
                SELECT DISTINCT ON (ticker)
                       ticker, close_price, log_return, rsi_14, prophet_forecast, volume_24h
                FROM consumption.crypto
                WHERE close_price > 0 AND (log_return IS NOT NULL OR prophet_forecast IS NOT NULL)
                ORDER BY ticker, date DESC
                LIMIT :limit
            """, {"limit": limit * 3}, label="signal_universe_crypto")
            best = {}
            for r in crypto_rows:
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
                row = {
                    "ticker": r.ticker, "name": r.ticker,
                    "families": ["momentum"],
                    "direction": direction, "potential": round(potential, 2),
                    "change_pct": round((r.log_return or 0) * 100, 2),
                    "note": f"RSI {round(r.rsi_14, 1)}" if r.rsi_14 is not None else "—",
                }
                base = _crypto_base(r.ticker)
                if base not in best or (row["potential"] or 0) > (best[base]["potential"] or 0):
                    best[base] = row
            ranked = sorted(best.values(), key=lambda x: x["potential"] or 0, reverse=True)
            data.setdefault("CRYPTO", []).extend(ranked[:limit])

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
                    "note": _human_note(r.reasoning) or "—",
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


def _pct(v):
    # ETL currently writes hit_rate as a fraction (0.62); spec says percent.
    # Normalize so the UI always receives percent.
    if v is None:
        return None
    v = float(v)
    return round(v * 100, 1) if v <= 1.5 else round(v, 1)


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
            "family": r.family, "hit_rate": _pct(r.hit_rate),
            "fwd_return_5d": round(float(r.fwd_return_5d), 2) if r.fwd_return_5d is not None else None,
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
