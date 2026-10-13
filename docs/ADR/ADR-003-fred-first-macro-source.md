# ADR-003: FRED as the primary macro data source for Phase 2
**Date:** 2026-10-13  
**Status:** Accepted

## Context

Phase 2 requires one verified, real-data end-to-end slice before expanding ingestion breadth. We need to choose which source to build the first macro adapter for.

## Decision

Use **FRED (Federal Reserve Bank of St. Louis)** for the first macro data vertical slice.

Primary series for the initial dashboard:
- `DGS10` — 10-year Treasury constant maturity yield
- `DGS2` — 2-year Treasury yield
- `T10Y2Y` — 10Y–2Y spread (direct FRED series)
- `CPIAUCSL` — US CPI all items
- `UNRATE` — Unemployment rate
- `FEDFUNDS` — Federal funds effective rate

## Reasons

1. FRED terms explicitly permit personal/research use with attribution — documented in DATA_SOURCE_REGISTER.md.
2. 800,000+ series behind a single consistent API; building FRED support gives access to most macro series we'll ever need.
3. ALFRED (same API) provides vintage/as-of-date history, enabling look-ahead-free backtesting later.
4. Free API key, well-documented rate limits (120 req/min), stable API since 2012.
5. The `MacroSeriesProvider` interface built for FRED will be reusable for BLS, ECB and others with minimal changes.

## Consequences

- FRED adapter is the reference implementation for all macro providers.
- FRED API key must be stored in `.env` as `FRED_API_KEY`; the app must boot without it (providers show `UNAVAILABLE` status, not a crash).
- ALFRED vintage queries are added as an enhancement, not a Phase 2 blocker.
