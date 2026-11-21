"""GPR provider: legacy .xls and .xlsx parsing, and graceful failure."""
import io
from datetime import date
from pathlib import Path

import httpx
import openpyxl

from app.providers import gpr

FIXTURE = Path(__file__).parent / "fixtures" / "gpr_sample.xls"


def test_parse_xls_skips_months_without_gpr_and_sorts_ascending():
    points = gpr._parse_excel(FIXTURE.read_bytes())
    assert [p.period for p in points] == [date(2026, 8, 1), date(2026, 9, 1), date(2026, 10, 1)]
    assert points[-1].gpr_value == 150.5
    assert points[-1].gpr_threat == 156.8
    assert points[-1].gpr_act == 167.5


def test_parse_xlsx_in_memory():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["month", "GPR", "GPRT", "GPRA"])
    ws.append([date(2026, 9, 1), 120.0, 130.0, 110.0])
    ws.append([date(2026, 10, 1), 125.0, 135.0, 115.0])
    buf = io.BytesIO()
    wb.save(buf)
    points = gpr._parse_excel(buf.getvalue())
    assert [p.gpr_value for p in points] == [120.0, 125.0]
    assert points[0].period == date(2026, 9, 1)


def test_parse_empty_sheet_returns_no_points():
    wb = openpyxl.Workbook()
    buf = io.BytesIO()
    wb.save(buf)
    assert gpr._parse_excel(buf.getvalue()) == []


def _patch_client(monkeypatch, handler):
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(*args, **kwargs)

    monkeypatch.setattr(gpr.httpx, "AsyncClient", factory)


async def test_fetch_success_is_official_release_and_trimmed(monkeypatch):
    _patch_client(monkeypatch, lambda req: httpx.Response(200, content=FIXTURE.read_bytes()))
    result = await gpr.fetch_gpr_index(last_n_months=2)
    assert result.data_status == "PERIODIC_OFFICIAL_RELEASE"
    assert [p.period for p in result.series] == [date(2026, 9, 1), date(2026, 10, 1)]
    assert result.source_url.endswith("data_gpr_export.xls")


async def test_fetch_failure_is_unavailable_never_fabricated(monkeypatch):
    _patch_client(monkeypatch, lambda req: httpx.Response(503, text="down"))
    result = await gpr.fetch_gpr_index()
    assert result.data_status == "UNAVAILABLE"
    assert result.series == []


async def test_fetch_garbage_payload_is_unavailable(monkeypatch):
    _patch_client(monkeypatch, lambda req: httpx.Response(200, content=b"<html>not excel</html>"))
    result = await gpr.fetch_gpr_index()
    assert result.data_status == "UNAVAILABLE"
