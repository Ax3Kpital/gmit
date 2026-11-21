"""U.S. Treasury daily par yield curve (official, public domain, no key).

Published the evening of each trading day, i.e. about one day ahead of FRED's DGS2/DGS10 copy.
"""
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import httpx

logger = logging.getLogger("gmit.treasury")

_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
_M = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"
_D = "{http://schemas.microsoft.com/ado/2007/08/dataservices}"
_MAX_BYTES = 5_000_000


class TreasuryError(Exception):
    pass


@dataclass(frozen=True)
class YieldPoint:
    date: date
    y2: float | None
    y10: float | None


def source_url(month: str) -> str:
    return f"{_URL}?data=daily_treasury_yield_curve&field_tdr_date_value_month={month}"


def _num(text: str | None) -> float | None:
    try:
        return float(text) if text not in (None, "") else None
    except ValueError:
        return None


def parse_yield_xml(text: str) -> list[YieldPoint]:
    if len(text) > _MAX_BYTES:
        raise TreasuryError("response too large")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise TreasuryError(f"invalid XML: {exc}") from exc
    points: list[YieldPoint] = []
    for props in root.iter(f"{_M}properties"):
        raw = props.findtext(f"{_D}NEW_DATE")
        if not raw:
            continue
        try:
            d = date.fromisoformat(raw[:10])
        except ValueError:
            continue
        points.append(YieldPoint(d, _num(props.findtext(f"{_D}BC_2YEAR")),
                                 _num(props.findtext(f"{_D}BC_10YEAR"))))
    points.sort(key=lambda p: p.date)
    return points


def months_to_fetch(now: datetime) -> list[str]:
    now = now.astimezone(timezone.utc)
    prev = (now.replace(day=1) - timedelta(days=1))
    return [prev.strftime("%Y%m"), now.strftime("%Y%m")]


async def fetch_recent_yields(client: httpx.AsyncClient, now: datetime | None = None) -> list[YieldPoint]:
    now = now or datetime.now(timezone.utc)
    merged: dict[date, YieldPoint] = {}
    for month in months_to_fetch(now):
        try:
            resp = await client.get(_URL, params={"data": "daily_treasury_yield_curve",
                                                  "field_tdr_date_value_month": month})
            resp.raise_for_status()
            for p in parse_yield_xml(resp.text):
                merged[p.date] = p
        except (httpx.HTTPError, TreasuryError) as exc:
            logger.warning("Treasury yield fetch failed for %s: %s", month, exc)
    return [merged[d] for d in sorted(merged)]
