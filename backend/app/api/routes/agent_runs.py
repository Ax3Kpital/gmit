from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.agent import AgentRun, Briefing
from app.services import auth_service
from app.core.config import settings

router = APIRouter()
_SESSION_COOKIE = "gmit_session"


def _require_auth(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not auth_service.get_session(db, token):
        raise HTTPException(status_code=401, detail="Session expired")


@router.get("/agent-runs")
def list_agent_runs(
    limit: int = 50,
    agent_type: str | None = None,
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    q = db.query(AgentRun).order_by(AgentRun.started_at.desc())
    if agent_type:
        q = q.filter(AgentRun.agent_type == agent_type)
    runs = q.limit(min(limit, 200)).all()

    return [
        {
            "id": str(r.id),
            "agent_type": r.agent_type,
            "trigger": r.trigger,
            "status": r.status,
            "provider": r.provider,
            "model_name": r.model_name,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "duration_ms": r.duration_ms,
            "result_summary": r.result_summary,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]


@router.get("/briefings")
def list_briefings(
    limit: int = 30,
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    briefings = (
        db.query(Briefing)
        .order_by(Briefing.date.desc())
        .limit(min(limit, 90))
        .all()
    )
    return [_fmt_briefing(b) for b in briefings]


@router.get("/briefings/latest")
def get_latest_briefing(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    briefing = db.query(Briefing).order_by(Briefing.date.desc()).first()
    if not briefing:
        return None
    return _fmt_briefing(briefing)


@router.get("/notifications/status")
def get_notification_status(_auth=Depends(_require_auth)):
    return {
        "email_configured": settings.email_configured,
        "telegram_configured": settings.telegram_configured,
        "smtp_host": settings.smtp_host or "",
        "notification_email": settings.notification_email or "",
        "telegram_chat_id": settings.telegram_chat_id or "",
    }


@router.post("/briefings/generate")
def trigger_briefing(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    from app.services.briefing_service import generate_daily_briefing
    briefing = generate_daily_briefing(db)
    return _fmt_briefing(briefing)


def _fmt_briefing(b: Briefing) -> dict:
    sections = b.sections or {}
    return {
        "id": str(b.id),
        "date": b.date.isoformat() if b.date else None,
        "macro_regime": b.macro_regime,
        "headline": b.headline,
        "key_moves": sections.get("key_moves", []),
        "cot_highlights": sections.get("cot_highlights", []),
        "alert_summary": sections.get("alert_summary", []),
        "watchlist": sections.get("watchlist", []),
        "generated_at": b.generated_at.isoformat() if b.generated_at else None,
    }
