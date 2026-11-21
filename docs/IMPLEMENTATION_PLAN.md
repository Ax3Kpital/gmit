# GMIT — Implementation Plan
**Last updated:** 2026-10-13  
**Status:** Phases 0–8 complete (verified 2026-11-21); Phase 9 optional

---

## Guiding principle

Build vertical slices, not horizontal layers. One end-to-end feature that works reliably is worth more than five incomplete pipelines.

---

## Phase 0 — Repository reconnaissance and plan ✅

**Goal:** Establish foundation documents. No application code yet.

Tasks:
- [x] Create `/Users/pingutheboss/gmit` repository
- [x] `CLAUDE.md` with project rules, commands and design tokens
- [x] `docs/IMPLEMENTATION_PLAN.md` (this file)
- [x] `docs/DATA_SOURCE_REGISTER.md` skeleton
- [x] `docs/ADR/` directory + first ADR
- [ ] `.env.example`
- [ ] `DOMAIN_MODEL.md` first draft

**Acceptance criteria:** No application code committed. Plan reflects real decisions. No credentials in repo.

---

## Phase 1 — Local application foundation ✅

**Goal:** A runnable skeleton. No real data yet.

### 1.1 Backend
- FastAPI app with health endpoint
- PostgreSQL + SQLAlchemy 2.0 + Alembic setup
- User auth: password hashing (Argon2id), session tokens, login/logout endpoints
- Structured logging, configuration validation (Pydantic Settings)
- Provider health endpoint stub

### 1.2 Frontend
- Next.js 14 + TypeScript + Tailwind
- Design system wired to reference tokens (bg, panel, line, text, muted, accent, up, down, warn)
- Sidebar navigation (Command Center, Markets, Macro, Geopolitics, Scenarios, Opportunities, Smart Money, Alerts, Research Library, Agent Activity, Settings)
- Login page
- Command Center shell (layout, no real data)
- Provider health page (status tiles)

### 1.3 Infrastructure
- Docker Compose: `web`, `api`, `postgres` (+ optional `redis` stub)
- `.env.example` with all variable names and descriptions
- `healthcheck` on every service
- CI: lint, type check, unit tests (GitHub Actions or local Makefile)

**Acceptance criteria:**
- `docker compose up --build` from a fresh clone produces a running app
- App boots without any paid API keys
- Missing providers show a status tile, not a crash
- Login page is functional with a demo/dev user

---

## Phase 2 — First real-data vertical slice ✅

**Goal:** One macro series, end-to-end, with real data.

Chosen slice: **US 10-year Treasury yield and 2Y–10Y spread from FRED**.

Tasks:
- FRED adapter behind `MacroSeriesProvider` interface
- `MacroSeries` and `MacroObservation` models + migration
- Scheduled ingestion job (APScheduler), idempotent upsert
- Provenance fields: provider, source_url, observed_at, published_at, retrieved_at, data_status, units
- API endpoint: `GET /api/macro/series/{series_id}`
- Frontend: one chart with source label, observation date, data_status badge
- Tests: fixture-based (no live network in CI)

**Acceptance criteria:**
- Chart shows real FRED data with timestamp and `END_OF_DAY` / `PERIODIC_OFFICIAL_RELEASE` label
- Provider outage returns `STALE` in UI, not a crash
- Ingestion is idempotent (re-running does not duplicate rows)
- No mock values presented as real

---

## Phase 3 — Market watchlist and data-quality layer ✅

**Goal:** Initial market data (EOD/delayed, clearly labeled).

Instruments (initial watchlist):
- Gold, Silver, WTI crude, Brent crude, Henry Hub gas
- S&P 500, Nasdaq-100, Russell 2000 (proxies, EOD)
- EUR/USD, USD/JPY, GBP/USD, USD/CNH (reference rates)
- US 2Y, 10Y, 30Y yields (already from Phase 2 — extend)

Tasks:
- `Instrument`, `MarketObservation` models
- `MarketQuoteProvider` interface + first adapter (TBD after DATA_SOURCE_REGISTER)
- Watchlist API and frontend table with freshness badges
- Provider health dashboard: uptime, last successful fetch, error count
- Stale-data detection per instrument

**Acceptance criteria:**
- Every quote shows provider, quote type (EOD/DELAYED/INDICATIVE), and timestamp
- Stale data is visually distinct (amber/warn color)
- Unavailable data shows last known value + stale badge, never a fabricated value

---

## Phase 4 — Theses, scenarios and AI research ✅

**Goal:** Persistent research objects + first AI workflow.

Tasks:
- `Thesis`, `Scenario`, `ProbabilityAssessment`, `EvidenceItem`, `CounterArgument`, `Catalyst`, `InvalidationCondition` models
- AI provider abstraction: Anthropic + OpenAI behind `LLMProvider` interface
- Mock provider for tests (no API keys required)
- Orchestrator with token/time/cost budgets
- Agents: Macro, Geopolitics/Game Theory, Transmission, Scenario, Skeptic/Risk, Research Synthesizer
- Structured outputs with JSON schema validation
- Research Library UI
- Thesis card: claim, evidence, counter-evidence, scenarios, probabilities, catalysts, invalidation, confidence, source links

**Acceptance criteria:**
- Each research result includes model/provider metadata, timestamp and evidence references
- Malformed model output fails safely and does not corrupt saved theses
- A provider outage does not overwrite saved theses
- Skeptic agent must produce at least one counter-argument per thesis

---

## Phase 5 — Smart-money v1 and alerts ✅

**Goal:** CFTC COT + SEC 13F + configurable alerts.

Tasks:
- CFTC COT adapter (weekly, Tuesday data / Friday publication)
- SEC EDGAR 13F adapter (quarterly, with filing vs. as-of date)
- COT dashboard: net position, weekly delta, historical percentile
- 13F dashboard: notable changes, filing lag prominently displayed
- `AlertRule`, `AlertEvent`, `NotificationDelivery` models
- Rule engine: price threshold, COT extreme, macro release, scenario probability change
- In-app notification panel
- Deduplication, cooldown, quiet hours
- Alert history

**Acceptance criteria:**
- COT data displays report date and publication date, not just retrieval date
- 13F data displays as-of quarter and filing date; labeled as delayed disclosure
- Repeat polling does not create duplicate alerts
- Every alert explains: what changed, why it crossed threshold, source, timestamp, known lag

---

## Phase 6 — Agent observability and daily briefing ✅

**Goal:** Real agent execution events in UI + daily AI briefing.

Tasks:
- `AgentRun`, `AgentTask`, `AgentEvent`, `ModelCall`, `ToolCall` models
- SSE stream of real execution events (run started, source fetched, tool call/result, model call, handoff, validation, error, completion)
- Agent Activity UI: node graph driven by real persisted events (no fake animation)
- Daily briefing: AI-generated, with source links, what changed, counter-arguments, open questions
- Cost and runtime tracking per run

**Acceptance criteria:**
- A run can be fully reconstructed from stored events
- Failures, skipped steps and retries are visible in UI
- Briefing distinguishes facts, inferences and assumptions
- Fake/simulated activity is never shown in production

---

## Phase 7 — Notification channels and cloud hardening ✅

**Goal:** Email + WhatsApp alerts; cloud deployment path.

Tasks:
- Email notification adapter
- WhatsApp Business API adapter (after account validation and cost review)
- Terraform scaffold for chosen cloud (AWS or Azure)
- Managed PostgreSQL, object storage, secret manager, load balancer
- CI/CD: container registry, plan/apply separation, approval gate
- Backup and restore procedure
- Load test results and security review sign-off

**Not in scope until validated:** Kubernetes, multi-region DR, broker integration.

---

## Phase 8 — Geopolitics data feeds ✅

GDELT 2.0 (tone, volume and top articles per region, throttled to about one request every 5 seconds) and the Caldara–Iacoviello GPR index; region risk scoring; `/geopolitics` page. Providers that are down degrade to an explicit `UNAVAILABLE` state.

---

## Deferred / out of scope for MVP

- Intraday market data
- Options/dealer positioning
- Kubernetes and multi-region HA
- Multi-user billing and subscriptions
- Broker integration or automated order execution
- Comprehensive ETF flow data (pending source validation)

---

## Known open decisions

| Decision | Status |
|---|---|
| Market data provider for EOD quotes (Alpha Vantage vs. alternatives) | UNVERIFIED — Phase 3 gate |
| ETF flow data source | UNVERIFIED — Phase 5 gate |
| WhatsApp Business account and cost model | UNVERIFIED — Phase 7 gate |
| Cloud provider (AWS vs. Azure) | Open — user to decide before Phase 7 |
| RPO/RTO/availability targets | Open — required before Phase 7 |
