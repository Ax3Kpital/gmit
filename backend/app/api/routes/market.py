from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.macro import MacroSeries, MacroObservation
from app.core.freshness import age_label, classify_daily
from app.services.series_catalog import LIVE_IDS
from app.services.series_snapshot import resolve
from app.services import auth_service

router = APIRouter(prefix="/market")
_SESSION_COOKIE = "gmit_session"

_CATEGORY_ORDER = ["commodity", "equity", "fx"]

# Preferred display order within each category
_SERIES_ORDER = {
    "DCOILWTICO": 0, "DCOILBRENTEU": 1, "DHHNGSP": 2,   # commodities
    "SP500": 0,      "NASDAQCOM": 1,                     # equities
    "DEXUSEU": 0,    "DEXJPUS": 1, "DEXUSUK": 2, "DEXCHUS": 3,  # fx
}


def _require_auth(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
):
    if not token:
        raise HTTPException(status_code=401)
    if not auth_service.get_session(db, token):
        raise HTTPException(status_code=401)


@router.get("/watchlist")
def get_watchlist(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    rows = db.query(MacroSeries).filter(MacroSeries.category.in_(_CATEGORY_ORDER)).all()
    by_id = {s.series_id: s for s in rows}
    logical = [s for s in rows if s.series_id not in LIVE_IDS]
    logical.sort(key=lambda s: (_CATEGORY_ORDER.index(s.category), _SERIES_ORDER.get(s.series_id, 99)))

    now = datetime.now(timezone.utc)
    items = []
    for base in logical:
        series, latest = resolve(db, base, by_id)
        prev = None
        if latest:
            prev = (
                db.query(MacroObservation)
                .filter(MacroObservation.macro_series_id == series.id,
                        MacroObservation.value.isnot(None), MacroObservation.date < latest.date)
                .order_by(MacroObservation.date.desc()).first()
            )
        change = change_pct = None
        if latest and prev and prev.value:
            change = latest.value - prev.value
            change_pct = change / prev.value * 100

        fresh = classify_daily(latest.date if latest else None,
                               latest.data_status if latest else series.data_status, now)
        updated = (latest.published_at or latest.retrieved_at) if latest else None
        items.append({
            "series_id": series.series_id,
            "display_name": series.display_name or series.series_id,
            "category": base.category,
            "units": series.units,
            "data_status": fresh.status,
            "lag_sessions": fresh.lag_sessions,
            "age": age_label(latest.date if latest else None, now),
            "provider": latest.provider if latest else series.provider,
            "latest_date": latest.date.isoformat() if latest else None,
            "latest_value": latest.value if latest else None,
            "prev_date": prev.date.isoformat() if prev else None,
            "prev_value": prev.value if prev else None,
            "change": round(change, 4) if change is not None else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "updated_at": updated.isoformat() if updated else None,
            "last_fetched_at": series.last_fetched_at.isoformat() if series.last_fetched_at else None,
            "source_url": latest.source_url if latest else series.source_url,
        })
    return {"items": items, "as_of": now.isoformat()}
