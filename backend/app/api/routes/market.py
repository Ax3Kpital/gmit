from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.macro import MacroSeries, MacroObservation
from app.core.config import settings
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
    series_list = (
        db.query(MacroSeries)
        .filter(MacroSeries.category.in_(_CATEGORY_ORDER))
        .all()
    )
    series_list.sort(key=lambda s: (
        _CATEGORY_ORDER.index(s.category),
        _SERIES_ORDER.get(s.series_id, 99),
    ))

    now = datetime.now(timezone.utc)
    items = []

    for series in series_list:
        recent = (
            db.query(MacroObservation)
            .filter(MacroObservation.macro_series_id == series.id)
            .order_by(MacroObservation.date.desc())
            .limit(2)
            .all()
        )

        latest = recent[0] if recent else None
        prev = recent[1] if len(recent) > 1 else None

        change = None
        change_pct = None
        if latest and prev and latest.value is not None and prev.value is not None and prev.value != 0:
            change = latest.value - prev.value
            change_pct = (change / prev.value) * 100

        if not settings.fred_api_key:
            data_status = "UNAVAILABLE"
        elif not latest:
            data_status = "UNAVAILABLE"
        elif series.last_fetched_at:
            age_hours = (now - series.last_fetched_at).total_seconds() / 3600
            data_status = "STALE" if age_hours > series.stale_after_hours else series.data_status
        else:
            data_status = series.data_status

        items.append({
            "series_id": series.series_id,
            "display_name": series.display_name or series.series_id,
            "category": series.category,
            "units": series.units,
            "data_status": data_status,
            "latest_date": latest.date.isoformat() if latest else None,
            "latest_value": latest.value if latest else None,
            "prev_date": prev.date.isoformat() if prev else None,
            "prev_value": prev.value if prev else None,
            "change": round(change, 4) if change is not None else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "last_fetched_at": series.last_fetched_at.isoformat() if series.last_fetched_at else None,
            "source_url": series.source_url,
        })

    return {"items": items, "as_of": now.isoformat()}
