"""GDELT 2.0 provider — tone timeline + article list per geopolitical region."""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import asyncio
import time

import httpx

logger = logging.getLogger("gmit.gdelt")

# Timeline modes (timelinetone, timelinevolraw) are served by the DOC endpoint too.
_TIMELINE_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_DOC_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# Region keys → human label + GDELT query string
REGIONS: dict[str, dict] = {
    "eastern_europe": {
        "label": "Eastern Europe / Russia-Ukraine",
        "query": "Russia Ukraine conflict war sanctions NATO",
    },
    "middle_east": {
        "label": "Middle East / MENA",
        "query": "Middle East Iran Israel conflict Houthi oil Gaza",
    },
    "taiwan_strait": {
        "label": "Taiwan Strait",
        "query": "Taiwan China military strait threat invasion",
    },
    "sub_saharan_africa": {
        "label": "Sub-Saharan Africa",
        "query": "Sahel Africa coup conflict junta military government",
    },
    "latin_america": {
        "label": "Latin America",
        "query": "Latin America Venezuela Colombia political crisis instability",
    },
    "north_america_europe": {
        "label": "North America / Europe",
        "query": "NATO alliance political polarization democracy threat Europe",
    },
}


@dataclass
class TonePoint:
    date: str        # YYYYMMDDTHHMMSSZ
    value: float     # GDELT tone: negative = conflict/negative coverage


@dataclass
class GdeltArticle:
    url: str
    title: Optional[str]
    domain: Optional[str]
    source_country: Optional[str]
    language: Optional[str]
    published_at: Optional[datetime]


@dataclass
class RegionToneResult:
    region_key: str
    region_label: str
    query: str
    tone_series: list[TonePoint]   # daily tone for last ~2 weeks
    avg_tone: Optional[float]       # average over series
    article_count: Optional[int]    # from volume timeline
    articles: list[GdeltArticle]
    retrieved_at: datetime
    data_status: str


# GDELT asks clients to stay at roughly one request per 5 seconds; faster calls get 429 or
# dropped connections. All requests go through one throttle, with a single retry on 429.
_MIN_INTERVAL_S = 5.5
_RETRY_AFTER_429_S = 15.0
_throttle_lock = asyncio.Lock()
_last_request_at = 0.0


async def _get(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    global _last_request_at
    for attempt in (1, 2):
        async with _throttle_lock:
            wait = _MIN_INTERVAL_S - (time.monotonic() - _last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            resp = await client.get(url, params=params)
            _last_request_at = time.monotonic()
        if resp.status_code == 429 and attempt == 1:
            logger.warning("GDELT rate limit (429); retrying once in %.0fs", _RETRY_AFTER_429_S)
            await asyncio.sleep(_RETRY_AFTER_429_S)
            continue
        return resp
    return resp


async def fetch_region_tone(region_key: str, timespan: str = "2weeks") -> RegionToneResult:
    """Fetch GDELT tone timeline + top articles for a region."""
    region = REGIONS[region_key]
    query = region["query"]
    retrieved_at = datetime.now(timezone.utc)

    tone_series: list[TonePoint] = []
    avg_tone: Optional[float] = None
    article_count: Optional[int] = None
    articles: list[GdeltArticle] = []
    data_status = "UNAVAILABLE"

    async with httpx.AsyncClient(timeout=20) as client:
        # 1. Tone timeline
        try:
            resp = await _get(
                client,
                _TIMELINE_BASE,
                {
                    "query": query,
                    "mode": "timelinetone",
                    "timespan": timespan,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            # payload["timeline"] is a list; first series has "data"
            series_list = payload.get("timeline", [])
            if series_list and series_list[0].get("data"):
                for pt in series_list[0]["data"]:
                    tone_series.append(TonePoint(date=pt["date"], value=float(pt["value"])))
            if tone_series:
                avg_tone = sum(p.value for p in tone_series) / len(tone_series)
                data_status = "DELAYED"
        except Exception as exc:
            logger.warning("GDELT tone timeline failed for %s: %s", region_key, exc)

        # 2. Volume timeline (article count)
        try:
            resp = await _get(
                client,
                _TIMELINE_BASE,
                {
                    "query": query,
                    "mode": "timelinevolraw",
                    "timespan": "1week",
                    "format": "json",
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            series_list = payload.get("timeline", [])
            if series_list and series_list[0].get("data"):
                # Sum article counts for the week
                article_count = int(sum(
                    float(pt.get("value", 0))
                    for pt in series_list[0]["data"]
                ))
        except Exception as exc:
            logger.warning("GDELT volume timeline failed for %s: %s", region_key, exc)

        # 3. Top articles
        try:
            resp = await _get(
                client,
                _DOC_BASE,
                {
                    "query": query,
                    "mode": "artlist",
                    "maxrecords": "5",
                    "format": "json",
                    "sourcelang": "english",
                    "timespan": "3days",
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            for art in payload.get("articles", []):
                pub_at: Optional[datetime] = None
                raw_date = art.get("seendate", "")
                if raw_date:
                    try:
                        pub_at = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ").replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        pass
                articles.append(
                    GdeltArticle(
                        url=art.get("url", ""),
                        title=art.get("title"),
                        domain=art.get("domain"),
                        source_country=art.get("sourcecountry"),
                        language=art.get("language"),
                        published_at=pub_at,
                    )
                )
        except Exception as exc:
            logger.warning("GDELT artlist failed for %s: %s", region_key, exc)

    return RegionToneResult(
        region_key=region_key,
        region_label=region["label"],
        query=query,
        tone_series=tone_series,
        avg_tone=avg_tone,
        article_count=article_count,
        articles=articles,
        retrieved_at=retrieved_at,
        data_status=data_status,
    )


async def fetch_all_regions(timespan: str = "2weeks") -> list[RegionToneResult]:
    """Fetch tone data for all regions, one at a time (GDELT rate limit)."""
    return [await fetch_region_tone(key, timespan) for key in REGIONS]
