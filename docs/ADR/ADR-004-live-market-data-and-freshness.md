# ADR-004: Near-real-time market data and observation-based freshness
**Date:** 2026-11-21  
**Status:** Accepted

## Context

ADR-003 chose FRED as the first macro source. FRED redistributes EIA oil and gas prices, the H.10 FX rates and index data with delays of up to a week: on 2026-11-21 WTI ended on the 17th and FX on the 13th. A research terminal that shows days-old prices is misleading.

A second defect hid the problem: the data status was derived from `last_fetched_at` (when we last downloaded) instead of the date of the newest observation. FX data eight days old was labelled `END_OF_DAY` because the download was recent.

## Decision

1. **Add near-real-time sources next to FRED, not in place of it.** Yahoo Finance chart API for futures, indices and FX (every 10 minutes); the U.S. Treasury yield curve for 2Y/10Y (every 30 minutes). Yahoo terms are UNVERIFIED, so it is for personal use only (see the data source register).
2. **Store them as separate series** (`CL=F`, `^GSPC`, `EURUSD=X`, ...). EIA spot and NYMEX front-month futures are different instruments and are never spliced into one series. Treasury yields are the same quantity as FRED's DGS2/DGS10, so they write into those series with per-observation provenance.
3. **Resolve through a catalogue.** `series_catalog.LIVE_ALIAS` maps each FRED series to its fresher counterpart; `series_snapshot.build_snippets` answers with the alias when it is at least as recent, so signals, briefings, theses, the watchlist and alerts all see the same data. The 30-day change is always computed inside one series.
4. **Classify freshness from the observation date** (`core/freshness.py`): current against the latest expected US session -> the series' own status; one session late -> `DELAYED`; two or more -> `STALE`. COT is judged against the Friday release schedule.
5. FRED stays as history and fallback.

## Consequences

- Prices on screen are at most about ten minutes old during market hours and are the latest close at weekends.
- A failing provider no longer produces silently old numbers: the series ages to `DELAYED` and then `STALE`.
- Dependence on an unofficial endpoint. If it breaks the app degrades to FRED with honest `STALE` labels. A licensed feed (for example Alpha Vantage, Twelve Data or Polygon) can replace it behind `series_catalog` without touching consumers.
- Holidays are not modelled, so the first session after a market holiday can show one session as `DELAYED`.
