# ADR-001: Modular monolith, not microservices
**Date:** 2026-10-13  
**Status:** Accepted

## Context

GMIT needs workers for data ingestion, AI agent workflows, alert delivery and scheduled briefings — plus an API layer and a frontend. This raises the question of whether to split these into separate deployable services.

## Decision

Ship a **modular monolith**: all backend logic in one FastAPI codebase, with workers as logical modules (not separate deployments). Frontend is a separate Next.js app. PostgreSQL is the single primary datastore.

## Reasons

1. A single-developer personal tool does not need service discovery, network policies, inter-service auth or distributed tracing at launch.
2. Microservices increase debugging surface area; a shared process makes agent workflows, database transactions and error handling simpler.
3. The same Docker Compose works locally and cloud-ready; separate services can be extracted later based on measured bottlenecks.
4. bvb_project proved this stack pattern is workable for this use case.

## Consequences

- Worker code (ingestion, agents, alerts) lives in `backend/app/workers/` and is called via APScheduler or triggered internally.
- Module boundaries are enforced by code organization and interface contracts, not network calls.
- If a specific worker (e.g. heavy AI orchestrator) causes resource contention, it can be extracted to a separate container later — same codebase, different entrypoint.
- Kubernetes is out of scope until there is a measured reason (team size, scale, isolation requirements).
