from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "phase": "1",
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
