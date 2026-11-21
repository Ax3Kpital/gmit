import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Cookie, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import auth_service
from app.db.models.smart_money import AlertRule, AlertEvent

router = APIRouter(prefix="/alerts")
_SESSION_COOKIE = "gmit_session"


def _get_user_id(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
) -> uuid.UUID:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = auth_service.get_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session.user_id


class CreateAlertRuleRequest(BaseModel):
    name: str
    rule_type: str  # price_threshold | cot_extreme
    series_id: str | None = None
    cftc_code: str | None = None
    condition: str  # above | below
    threshold_value: float


@router.get("/rules")
def get_rules(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    rules = db.query(AlertRule).filter(AlertRule.user_id == user_id).order_by(AlertRule.created_at.desc()).all()
    return [_rule_to_dict(r) for r in rules]


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(
    req: CreateAlertRuleRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    if req.rule_type not in ("price_threshold", "cot_extreme"):
        raise HTTPException(status_code=422, detail="Invalid rule_type")
    if req.condition not in ("above", "below"):
        raise HTTPException(status_code=422, detail="condition must be 'above' or 'below'")
    if req.rule_type == "price_threshold" and not req.series_id:
        raise HTTPException(status_code=422, detail="series_id required for price_threshold")
    if req.rule_type == "cot_extreme" and not req.cftc_code:
        raise HTTPException(status_code=422, detail="cftc_code required for cot_extreme")

    rule = AlertRule(
        user_id=user_id,
        name=req.name.strip(),
        rule_type=req.rule_type,
        series_id=req.series_id,
        cftc_code=req.cftc_code,
        condition=req.condition,
        threshold_value=req.threshold_value,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _rule_to_dict(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    try:
        rid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid rule_id")
    rule = db.query(AlertRule).filter(AlertRule.id == rid, AlertRule.user_id == user_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    db.delete(rule)
    db.commit()


@router.get("/events")
def get_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.user_id == user_id)
        .order_by(AlertEvent.triggered_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return [_event_to_dict(e) for e in events]


@router.put("/events/{event_id}/acknowledge", status_code=status.HTTP_200_OK)
def acknowledge_event(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    try:
        eid = uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid event_id")
    event = db.query(AlertEvent).filter(AlertEvent.id == eid, AlertEvent.user_id == user_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    event.acknowledged = True
    event.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return _event_to_dict(event)


@router.get("/events/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    count = db.query(AlertEvent).filter(
        AlertEvent.user_id == user_id,
        AlertEvent.acknowledged == False,
    ).count()
    return {"count": count}


def _rule_to_dict(r: AlertRule) -> dict:
    return {
        "id": str(r.id),
        "name": r.name,
        "rule_type": r.rule_type,
        "series_id": r.series_id,
        "cftc_code": r.cftc_code,
        "condition": r.condition,
        "threshold_value": r.threshold_value,
        "enabled": r.enabled,
        "created_at": r.created_at.isoformat(),
    }


def _event_to_dict(e: AlertEvent) -> dict:
    return {
        "id": str(e.id),
        "rule_id": str(e.rule_id),
        "triggered_at": e.triggered_at.isoformat(),
        "message": e.message,
        "value_at_trigger": e.value_at_trigger,
        "threshold_value": e.threshold_value,
        "acknowledged": e.acknowledged,
        "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None,
    }
