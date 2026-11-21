"""U.S. Treasury yield-curve XML parsing."""
from datetime import date, datetime, timezone

import httpx
import pytest

from app.providers import treasury

XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
 <entry><content type="application/xml"><m:properties>
   <d:NEW_DATE m:type="Edm.DateTime">2026-11-20T00:00:00</d:NEW_DATE>
   <d:BC_2YEAR m:type="Edm.Double">4.63</d:BC_2YEAR>
   <d:BC_10YEAR m:type="Edm.Double">4.92</d:BC_10YEAR>
 </m:properties></content></entry>
 <entry><content type="application/xml"><m:properties>
   <d:NEW_DATE m:type="Edm.DateTime">2026-11-19T00:00:00</d:NEW_DATE>
   <d:BC_2YEAR m:type="Edm.Double">4.76</d:BC_2YEAR>
   <d:BC_10YEAR m:type="Edm.Double">5.04</d:BC_10YEAR>
 </m:properties></content></entry>
 <entry><content type="application/xml"><m:properties>
   <d:NEW_DATE m:type="Edm.DateTime">2026-11-18T00:00:00</d:NEW_DATE>
   <d:BC_2YEAR m:type="Edm.Double"></d:BC_2YEAR>
 </m:properties></content></entry>
</feed>"""


def test_parse_sorted_with_missing_values():
    pts = treasury.parse_yield_xml(XML)
    assert [p.date for p in pts] == [date(2026, 11, 18), date(2026, 11, 19), date(2026, 11, 20)]
    assert (pts[-1].y2, pts[-1].y10) == (4.63, 4.92)
    assert (pts[0].y2, pts[0].y10) == (None, None)


def test_invalid_xml_raises():
    with pytest.raises(treasury.TreasuryError):
        treasury.parse_yield_xml("<html>maintenance")


def test_oversized_response_is_rejected():
    with pytest.raises(treasury.TreasuryError):
        treasury.parse_yield_xml("x" * (treasury._MAX_BYTES + 1))


def test_months_to_fetch_crosses_year_boundary():
    assert treasury.months_to_fetch(datetime(2026, 1, 5, tzinfo=timezone.utc)) == ["202512", "202601"]
    assert treasury.months_to_fetch(datetime(2026, 11, 21, tzinfo=timezone.utc)) == ["202610", "202611"]


async def test_one_failing_month_does_not_lose_the_other():
    def handler(req):
        if req.url.params["field_tdr_date_value_month"] == "202610":
            return httpx.Response(503)
        return httpx.Response(200, text=XML)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        pts = await treasury.fetch_recent_yields(c, datetime(2026, 11, 21, tzinfo=timezone.utc))
    assert pts[-1].date == date(2026, 11, 20)
