import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.on_event("startup")
async def startup():
    logger.info(
        "GMIT API starting — env=%s llm=%s fred=%s",
        settings.app_env,
        settings.llm_provider,
        "configured" if settings.fred_api_key else "not configured",
    )
