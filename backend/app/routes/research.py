"""
Research endpoints — regime forecasts and top-down research snapshots.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/research", tags=["research"])


VALID_HORIZONS = {"1d", "7d", "30d", "90d"}
HORIZON_TO_DAY_OFFSET = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/regime-forecast")
def get_regime_forecast(
    region: str = Query(..., description="Region code (US, FX, HK, CN, CRYPTO, METAL, ENERGY, etc.)"),
    horizon: str = Query("7d", description="Forecast horizon (1d, 7d, 30d, 90d)"),
    db: Session = Depends(get_db),
):
    """Return the latest market-regime forecast for a given region and horizon."""
    h = (horizon or "7d").lower().replace("1m", "30d").replace("3m", "90d")
    if h not in VALID_HORIZONS:
        return {"error": "invalid_horizon", "valid": sorted(VALID_HORIZONS)}
    day_offset = HORIZON_TO_DAY_OFFSET[h]
    region_norm = region.upper().strip()

    rows = safe_query(
        db,
        """
        SELECT forecast_date, scope AS region, day_offset,
               risk_on_pct, (100 - risk_on_pct) AS risk_off_pct, 0 AS neutral_pct,
               CASE WHEN risk_on_pct >= 55 THEN 'RISK_ON'
                    WHEN risk_on_pct <= 45 THEN 'RISK_OFF'
                    ELSE 'NEUTRAL' END AS dominant_regime,
               NULL::numeric AS regime_confidence, NULL AS features,
               updated_at
        FROM gold.regime_forecast
        WHERE scope = :region AND day_offset = :day_offset
        ORDER BY forecast_date DESC, updated_at DESC
        LIMIT 1
        """,
        {"region": region_norm, "day_offset": day_offset},
        label="regime_forecast",
    )

    if not rows:
        return {
            "region": region_norm,
            "horizon": h,
            "forecast_date": None,
            "risk_on_pct": 50,
            "risk_off_pct": 50,
            "neutral_pct": 0,
            "dominant_regime": "NEUTRAL",
            "regime_confidence": None,
            "features": None,
            "stale": True,
            "message": "No forecast data available for this region/horizon.",
        }

    r = rows[0]
    return {
        "region": r.region,
        "horizon": h,
        "forecast_date": r.forecast_date.isoformat() if r.forecast_date else None,
        "risk_on_pct": float(r.risk_on_pct) if r.risk_on_pct is not None else 50,
        "risk_off_pct": float(r.risk_off_pct) if r.risk_off_pct is not None else 50,
        "neutral_pct": float(r.neutral_pct) if r.neutral_pct is not None else 0,
        "dominant_regime": r.dominant_regime,
        "regime_confidence": float(r.regime_confidence) if r.regime_confidence is not None else None,
        "features": r.features,
        "stale": False,
    }


@router.get("/regime-forecast/all")
def get_all_regime_forecasts(
    horizon: str = Query("7d", description="Forecast horizon (1d, 7d, 30d, 90d)"),
    db: Session = Depends(get_db),
):
    """Return the latest forecast for every region for a given horizon."""
    h = (horizon or "7d").lower().replace("1m", "30d").replace("3m", "90d")
    if h not in VALID_HORIZONS:
        return {"error": "invalid_horizon", "valid": sorted(VALID_HORIZONS)}
    day_offset = HORIZON_TO_DAY_OFFSET[h]

    rows = safe_query(
        db,
        """
        SELECT DISTINCT ON (scope)
               forecast_date, scope AS region, day_offset,
               risk_on_pct, (100 - risk_on_pct) AS risk_off_pct, 0 AS neutral_pct,
               CASE WHEN risk_on_pct >= 55 THEN 'RISK_ON'
                    WHEN risk_on_pct <= 45 THEN 'RISK_OFF'
                    ELSE 'NEUTRAL' END AS dominant_regime,
               NULL::numeric AS regime_confidence,
               updated_at
        FROM gold.regime_forecast
        WHERE day_offset = :day_offset
        ORDER BY scope, forecast_date DESC, updated_at DESC
        """,
        {"day_offset": day_offset},
        label="regime_forecast_all",
    )

    result = []
    for r in rows:
        result.append({
            "region": r.region,
            "forecast_date": r.forecast_date.isoformat() if r.forecast_date else None,
            "risk_on_pct": float(r.risk_on_pct) if r.risk_on_pct is not None else 50,
            "risk_off_pct": float(r.risk_off_pct) if r.risk_off_pct is not None else 50,
            "neutral_pct": float(r.neutral_pct) if r.neutral_pct is not None else 0,
            "dominant_regime": r.dominant_regime,
            "regime_confidence": float(r.regime_confidence) if r.regime_confidence is not None else None,
        })
    return {"horizon": h, "count": len(result), "forecasts": result}
