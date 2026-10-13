# ADR-002: Data provenance is a first-class schema requirement
**Date:** 2026-10-13  
**Status:** Accepted

## Context

A macro intelligence terminal can only be trusted if every value is traceable to a source. Presenting stale, fabricated or misattributed data as current is the primary failure mode.

## Decision

Every data-bearing model (MacroObservation, MarketObservation, PositioningReport, etc.) must include:
- `provider_id` — which adapter fetched it
- `source_url` — direct link to the source document or endpoint
- `observed_at` — the timestamp of the underlying data (not our retrieval)
- `published_at` — when the provider made it available (nullable if unknown)
- `retrieved_at` — when we fetched it
- `data_status` — freshness label from the defined enum
- `units` — explicit unit string (percent, USD/bbl, index_points, etc.)

## Consequences

- Schema is slightly larger, but every query can answer "how fresh is this?"
- UI components must accept and display `data_status`; stale data is amber/warn, unavailable is gray.
- Ingestion code must populate all provenance fields; missing provenance is a DataQualityIssue, not silently ignored.
- AI agents must cite `EvidenceItem` records (which link back to source documents) rather than stating facts from memory.
