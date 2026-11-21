"""Yahoo Finance chart API: daily bars plus the latest quote for futures, indices and FX.

Unofficial endpoint (no key). Terms of use for redistribution are UNVERIFIED, so this is meant
for personal, non-commercial research only; see docs/DATA_SOURCE_REGISTER.md.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import httpx

logger = logging.getLogger("gmit.yahoo")

_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GMIT-research/0.1; personal, non-commercial)"}
LIVE_WINDOW = timedelta(minutes=30)


class YahooError(Exception):
    pass


@dataclass(frozen=True)
class Bar:
    date: date
    close: float


@dataclass
class Quote:
    symbol: str
    bars: list[Bar]               # ascending by date; the newest bar carries the latest price
    last_price: float | None
    last_time: datetime | None    # UTC time of the latest trade
    source_url: str
    retrieved_at: datetime

    def is_live(self, now: datetime) -> bool:
        return self.last_time is not None and now - self.last_time <= LIVE_WINDOW


def trade_date(local: datetime) -> date:
    """Trading day of a timestamp in the exchange's local time.

    Local time can already be Saturday for Asian-zone FX quotes that trade until Friday 22:00 UTC,
    and Sunday for sessions that open Sunday evening. Saturday belongs to Friday's session and
    Sunday to Monday's (CME convention), so weekend dates never make data look fresher than it is.
    """
    d = local.date()
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def source_url(symbol: str) -> str:
    return f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}"


def parse_chart(payload: dict, symbol: str, retrieved_at: datetime | None = None) -> Quote:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise YahooError(f"{symbol}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise YahooError(f"{symbol}: empty result")
    res = results[0]
    meta = res.get("meta") or {}
    offset = timedelta(seconds=int(meta.get("gmtoffset") or 0))
    timestamps = res.get("timestamp") or []
    closes = ((res.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []

    bars: dict[date, float] = {}
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        local = datetime.fromtimestamp(ts, timezone.utc) + offset
        bars[trade_date(local)] = float(close)

    last_price = meta.get("regularMarketPrice")
    last_time = None
    if meta.get("regularMarketTime"):
        last_time = datetime.fromtimestamp(int(meta["regularMarketTime"]), timezone.utc)
    if last_price is not None and last_time is not None:
        # the newest daily bar is the live session: make it carry the latest traded price
        bars[trade_date(last_time + offset)] = float(last_price)

    if not bars:
        raise YahooError(f"{symbol}: no price data")
    ordered = [Bar(d, bars[d]) for d in sorted(bars)]
    return Quote(symbol, ordered, float(last_price) if last_price is not None else None,
                 last_time, source_url(symbol), retrieved_at)


async def fetch_quote(client: httpx.AsyncClient, symbol: str, range_: str = "6mo") -> Quote:
    url = _BASE + quote(symbol, safe="")
    last_exc: Exception | None = None
    for attempt in (1, 2):
        try:
            resp = await client.get(url, params={"range": range_, "interval": "1d"}, headers=_HEADERS)
            if resp.status_code in (429, 500, 502, 503) and attempt == 1:
                await asyncio.sleep(3)
                continue
            resp.raise_for_status()
            return parse_chart(resp.json(), symbol)
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
    raise YahooError(f"{symbol}: {last_exc}")
