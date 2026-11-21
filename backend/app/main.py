import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
)
logger = logging.getLogger("gmit")

app = FastAPI(
    title="GMIT API",
    description="Global Macro Intelligence Terminal — backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

_scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    logger.info(
        "GMIT API starting — env=%s llm=%s fred=%s",
        settings.app_env,
        settings.llm_provider,
        "configured" if settings.fred_api_key else "not configured",
    )

    from datetime import datetime

    if settings.fred_api_key:
        from app.services.macro_ingestion import run_macro_ingestion
        _scheduler.add_job(
            run_macro_ingestion,
            trigger="interval",
            hours=1,
            next_run_time=datetime.now(),
            id="macro_ingestion",
            replace_existing=True,
        )
        logger.info("Macro ingestion scheduler started (1h interval, firing immediately)")
    else:
        logger.info("FRED_API_KEY not set — macro ingestion disabled")

    from app.services.cot_ingestion import run_cot_ingestion
    from app.services.alert_service import run_alert_checks
    _scheduler.add_job(
        run_cot_ingestion,
        trigger="interval",
        hours=6,
        next_run_time=datetime.now(),
        id="cot_ingestion",
        replace_existing=True,
    )
    _scheduler.add_job(
        run_alert_checks,
        trigger="interval",
        minutes=30,
        id="alert_checks",
        replace_existing=True,
    )
    logger.info("COT ingestion scheduler started (6h interval, firing immediately)")

    from app.services.briefing_service import generate_daily_briefing
    from app.db.session import SessionLocal
    import asyncio

    def _run_briefing():
        db = SessionLocal()
        try:
            generate_daily_briefing(db)
        except Exception as e:
            logger.error("Scheduled briefing failed: %s", e)
        finally:
            db.close()

    _scheduler.add_job(
        _run_briefing,
        trigger="cron",
        hour=7,
        minute=0,
        id="daily_briefing",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_briefing,
        trigger="date",
        run_date=datetime.now(),
        id="briefing_startup",
        replace_existing=True,
    )
    logger.info("Daily briefing scheduler started (07:00 UTC, firing immediately)")

    from app.services.geo_ingestion import run_geo_ingestion
    _scheduler.add_job(
        run_geo_ingestion,
        trigger="interval",
        hours=4,
        next_run_time=datetime.now(),
        id="geo_ingestion",
        replace_existing=True,
    )
    logger.info("Geo ingestion scheduler started (4h interval, firing immediately)")

    if not _scheduler.running:
        _scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
