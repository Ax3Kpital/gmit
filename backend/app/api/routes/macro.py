from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.macro import MacroSeries, MacroObservation
from app.core.freshness import age_label, classify_daily
from app.services import auth_service
from app.analysis.signals import compute_signals
from app.services.series_snapshot import build_snippets

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
    return asdict(compute_signals(build_snippets(db)))


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
    now = datetime.now(timezone.utc)
    data_status = classify_daily(latest.date if latest else None,
                                 latest.data_status if latest else series.data_status, now).status

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
            "provider": latest.provider,
            "age": age_label(latest.date, now),
        } if latest else None,
        "history": [
            {"date": o.date.isoformat(), "value": o.value}
            for o in reversed(observations)
        ],
    }
