from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import auth_service, data_health

router = APIRouter(prefix="/data-health")
_SESSION_COOKIE = "gmit_session"


def _require_auth(db: Session = Depends(get_db),
                  token: str | None = Cookie(default=None, alias=_SESSION_COOKIE)):
    if not token or not auth_service.get_session(db, token):
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.get("")
def get_data_health(_auth=Depends(_require_auth), db: Session = Depends(get_db)):
    from app.main import _scheduler    # imported lazily: app.main imports this router
    next_runs = {j.id: j.next_run_time for j in _scheduler.get_jobs()}
    return data_health.collect(db, datetime.now(timezone.utc), next_runs)
