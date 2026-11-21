"""
CFTC Commitments of Traders — Socrata public API provider.
Dataset: Legacy Futures Only (6dca-aqww)
URL: https://publicreporting.cftc.gov/resource/6dca-aqww.json
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import httpx

_BASE_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
_SOURCE_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww"


@dataclass
class CotObservation:
    cftc_code: str
    report_date: date
    open_interest: int | None
    noncomm_long: int | None
    noncomm_short: int | None
    noncomm_spread: int | None
    comm_long: int | None
    comm_short: int | None
    change_noncomm_long: int | None
    change_noncomm_short: int | None
    retrieved_at: datetime
    source_url: str


def _int(row: dict, key: str) -> int | None:
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return int(float(str(v).replace(",", "")))
    except (ValueError, TypeError):
        return None


class CftcProvider:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=30,
            headers={"Accept": "application/json"},
        )

    async def fetch_observations(self, cftc_code: str, limit: int = 104) -> list[CotObservation]:
        # Socrata SoQL uses literal '$' — must NOT be percent-encoded, so build URL directly
        # Note: "noncomm_postions_spread_all" is the actual column name in the Socrata dataset (typo by CFTC)
        select_cols = "report_date_as_yyyy_mm_dd,open_interest_all,noncomm_positions_long_all,noncomm_positions_short_all,noncomm_postions_spread_all,comm_positions_long_all,comm_positions_short_all,change_in_noncomm_long_all,change_in_noncomm_short_all"
        url = (
            f"{_BASE_URL}"
            f"?$where=cftc_contract_market_code='{cftc_code}'"
            f"&$order=report_date_as_yyyy_mm_dd DESC"
            f"&$limit={limit}"
            f"&$select={select_cols}"
        )
        resp = await self._client.get(url)
        resp.raise_for_status()
        rows = resp.json()
        retrieved_at = datetime.now(timezone.utc)

        results: list[CotObservation] = []
        for row in rows:
            date_str = row.get("report_date_as_yyyy_mm_dd", "")
            if not date_str:
                continue
            try:
                report_date = date.fromisoformat(date_str[:10])
            except ValueError:
                continue
            results.append(CotObservation(
                cftc_code=cftc_code,
                report_date=report_date,
                open_interest=_int(row, "open_interest_all"),
                noncomm_long=_int(row, "noncomm_positions_long_all"),
                noncomm_short=_int(row, "noncomm_positions_short_all"),
                noncomm_spread=_int(row, "noncomm_postions_spread_all"),
                comm_long=_int(row, "comm_positions_long_all"),
                comm_short=_int(row, "comm_positions_short_all"),
                change_noncomm_long=_int(row, "change_in_noncomm_long_all"),
                change_noncomm_short=_int(row, "change_in_noncomm_short_all"),
                retrieved_at=retrieved_at,
                source_url=_SOURCE_URL,
            ))
        return results

    async def aclose(self) -> None:
        await self._client.aclose()
