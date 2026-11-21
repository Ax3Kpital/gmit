from fastapi import APIRouter, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import auth_service
from app.db.models.geo import GeoEvent, GeoRiskIndex, GeoNewsArticle
from app.analysis.geo_analysis import compute_region_risk
from datetime import datetime, timezone

from app.core.freshness import classify_fetch_age
from app.providers.gdelt import REGIONS
from app.services.data_health import GDELT_MAX_AGE_HOURS

router = APIRouter(prefix="/geo")
_SESSION_COOKIE = "gmit_session"


def _require_auth(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not auth_service.get_session(db, token):
        raise HTTPException(status_code=401, detail="Session expired")


@router.get("/risk-summary")
def get_risk_summary(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    """Computed risk level per region — from latest GDELT geo_events row."""
    result = []
    for region_key, region_meta in REGIONS.items():
        # newest row that carries real tone data: a later failed fetch must not hide it
        latest = (
            db.query(GeoEvent)
            .filter(GeoEvent.region_key == region_key, GeoEvent.avg_tone.isnot(None))
            .order_by(GeoEvent.retrieved_at.desc())
            .first()
        )
        status = "UNAVAILABLE"
        if latest:
            status = classify_fetch_age(latest.retrieved_at, datetime.now(timezone.utc),
                                        GDELT_MAX_AGE_HOURS, latest.data_status or "DELAYED")
        risk = compute_region_risk(
            region_key=region_key,
            region_label=region_meta["label"],
            avg_tone=latest.avg_tone if latest else None,
            article_count=latest.article_count if latest else None,
            data_status=status,
        )
        articles = []
        if latest:
            rows = (
                db.query(GeoNewsArticle)
                .filter(GeoNewsArticle.region_key == region_key)
                .order_by(GeoNewsArticle.retrieved_at.desc())
                .limit(5)
                .all()
            )
            for art in rows:
                articles.append({
                    "url": art.url,
                    "title": art.title,
                    "domain": art.domain,
                    "source_country": art.source_country,
                    "published_at": art.published_at.isoformat() if art.published_at else None,
                })
        result.append({
            "region_key": risk.region_key,
            "region_label": risk.region_label,
            "risk_level": risk.risk_level,
            "risk_score": risk.risk_score,
            "avg_tone": risk.avg_tone,
            "article_count": risk.article_count,
            "note": risk.note,
            "data_status": risk.data_status,
            "event_date": latest.event_date.isoformat() if latest else None,
            "retrieved_at": latest.retrieved_at.isoformat() if latest else None,
            "articles": articles,
        })
    return {"regions": result}


@router.get("/risk-index")
def get_risk_index(
    months: int = 36,
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    """GPR Index — last N months of monthly data."""
    rows = (
        db.query(GeoRiskIndex)
        .order_by(GeoRiskIndex.period.desc())
        .limit(months)
        .all()
    )
    rows = list(reversed(rows))  # ascending for chart

    if not rows:
        return {"series": [], "data_status": "UNAVAILABLE", "latest_period": None}

    latest_status = rows[-1].data_status if rows else "UNAVAILABLE"
    return {
        "series": [
            {
                "period": r.period.isoformat(),
                "gpr_value": r.gpr_value,
                "gpr_threat": r.gpr_threat,
                "gpr_act": r.gpr_act,
            }
            for r in rows
        ],
        "data_status": latest_status,
        "latest_period": rows[-1].period.isoformat() if rows else None,
    }


@router.get("/events")
def get_events(
    region_key: str | None = None,
    days: int = 30,
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    """Recent geo events (GDELT tone data) per region."""
    from datetime import date, timedelta
    since = date.today() - timedelta(days=days)
    q = db.query(GeoEvent).filter(GeoEvent.event_date >= since)
    if region_key:
        q = q.filter(GeoEvent.region_key == region_key)
    rows = q.order_by(GeoEvent.region_key, GeoEvent.event_date.desc()).all()

    return {
        "events": [
            {
                "region_key": r.region_key,
                "region_label": r.region_label,
                "event_date": r.event_date.isoformat(),
                "avg_tone": r.avg_tone,
                "article_count": r.article_count,
                "data_status": r.data_status,
                "retrieved_at": r.retrieved_at.isoformat(),
            }
            for r in rows
        ]
    }
