# Global Macro Intelligence Terminal (GMIT)

A personal macro-financial research terminal: monitors global macro data, commodity and equity markets, geopolitical developments, smart-money positioning, and produces cited investment theses, scenario trees and daily research briefings.

**Not a trading system.** No order execution, no money movement.

---

## Status

| Phase | Status | Description |
|---|---|---|
| **Phase 0** | ✅ Complete | Repository, CLAUDE.md, plan, data-source register, domain model, ADRs |
| **Phase 1** | 🔲 Next | Application foundation: Next.js + FastAPI + PostgreSQL + Docker Compose + auth |
| **Phase 2** | 🔲 | First real-data slice: FRED macro series, end-to-end |
| **Phase 3** | 🔲 | Market watchlist (EOD/delayed, labeled) |
| **Phase 4** | 🔲 | Theses, scenarios, AI research agents |
| **Phase 5** | 🔲 | Smart-money v1: CFTC COT + SEC 13F + alerts |
| **Phase 6** | 🔲 | Agent observability UI + daily briefing |
| **Phase 7** | 🔲 | Email/WhatsApp notifications + cloud deployment |

---

## Quick start (Phase 1+)

```bash
cp .env.example .env
# Edit .env — only FRED_API_KEY is needed for real macro data.
# App boots without any API keys (providers show UNAVAILABLE status).

docker compose up --build
```

- Frontend: http://localhost:3000  
- API + Docs: http://localhost:8000/docs

---

## Key documents

- [`CLAUDE.md`](CLAUDE.md) — project rules, design tokens, commands, security rules
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — ordered phases and acceptance criteria
- [`docs/DATA_SOURCE_REGISTER.md`](docs/DATA_SOURCE_REGISTER.md) — provider terms, rate limits, verified status
- [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md) — core entities and relationships
- [`docs/ADR/`](docs/ADR/) — architecture decision records

---

## Design principles

- **Data provenance always:** every value shows provider, timestamp, freshness status and units.
- **Deterministic finance:** calculations are tested code; AI interprets, does not compute.
- **No fabricated data:** unavailable = `UNAVAILABLE`, stale = `STALE` — never a fake value.
- **AI claims need evidence:** every material claim links to a stored source.
- **No trade execution:** this terminal supports research decisions; it does not place orders.

---

*Private research tool. Not financial advice.*
