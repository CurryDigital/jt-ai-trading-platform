"""Settings endpoints — six sections: IBKR, Risk, Mode, Notifications, Data, Auth.

Reads/writes gold.platform_settings (existing table); writes log gold.audit_events.
See design-bundle handoff/API_SPEC_v2.md §7.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timezone

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/settings", tags=["settings"])

SECTIONS = {"ibkr_connection", "risk_config", "execution_mode", "notifications", "data_sources", "auth", "trading_config"}
RISK_KEYS = {"max_drawdown", "min_sharpe_oos", "high_turnover", "low_trade_count"}


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT key, value FROM gold.platform_settings
        WHERE key LIKE 'settings.%'
    """, label="settings_get_all")
    sections = {s: {} for s in SECTIONS}
    for r in rows:
        _, section, field = (r.key.split(".", 2) + [None])[:3]
        if section in sections and field:
            try:
                sections[section][field] = json.loads(r.value)
            except (TypeError, ValueError):
                sections[section][field] = r.value
    return sections


@router.put("/{section}")
def put_settings_section(section: str, payload: dict, db: Session = Depends(get_db)):
    if section not in SECTIONS:
        raise HTTPException(status_code=404, detail=f"Unknown settings section: {section}")
    if section == "risk_config":
        unknown = set(payload.keys()) - RISK_KEYS
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown risk_config keys: {sorted(unknown)}")

    for field, value in payload.items():
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES (:key, :value, NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """), {"key": f"settings.{section}.{field}", "value": json.dumps(value)})

    safe_query(db, """
        INSERT INTO gold.audit_events (event_type, detail, created_at)
        VALUES (:event_type, :detail, NOW())
    """, {"event_type": "settings.update", "detail": f"Updated {section}: {sorted(payload.keys())}"},
        label="settings_audit")
    db.commit()
    return {"section": section, "updated": payload}


@router.get("/data-sources")
def get_data_sources(db: Session = Depends(get_db)):
    """Ingestion metadata + ETL freshness for the Settings Data Sources tab.

    Response shape:
      {
        "data_sources": [...consumption.settings_data_sources rows...],
        "freshness":    [...gold.source_freshness rows with computed stale flag...],
        "ibkr_connected": bool,
        "as_of": ISO timestamp
    }
    """
    rows = safe_query(db, """
        SELECT id, category, data_type, primary_source, frequency, last_refreshed, status
        FROM consumption.settings_data_sources
        ORDER BY category, data_type, primary_source
    """, label="settings_data_sources")
    data_sources = [
        {
            "id": r.id,
            "category": r.category,
            "data_type": r.data_type,
            "primary_source": r.primary_source,
            "frequency": r.frequency,
            "last_refreshed": r.last_refreshed.isoformat() if r.last_refreshed else None,
            "status": r.status,
        }
        for r in rows
    ]

    # ETL freshness estate — gold.source_freshness is written by every pipeline
    # (including news_pipeline_c). stale = now() - last_refreshed_at > expected_max_staleness_hours;
    # a NULL last_refreshed_at (never refreshed) counts as stale.
    freshness_rows = safe_query(db, """
        SELECT source, asset_class, max_date, expected_frequency,
               expected_max_staleness_hours, last_refreshed_at, last_checked_at,
               last_error,
               CASE
                   WHEN last_refreshed_at IS NULL THEN TRUE
                   WHEN expected_max_staleness_hours IS NULL THEN FALSE
                   ELSE now() - last_refreshed_at
                        > make_interval(hours => expected_max_staleness_hours)
               END AS stale,
               EXTRACT(EPOCH FROM (now() - last_refreshed_at)) / 3600.0 AS age_hours
        FROM gold.source_freshness
        ORDER BY stale DESC, source
    """, label="settings_source_freshness")
    freshness = [
        {
            "source": r.source,
            "asset_class": r.asset_class,
            "max_date": r.max_date.isoformat() if r.max_date else None,
            "expected_frequency": r.expected_frequency,
            "expected_max_staleness_hours": r.expected_max_staleness_hours,
            "last_refreshed_at": r.last_refreshed_at.isoformat() if r.last_refreshed_at else None,
            "last_checked_at": r.last_checked_at.isoformat() if r.last_checked_at else None,
            "last_error": r.last_error,
            "stale": bool(r.stale),
            "age_hours": round(float(r.age_hours), 2) if r.age_hours is not None else None,
        }
        for r in freshness_rows
    ]

    ibkr_connected = False
    try:
        from app.services.ib_service import ib_quant_service
        ibkr_connected = ib_quant_service.is_connected
    except Exception:
        pass

    return {
        "data_sources": data_sources,
        "freshness": freshness,
        "ibkr_connected": ibkr_connected,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }
