from fastapi import APIRouter
from app.api.routes import health, auth, providers, macro, market, research, smart_money, alerts, agent_runs, geo, data_health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(providers.router, tags=["providers"])
api_router.include_router(macro.router, tags=["macro"])
api_router.include_router(market.router, tags=["market"])
api_router.include_router(research.router, tags=["research"])
api_router.include_router(smart_money.router, tags=["smart-money"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(agent_runs.router, tags=["agent-runs"])
api_router.include_router(geo.router, tags=["geo"])
api_router.include_router(data_health.router, tags=["data-health"])
