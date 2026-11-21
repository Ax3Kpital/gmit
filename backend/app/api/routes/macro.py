from dataclasses import asdict
from datetime import datetime, timezone, timedelta, date as date_type
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.macro import MacroSeries, MacroObservation
from app.core.config import settings
from app.services import auth_service
from app.analysis.signals import compute_signals

router = APIRouter(prefix="/macro")
_SESSION_COOKIE = "gmit_session"


def _require_auth(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not auth_service.get_session(db, token):
        raise HTTPException(status_code=401, detail="Session expired")


@router.get("/signals")
def get_macro_signals(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    series_list = db.query(MacroSeries).all()
    cutoff = date_type.today() - timedelta(days=35)
    snippets = []
    for s in series_list:
        latest = (
            db.query(MacroObservation)
            .filter(MacroObservation.macro_series_id == s.id,
                    MacroObservation.value.isnot(None))
            .order_by(MacroObservation.date.desc())
            .first()
        )
        if not latest:
            continue
        prev = (
            db.query(MacroObservation)
            .filter(MacroObservation.macro_series_id == s.id,
                    MacroObservation.value.isnot(None),
                    MacroObservation.date <= cutoff)
            .order_by(MacroObservation.date.desc())
            .first()
        )
        delta30d = delta30d_pct = None
        if prev and prev.value and prev.value != 0:
            delta30d = latest.value - prev.value
            delta30d_pct = delta30d / abs(prev.value) * 100
        snippets.append({
            "series_id": s.series_id,
            "display_name": s.display_name or s.series_id,
            "latest_value": latest.value,
            "latest_date": latest.date.isoformat(),
            "delta30d": delta30d,
            "delta30d_pct": delta30d_pct,
            "units": s.units or "",
            "category": s.category,
        })

    signals = compute_signals(snippets)
    return asdict(signals)


@router.get("/series/{series_id}")
def get_macro_series(
    series_id: str,
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    series = db.query(MacroSeries).filter(MacroSeries.series_id == series_id.upper()).first()
    if not series:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")

    observations = (
        db.query(MacroObservation)
        .filter(MacroObservation.macro_series_id == series.id)
        .order_by(MacroObservation.date.desc())
        .limit(365)
        .all()
    )

    latest = observations[0] if observations else None

    if not settings.fred_api_key:
        data_status = "UNAVAILABLE"
    elif not latest:
        data_status = "UNAVAILABLE"
    elif series.last_fetched_at:
        age_hours = (datetime.now(timezone.utc) - series.last_fetched_at).total_seconds() / 3600
        data_status = "STALE" if age_hours > series.stale_after_hours else series.data_status
    else:
        data_status = series.data_status

    return {
        "series_id": series.series_id,
        "title": series.title,
        "provider": series.provider,
        "source_url": series.source_url,
        "units": series.units,
        "data_status": data_status,
        "last_fetched_at": series.last_fetched_at.isoformat() if series.last_fetched_at else None,
        "latest": {
            "date": latest.date.isoformat(),
            "value": latest.value,
            "retrieved_at": latest.retrieved_at.isoformat(),
        } if latest else None,
        "history": [
            {"date": o.date.isoformat(), "value": o.value}
            for o in reversed(observations)
        ],
    }
