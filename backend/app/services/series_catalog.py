"""Catalogue of near-real-time market series and how they map to the FRED series used elsewhere.

FRED republishes EIA, H.10 and index data with a delay of days, so each FRED market series has a
fresher counterpart from a market-data source. The two are *different instruments* (e.g. EIA spot
vs NYMEX front-month futures) and are stored as separate series; `LIVE_ALIAS` only says which
fresher series may stand in for a FRED series when it is at least as recent.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveSeries:
    series_id: str       # also the Yahoo Finance symbol
    display_name: str
    title: str
    category: str        # commodity | equity | fx
    units: str
    logical_id: str      # FRED series it can stand in for
    base_status: str     # status of a completed session's value


LIVE_SERIES: tuple[LiveSeries, ...] = (
    LiveSeries("CL=F", "WTI Crude (futures)", "WTI crude oil, NYMEX front-month futures",
               "commodity", "USD per barrel", "DCOILWTICO", "END_OF_DAY"),
    LiveSeries("BZ=F", "Brent Crude (futures)", "Brent crude oil, ICE front-month futures",
               "commodity", "USD per barrel", "DCOILBRENTEU", "END_OF_DAY"),
    LiveSeries("NG=F", "Natural Gas (futures)", "Henry Hub natural gas, NYMEX front-month futures",
               "commodity", "USD per MMBtu", "DHHNGSP", "END_OF_DAY"),
    LiveSeries("^GSPC", "S&P 500", "S&P 500 index", "equity", "Index", "SP500", "END_OF_DAY"),
    LiveSeries("^IXIC", "Nasdaq Composite", "Nasdaq Composite index", "equity", "Index",
               "NASDAQCOM", "END_OF_DAY"),
    LiveSeries("EURUSD=X", "EUR/USD", "Euro to US dollar spot", "fx", "USD per EUR",
               "DEXUSEU", "INDICATIVE"),
    LiveSeries("JPY=X", "USD/JPY", "US dollar to Japanese yen spot", "fx", "JPY per USD",
               "DEXJPUS", "INDICATIVE"),
    LiveSeries("GBPUSD=X", "GBP/USD", "British pound to US dollar spot", "fx", "USD per GBP",
               "DEXUSUK", "INDICATIVE"),
    LiveSeries("CNY=X", "USD/CNY", "US dollar to Chinese yuan spot", "fx", "CNY per USD",
               "DEXCHUS", "INDICATIVE"),
)

LIVE_ALIAS: dict[str, str] = {s.logical_id: s.series_id for s in LIVE_SERIES}
LIVE_IDS: frozenset[str] = frozenset(s.series_id for s in LIVE_SERIES)
