"""Settings endpoints — six sections: IBKR, Risk, Mode, Notifications, Data, Auth.

Reads/writes gold.platform_settings (existing table); writes log gold.audit_events.
See design-bundle handoff/API_SPEC_v2.md §7.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

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
    """Return real-time ingestion metadata for the Settings Data Sources tab."""
    rows = safe_query(db, """
        SELECT id, category, data_type, primary_source, frequency, last_refreshed, status
        FROM consumption.settings_data_sources
        ORDER BY category, data_type, primary_source
    """, label="settings_data_sources")
    return [
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
