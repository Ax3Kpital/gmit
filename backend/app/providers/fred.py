import logging
from datetime import date, datetime, timezone
import httpx
from app.providers.base import MacroSeriesProvider, SeriesInfoDTO, ObservationDTO
from app.core.config import settings

logger = logging.getLogger("gmit.fred")

_FRED_BASE = "https://api.stlouisfed.org/fred"
_SOURCE_TMPL = "https://fred.stlouisfed.org/series/{series_id}"


class FredProvider(MacroSeriesProvider):
    @property
    def provider_name(self) -> str:
        return "fred"

    def _source_url(self, series_id: str) -> str:
        return _SOURCE_TMPL.format(series_id=series_id)

    async def fetch_series_info(self, series_id: str) -> SeriesInfoDTO:
        url = (
            f"{_FRED_BASE}/series"
            f"?series_id={series_id}&api_key={settings.fred_api_key}&file_type=json"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        s = resp.json()["seriess"][0]
        return SeriesInfoDTO(
            series_id=series_id,
            title=s["title"],
            description=s.get("notes"),
            units=s["units"],
            frequency=s.get("frequency", ""),
            seasonal_adjustment=s.get("seasonal_adjustment"),
            source_url=self._source_url(series_id),
        )

    async def fetch_observations(self, series_id: str, limit: int = 365) -> list[ObservationDTO]:
        url = (
            f"{_FRED_BASE}/series/observations"
            f"?series_id={series_id}&api_key={settings.fred_api_key}"
            f"&file_type=json&limit={limit}&sort_order=desc"
        )
        retrieved_at = datetime.now(timezone.utc)
        source_url = self._source_url(series_id)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        results: list[ObservationDTO] = []
        for obs in resp.json().get("observations", []):
            raw = obs.get("value", ".")
            value = None if raw == "." else float(raw)
            results.append(ObservationDTO(
                date=date.fromisoformat(obs["date"]),
                value=value,
                retrieved_at=retrieved_at,
                source_url=source_url,
            ))
        return results
