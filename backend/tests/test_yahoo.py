"""Yahoo chart parsing and fetching."""
from datetime import date, datetime, timezone

import httpx
import pytest

from app.providers import yahoo

T = int(datetime(2026, 11, 20, 14, 30, tzinfo=timezone.utc).timestamp())   # Friday, session open
DAY = 86400


def payload(**meta):
    base_meta = {"gmtoffset": -18000, "regularMarketPrice": 83.41,
                 "regularMarketTime": T + 3600}
    base_meta.update(meta)
    return {"chart": {"error": None, "result": [{
        "meta": base_meta,
        "timestamp": [T - 4 * DAY, T - 3 * DAY, T - 2 * DAY, T - DAY, T],
        "indicators": {"quote": [{"close": [85.72, 86.01, None, 83.21, 83.98]}]},
    }]}}


def test_parse_bars_skip_null_closes_and_sort():
    q = yahoo.parse_chart(payload(), "CL=F")
    assert [b.date for b in q.bars] == [date(2026, 11, 16), date(2026, 11, 17),
                                        date(2026, 11, 19), date(2026, 11, 20)]


def test_newest_bar_carries_the_latest_traded_price():
    q = yahoo.parse_chart(payload(), "CL=F")
    assert q.bars[-1].close == 83.41            # regularMarketPrice, not the stale bar close 83.98
    assert q.last_price == 83.41


def test_dates_use_the_exchange_timezone_offset():
    p = payload()
    p["chart"]["result"][0]["timestamp"] = [int(datetime(2026, 11, 20, 3, 0, tzinfo=timezone.utc).timestamp())]
    p["chart"]["result"][0]["indicators"]["quote"][0]["close"] = [80.0]
    p["chart"]["result"][0]["meta"].pop("regularMarketPrice")
    q = yahoo.parse_chart(p, "CL=F")
    assert q.bars[-1].date == date(2026, 11, 19)      # 03:00 UTC is still the 19th in New York


def test_is_live_window():
    q = yahoo.parse_chart(payload(), "CL=F")
    last = q.last_time
    assert q.is_live(last.replace(minute=last.minute + 5 if last.minute < 54 else 59))
    assert not q.is_live(datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc))


@pytest.mark.parametrize("bad", [
    {"chart": {"error": {"code": "Not Found"}, "result": None}},
    {"chart": {"error": None, "result": []}},
    {},
    {"chart": {"error": None, "result": [{"meta": {}, "timestamp": [], "indicators": {"quote": [{}]}}]}},
])
def test_bad_payloads_raise(bad):
    with pytest.raises(yahoo.YahooError):
        yahoo.parse_chart(bad, "X")


def _client(monkeypatch, handler):
    async def fast(_):
        return None
    monkeypatch.setattr(yahoo.asyncio, "sleep", fast)
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_fetch_retries_once_on_429(monkeypatch):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(429) if len(calls) == 1 else httpx.Response(200, json=payload())

    async with _client(monkeypatch, handler) as c:
        q = await yahoo.fetch_quote(c, "CL=F")
    assert len(calls) == 2 and q.symbol == "CL=F"


async def test_fetch_encodes_special_symbols(monkeypatch):
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, json=payload())

    async with _client(monkeypatch, handler) as c:
        await yahoo.fetch_quote(c, "^GSPC")
    assert "%5EGSPC" in seen[0]


async def test_fetch_failure_raises_yahoo_error(monkeypatch):
    async with _client(monkeypatch, lambda r: httpx.Response(500)) as c:
        with pytest.raises(yahoo.YahooError):
            await yahoo.fetch_quote(c, "CL=F")


@pytest.mark.parametrize("local,expected", [
    (datetime(2026, 11, 21, 5, 59), date(2026, 11, 20)),    # Saturday morning (Asian FX) -> Friday
    (datetime(2026, 11, 22, 23, 0), date(2026, 11, 23)),    # Sunday evening session -> Monday
    (datetime(2026, 11, 20, 12, 0), date(2026, 11, 20)),    # weekdays unchanged
])
def test_trade_date_never_lands_on_a_weekend(local, expected):
    assert yahoo.trade_date(local) == expected


def test_saturday_local_quote_is_dated_friday():
    close_utc = datetime(2026, 11, 20, 21, 59, 59, tzinfo=timezone.utc)   # Asia/Shanghai is already Saturday
    p = {"chart": {"error": None, "result": [{
        "meta": {"gmtoffset": 28800, "regularMarketPrice": 6.6772, "regularMarketTime": int(close_utc.timestamp())},
        "timestamp": [int(datetime(2026, 11, 19, 16, 0, tzinfo=timezone.utc).timestamp())],
        "indicators": {"quote": [{"close": [6.69]}]}}]}}
    q = yahoo.parse_chart(p, "CNY=X")
    assert q.bars[-1].date == date(2026, 11, 20) and q.bars[-1].close == 6.6772
