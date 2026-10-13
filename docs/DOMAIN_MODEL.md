# GMIT — Domain Model
**Last updated:** 2026-10-13  
**Status:** Initial draft — subject to revision before Phase 1 migration

---

## Core principles

- Every entity has stable UUIDs, `created_at`, `updated_at`.
- No silent overwrites: macro observations and thesis updates are append-only; history is preserved.
- Raw payloads and normalized data are separated.
- Source provenance is a first-class field, not an afterthought.

---

## Identity and configuration

### User
Single user for MVP. Architecture supports multi-user (separate rows per user) without multi-tenant complexity.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | varchar | unique |
| password_hash | varchar | Argon2id |
| created_at | timestamptz | |
| last_login_at | timestamptz | nullable |
| is_active | bool | |

### UserSettings
| Field | Type | Notes |
|---|---|---|
| user_id | UUID FK → User | |
| timezone | varchar | default `Europe/Bucharest` |
| default_currency | varchar | default `USD` |
| alert_quiet_hours_start | time | nullable |
| alert_quiet_hours_end | time | nullable |
| daily_briefing_time | time | nullable |
| preferences_json | jsonb | extensible settings |

### Workspace / Watchlist
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | |
| name | varchar | |
| description | text | nullable |
| is_default | bool | |

### WatchlistItem
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| watchlist_id | UUID FK | |
| instrument_id | UUID FK | |
| display_order | int | |
| notes | text | nullable |

---

## Data providers and ingestion

### Provider
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| code | varchar | unique slug, e.g. `fred`, `cftc_cot`, `sec_edgar` |
| name | varchar | |
| base_url | varchar | |
| auth_type | enum | `none`, `api_key`, `oauth`, `download` |
| terms_url | varchar | |
| license_tag | varchar | e.g. `public_domain`, `free_personal`, `commercial_license_required` |
| rate_limit_per_minute | int | nullable |
| rate_limit_per_day | int | nullable |
| attribution_text | text | required attribution string |
| is_active | bool | |
| notes | text | |

### ProviderHealth
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | |
| checked_at | timestamptz | |
| status | enum | `ok`, `degraded`, `down`, `unknown` |
| latency_ms | int | nullable |
| error_message | text | nullable |

### IngestionRun
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | |
| dataset_code | varchar | which specific dataset/series was fetched |
| started_at | timestamptz | |
| completed_at | timestamptz | nullable |
| status | enum | `running`, `success`, `partial`, `failed` |
| records_fetched | int | |
| records_inserted | int | |
| records_updated | int | |
| error_message | text | nullable |

### DataQualityIssue
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| ingestion_run_id | UUID FK | nullable |
| provider_id | UUID FK | |
| issue_type | enum | `stale`, `missing_field`, `unit_mismatch`, `duplicate`, `schema_change`, `value_anomaly` |
| severity | enum | `info`, `warning`, `critical` |
| description | text | |
| detected_at | timestamptz | |
| resolved_at | timestamptz | nullable |

---

## Instruments and market data

### Instrument
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| symbol | varchar | primary symbol |
| name | varchar | |
| asset_class | enum | `equity`, `equity_index`, `commodity`, `fx_pair`, `fixed_income`, `etf`, `futures` |
| exchange | varchar | nullable |
| currency | varchar | ISO 4217 |
| units | varchar | e.g. `USD/oz`, `USD/bbl`, `index_points` |
| contract_type | enum | `spot`, `front_month_futures`, `continuous_futures`, `etf_proxy`, `reference_rate` |
| data_status | enum | freshness label (see CLAUDE.md) |
| primary_provider_id | UUID FK | nullable |
| notes | text | |

### InstrumentAlias
| Field | Type | Notes |
|---|---|---|
| instrument_id | UUID FK | |
| provider_id | UUID FK | |
| provider_symbol | varchar | symbol as the provider knows it |

### MarketObservation
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| instrument_id | UUID FK | |
| provider_id | UUID FK | |
| price | numeric(20,8) | |
| open | numeric(20,8) | nullable |
| high | numeric(20,8) | nullable |
| low | numeric(20,8) | nullable |
| close | numeric(20,8) | nullable |
| volume | numeric(20,2) | nullable |
| observed_at | timestamptz | the market timestamp |
| published_at | timestamptz | nullable — when provider made it available |
| retrieved_at | timestamptz | when we fetched it |
| data_status | enum | |
| source_url | varchar | nullable |
| raw_payload_hash | varchar | SHA-256 of raw provider response |

---

## Macro data

### MacroSeries
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | |
| provider_series_id | varchar | e.g. `DGS10`, `CPIAUCSL` |
| name | varchar | |
| description | text | |
| units | varchar | e.g. `percent`, `index_2015=100`, `thousands_of_persons` |
| frequency | enum | `daily`, `weekly`, `monthly`, `quarterly`, `annual` |
| seasonal_adjustment | varchar | `SA`, `NSA`, `SAAR`, `none` |
| source_agency | varchar | e.g. `BLS`, `BEA`, `Federal Reserve` |
| notes | text | |

### MacroObservation
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| series_id | UUID FK → MacroSeries | |
| observation_date | date | the period this value covers |
| value | numeric(20,6) | |
| vintage_date | date | nullable — "as of" date for point-in-time queries (ALFRED) |
| is_revised | bool | true if a later vintage changed this value |
| published_at | timestamptz | nullable |
| retrieved_at | timestamptz | |
| data_status | enum | |
| source_url | varchar | nullable |

### ReleaseEvent
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| series_id | UUID FK | nullable |
| name | varchar | e.g. "US CPI — March 2026" |
| expected_at | timestamptz | scheduled release time |
| actual_at | timestamptz | nullable — when actually released |
| prior_value | numeric | nullable |
| consensus_value | numeric | nullable — only if sourced legally |
| actual_value | numeric | nullable |
| surprise_direction | enum | nullable — `beat`, `miss`, `inline` |

---

## News, filings and evidence

### SourceDocument
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | |
| url | varchar | canonical URL |
| title | text | |
| published_at | timestamptz | |
| retrieved_at | timestamptz | |
| source_type | enum | `news`, `press_release`, `filing`, `official_statement`, `research`, `data_release` |
| summary | text | nullable — AI-generated excerpt/summary, not the full article |
| entities_json | jsonb | extracted entities |
| themes_json | jsonb | classified topics |
| is_verified | bool | cross-source confirmation |

### EvidenceItem
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| source_document_id | UUID FK | nullable |
| macro_observation_id | UUID FK | nullable |
| market_observation_id | UUID FK | nullable |
| claim | text | the specific claim supported/refuted |
| supports_thesis | bool | true = supports, false = refutes |
| confidence | enum | `low`, `medium`, `high` |
| retrieved_at | timestamptz | |
| notes | text | |

---

## Research: theses and scenarios

### Thesis
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | |
| title | varchar | |
| claim | text | the central hypothesis |
| status | enum | `draft`, `active`, `monitoring`, `invalidated`, `archived` |
| asset_class_focus | varchar | |
| time_horizon | enum | `days`, `weeks`, `months`, `quarters`, `years` |
| created_at | timestamptz | |
| last_reviewed_at | timestamptz | |

### ThesisUpdate
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| thesis_id | UUID FK | |
| updated_at | timestamptz | |
| updated_by | enum | `user`, `ai_agent` |
| agent_run_id | UUID FK | nullable |
| change_summary | text | what changed and why |
| previous_status | enum | nullable |
| new_status | enum | nullable |

### Scenario
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| thesis_id | UUID FK | |
| name | varchar | e.g. "Base case", "Bull", "Bear", "Tail risk" |
| description | text | |
| probability_estimate | numeric(5,4) | 0.0–1.0; null = insufficient data |
| probability_basis | text | rationale for the estimate |
| confidence | enum | `low`, `medium`, `high`, `insufficient_data` |
| timeline_notes | text | |
| created_at | timestamptz | |

### ProbabilityAssessment
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| scenario_id | UUID FK | |
| assessed_at | timestamptz | |
| assessed_by | enum | `user`, `ai_agent` |
| agent_run_id | UUID FK | nullable |
| probability | numeric(5,4) | |
| rationale | text | |
| model_id | varchar | nullable — which LLM model was used |

### Catalyst
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| scenario_id | UUID FK | |
| description | text | |
| expected_timing | text | nullable |
| has_triggered | bool | default false |
| triggered_at | timestamptz | nullable |

### InvalidationCondition
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| thesis_id | UUID FK | |
| condition | text | observable condition that would invalidate the thesis |
| has_triggered | bool | default false |
| triggered_at | timestamptz | nullable |

### CounterArgument
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| thesis_id | UUID FK | |
| argument | text | |
| source_document_id | UUID FK | nullable |
| agent_run_id | UUID FK | nullable |
| created_at | timestamptz | |

---

## Smart money and positioning

### PositioningReport
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | e.g. CFTC COT |
| instrument_id | UUID FK | |
| report_date | date | Tuesday for COT |
| published_date | date | Friday for COT |
| retrieved_at | timestamptz | |
| report_type | enum | `cot_legacy`, `cot_tff`, `cot_disaggregated` |
| net_position | numeric | |
| long_contracts | int | nullable |
| short_contracts | int | nullable |
| open_interest | int | nullable |
| net_change_week | numeric | nullable — calculated from prior week |
| percentile_52w | numeric | nullable — historical percentile |
| data_status | enum | |

### InstitutionalFiling
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| provider_id | UUID FK | SEC EDGAR |
| filer_cik | varchar | |
| filer_name | varchar | |
| form_type | varchar | e.g. `13F-HR`, `SC 13G`, `4` |
| as_of_date | date | end of reporting period — ALWAYS different from filing_date |
| filing_date | date | when filed with SEC |
| retrieved_at | timestamptz | |
| total_value_usd | numeric | nullable |
| holdings_json | jsonb | normalized holdings list |
| raw_url | varchar | EDGAR document URL |

---

## Signals and alerts

### Signal
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| signal_type | enum | `cot_extreme`, `filing_change`, `price_threshold`, `macro_surprise`, `scenario_change`, `data_quality` |
| instrument_id | UUID FK | nullable |
| thesis_id | UUID FK | nullable |
| description | text | |
| evidence_type | varchar | what data supports this signal |
| data_source | varchar | provider and series |
| observation_date | date | |
| known_lag | text | e.g. "COT data is 3 days old on publication" |
| confidence | enum | `low`, `medium`, `high` |
| alternative_explanations | text | |
| created_at | timestamptz | |
| agent_run_id | UUID FK | nullable |

### AlertRule
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | |
| name | varchar | |
| rule_type | enum | `price_threshold`, `pct_change`, `cot_percentile`, `macro_release`, `scenario_probability_change`, `data_stale` |
| condition_json | jsonb | rule parameters |
| severity | enum | `info`, `warning`, `critical` |
| cooldown_minutes | int | minimum minutes between repeated alerts |
| is_active | bool | |

### AlertEvent
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| rule_id | UUID FK | |
| signal_id | UUID FK | nullable |
| triggered_at | timestamptz | |
| message | text | |
| context_json | jsonb | what changed, source, timestamp, lag |
| deduplication_key | varchar | unique key; prevents duplicate alerts for same condition |

### NotificationDelivery
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| alert_event_id | UUID FK | |
| channel | enum | `in_app`, `email`, `whatsapp` |
| status | enum | `queued`, `sent`, `delivered`, `failed` |
| attempted_at | timestamptz | |
| delivered_at | timestamptz | nullable |
| error_message | text | nullable |
| retry_count | int | |

---

## Agent execution

### AgentRun
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| run_type | enum | `scheduled_monitoring`, `event_triggered`, `daily_briefing`, `on_demand`, `watch_mode` |
| trigger | text | what initiated this run |
| started_at | timestamptz | |
| completed_at | timestamptz | nullable |
| status | enum | `running`, `completed`, `failed`, `budget_exceeded` |
| token_budget | int | |
| tokens_used | int | nullable |
| cost_usd | numeric(10,6) | nullable |
| model_calls_count | int | |
| thesis_id | UUID FK | nullable — if triggered by a specific thesis |

### AgentTask
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| run_id | UUID FK | |
| agent_role | enum | `orchestrator`, `macro`, `market_flow`, `geopolitics`, `transmission`, `scenario`, `skeptic`, `synthesizer`, `alert_curator`, `data_quality` |
| task_description | text | |
| status | enum | `pending`, `running`, `completed`, `skipped`, `failed` |
| started_at | timestamptz | nullable |
| completed_at | timestamptz | nullable |

### AgentEvent
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| run_id | UUID FK | |
| task_id | UUID FK | nullable |
| event_type | enum | `run_started`, `task_assigned`, `source_fetched`, `tool_call`, `tool_result`, `model_call`, `model_result`, `handoff`, `validation`, `retry`, `error`, `completion` |
| sequence_number | int | ordering within a run |
| occurred_at | timestamptz | |
| payload_json | jsonb | event-specific details |

### ModelCall
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| run_id | UUID FK | |
| task_id | UUID FK | nullable |
| provider | varchar | e.g. `anthropic`, `openai` |
| model_id | varchar | e.g. `claude-sonnet-4-5`, `gpt-4o` |
| prompt_tokens | int | |
| completion_tokens | int | |
| cost_usd | numeric(10,6) | nullable |
| latency_ms | int | |
| called_at | timestamptz | |
| status | enum | `success`, `error`, `timeout` |

---

## Audit

### AuditLog
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | nullable |
| action | varchar | e.g. `login`, `change_alert_rule`, `configure_provider` |
| entity_type | varchar | nullable |
| entity_id | UUID | nullable |
| occurred_at | timestamptz | |
| ip_address | varchar | nullable |
| metadata_json | jsonb | additional context |
