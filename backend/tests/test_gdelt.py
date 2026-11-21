"""GDELT provider: correct endpoint, throttling/429 retry, graceful failure."""
import httpx

from app.providers import gdelt


def _patch(monkeypatch, handler):
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(*args, **kwargs)

    monkeypatch.setattr(gdelt.httpx, "AsyncClient", factory)


def _no_wait(monkeypatch):
    async def fast_sleep(_):
        return None

    monkeypatch.setattr(gdelt.asyncio, "sleep", fast_sleep)


def test_timeline_modes_use_the_doc_endpoint():
    assert gdelt._TIMELINE_BASE.endswith("/api/v2/doc/doc")
    assert "/timeline/timeline" not in gdelt._TIMELINE_BASE


async def test_429_is_retried_once_then_succeeds(monkeypatch):
    _no_wait(monkeypatch)
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(429) if len(calls) == 1 else httpx.Response(200, json={})

    _patch(monkeypatch, handler)
    async with httpx.AsyncClient() as client:
        resp = await gdelt._get(client, gdelt._DOC_BASE, {"query": "x"})
    assert resp.status_code == 200
    assert len(calls) == 2


async def test_persistent_429_returns_error_response_without_looping(monkeypatch):
    _no_wait(monkeypatch)
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(429)

    _patch(monkeypatch, handler)
    async with httpx.AsyncClient() as client:
        resp = await gdelt._get(client, gdelt._DOC_BASE, {"query": "x"})
    assert resp.status_code == 429
    assert len(calls) == 2


async def test_region_tone_parses_timeline_and_articles(monkeypatch):
    _no_wait(monkeypatch)

    def handler(req):
        mode = req.url.params.get("mode")
        if mode == "timelinetone":
            return httpx.Response(200, json={"timeline": [{"data": [
                {"date": "20261120T000000Z", "value": -3.0},
                {"date": "20261121T000000Z", "value": -5.0}]}]})
        if mode == "timelinevolraw":
            return httpx.Response(200, json={"timeline": [{"data": [{"value": 600}, {"value": 700}]}]})
        return httpx.Response(200, json={"articles": [
            {"url": "https://a.example/1", "title": "T", "domain": "a.example",
             "seendate": "20261121T101500Z"}]})

    _patch(monkeypatch, handler)
    res = await gdelt.fetch_region_tone("taiwan_strait")
    assert res.avg_tone == -4.0
    assert res.article_count == 1300
    assert res.data_status == "DELAYED"
    assert res.articles[0].url == "https://a.example/1"
    assert res.articles[0].published_at is not None


async def test_region_tone_all_failures_is_unavailable(monkeypatch):
    _no_wait(monkeypatch)
    _patch(monkeypatch, lambda req: httpx.Response(500))
    res = await gdelt.fetch_region_tone("middle_east")
    assert res.data_status == "UNAVAILABLE"
    assert res.avg_tone is None
    assert res.articles == []
