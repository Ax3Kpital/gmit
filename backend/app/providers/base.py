from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class SeriesInfoDTO:
    series_id: str
    title: str
    description: str | None
    units: str
    frequency: str
    seasonal_adjustment: str | None
    source_url: str


@dataclass
class ObservationDTO:
    date: date
    value: float | None
    retrieved_at: datetime
    source_url: str


class MacroSeriesProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def fetch_series_info(self, series_id: str) -> SeriesInfoDTO: ...

    @abstractmethod
    async def fetch_observations(self, series_id: str, limit: int = 365) -> list[ObservationDTO]: ...
