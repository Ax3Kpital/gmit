from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/providers")

PROVIDERS = [
    {
        "code": "yahoo_finance",
        "name": "Yahoo Finance (chart API)",
        "description": "Near-real-time futures (WTI, Brent, gas), indices and FX, refreshed every 10 minutes",
        "terms": "UNVERIFIED redistribution terms; unofficial endpoint, personal research use only",
        "phase": 9,
        "configured": True,  # no key required
    },
    {
        "code": "us_treasury_yields",
        "name": "U.S. Treasury daily par yield curve",
        "description": "Official 2Y and 10Y yields, same-day after the close (feeds DGS2, DGS10, 10Y-2Y)",
        "terms": "Public domain, no key",
        "phase": 9,
        "configured": True,  # no key required
    },
    {
        "code": "fred",
        "name": "FRED — Federal Reserve Bank of St. Louis",
        "description": "Macro series and fallback history. Market series lag by days, so live quotes take precedence",
        "terms": "Free, personal/research use, attribution required",
        "phase": 2,
        "configured": bool(settings.fred_api_key),
    },
    {
        "code": "cftc_cot",
        "name": "CFTC Commitments of Traders",
        "description": "Weekly futures positioning: gold, silver, crude, gas, equity indices, FX",
        "terms": "Public domain, weekly lag (Tuesday data / Friday publication)",
        "phase": 5,
        "configured": True,  # no key required
    },
    {
        "code": "sec_edgar",
        "name": "SEC EDGAR",
        "description": "13F institutional filings, insider transactions, company filings",
        "terms": "Public data, 10 req/sec limit, User-Agent identification required",
        "phase": 5,
        "configured": True,  # no key required
    },
    {
        "code": "ecb",
        "name": "ECB Data Portal (SDMX)",
        "description": "Euro-area rates, inflation, exchange rates, bank lending",
        "terms": "Free, attribution required",
        "phase": 3,
        "configured": True,  # no key required
    },
    {
        "code": "eia",
        "name": "EIA — U.S. Energy Information Administration",
        "description": "Oil/gas storage, production, prices, electricity",
        "terms": "Free, API key required, attribution required",
        "phase": 3,
        "configured": bool(settings.eia_api_key),
    },
    {
        "code": "gdelt",
        "name": "GDELT Project",
        "description": "Global news event monitoring, 100+ languages",
        "terms": "Open, bulk files, for discovery not as authoritative source",
        "phase": 3,
        "configured": True,  # no key required
    },
    {
        "code": "bls",
        "name": "BLS — Bureau of Labor Statistics",
        "description": "US CPI, employment, wages, productivity",
        "terms": "Free, API key recommended for higher limits",
        "phase": 2,
        "configured": True,  # key optional
    },
    {
        "code": "treasury",
        "name": "U.S. Treasury FiscalData",
        "description": "Treasury yields, TGA balance, debt securities",
        "terms": "Public domain, no key required",
        "phase": 2,
        "configured": True,
    },
    {
        "code": "anthropic",
        "name": "Anthropic (Claude)",
        "description": "AI research, analysis and synthesis agent",
        "terms": "Commercial API, cost per token",
        "phase": 4,
        "configured": bool(settings.anthropic_api_key),
    },
    {
        "code": "openai",
        "name": "OpenAI (GPT)",
        "description": "AI research, alternative provider",
        "terms": "Commercial API, cost per token",
        "phase": 4,
        "configured": bool(settings.openai_api_key),
    },
]


@router.get("")
def list_providers():
    return {
        "providers": [
            {
                **p,
                "status": "configured" if p["configured"] else "unconfigured",
                "active_phase": False,  # no adapter implemented yet in Phase 1
            }
            for p in PROVIDERS
        ]
    }
