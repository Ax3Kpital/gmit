# GMIT — Data Source Register
**Last updated:** 2026-10-13  
**Rule:** Before implementing any provider, fill its row completely. `UNVERIFIED` means do not use in production. Never guess licenses or rate limits.

---

## How to read this register

| Field | What it means |
|---|---|
| **Status** | `VERIFIED` = terms and limits confirmed from official docs. `UNVERIFIED` = not yet reviewed. `REJECTED` = unsuitable (terms, cost, reliability). |
| **Freshness** | Actual data lag, not marketing claims |
| **Terms** | Personal/local use? Caching? Display? Redistribution? Commercial use? |
| **Rate limits** | Per-minute, per-day, per-key limits |
| **Last verified** | Date terms and endpoints were confirmed |

---

## A. Macro and official releases

### FRED (Federal Reserve Bank of St. Louis)
| Field | Value |
|---|---|
| **Status** | VERIFIED |
| **Datasets** | 800,000+ US and international economic series |
| **Access** | REST API, requires free API key registration at fred.stlouisfed.org |
| **Cost** | Free, no charge for personal/research use |
| **Terms** | Personal and research use permitted. Attribution required ("Source: FRED, Federal Reserve Bank of St. Louis"). Caching permitted. Redistribution of underlying data subject to original source terms (BLS, BEA, etc.). See: https://fred.stlouisfed.org/legal |
| **Attribution** | "Source: FRED, Federal Reserve Bank of St. Louis; [series name], [URL], retrieved [date]." |
| **Freshness** | Depends on series: some same-day, most next-business-day. Official release timestamps available. |
| **Rate limits** | 120 requests/min per API key (as of last check). Bulk download available for large backfills. |
| **Pagination** | Yes, `limit` and `offset` params |
| **Revision behavior** | Data is revised; ALFRED provides vintage/as-of-date history |
| **ALFRED** | Available at same API; allows point-in-time queries to avoid look-ahead bias |
| **Key series for MVP** | FEDFUNDS, DGS2, DGS10, DGS30, T10Y2Y, T10Y3M, CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, UNRATE, PAYEMS, GDPC1, DTWEXBGS (USD broad index), BAMLH0A0HYM2 (HY spread), DFII10 (10Y real yield), T10YIE (10Y breakeven) |
| **Fallback** | ALFRED vintage, bulk download |
| **Reliability** | High; occasional maintenance windows |
| **Last verified** | 2026-10-13 |

---

### BLS (Bureau of Labor Statistics)
| Field | Value |
|---|---|
| **Status** | VERIFIED (documentation reviewed) |
| **Datasets** | CPI, PPI, employment, wages, productivity |
| **Access** | REST API v2; API key recommended for higher limits |
| **Cost** | Free |
| **Terms** | Public data, attribution required. See: https://www.bls.gov/developers/termsOfService.htm |
| **Rate limits** | Without key: 25 series/request, 500 requests/day. With key: 50 series/request, 500 requests/day. |
| **Freshness** | Released on official schedule; same-day on release |
| **Last verified** | 2026-10-13 |
| **Note** | FRED mirrors most BLS series; prefer FRED API for consistency |

---

### U.S. Treasury (TreasuryDirect / fiscaldata.treasury.gov)
| Field | Value |
|---|---|
| **Status** | VERIFIED (documentation reviewed) |
| **Datasets** | Treasury yields, debt, TGA balance, securities |
| **Access** | `https://api.fiscaldata.treasury.gov/services/api/v1/` — no API key required |
| **Cost** | Free |
| **Terms** | Public domain data. See: https://fiscaldata.treasury.gov/api-documentation/ |
| **Freshness** | Depends on series; yield data published each business day |
| **Rate limits** | Documented in API docs; pagination via `page[number]` and `page[size]` |
| **Last verified** | 2026-10-13 |
| **Note** | FRED mirrors yield data; use Treasury directly only if FRED is unavailable or for non-mirrored series |

---

### ECB Data Portal / SDMX
| Field | Value |
|---|---|
| **Status** | VERIFIED (documentation reviewed) |
| **Datasets** | Euro-area rates, inflation, exchange rates, bank lending |
| **Access** | SDMX REST API at `https://data-api.ecb.europa.eu/` — no key required |
| **Cost** | Free |
| **Terms** | Public data. Attribution: "Source: European Central Bank". See: https://www.ecb.europa.eu/stats/html/index.en.html |
| **Freshness** | Reference rates updated daily (15:00 CET). Statistics on official schedule. |
| **Rate limits** | Not documented as strict; respect reasonable polling intervals |
| **Key series** | EXR (exchange rates), FM (financial market rates), ICP (inflation) |
| **Last verified** | 2026-10-13 |

---

### CFTC Commitments of Traders (COT)
| Field | Value |
|---|---|
| **Status** | VERIFIED |
| **Datasets** | Legacy COT, Traders in Financial Futures (TFF), Disaggregated COT |
| **Access** | File download (CSV/TXT) from cftc.gov; also available via CFTC public reporting environment and Socrata API |
| **Cost** | Free |
| **Terms** | Public data. Attribution: "Source: U.S. Commodity Futures Trading Commission". See: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm |
| **Freshness** | Data as of **Tuesday close**; published **Friday ~15:30 ET** — always show the Tuesday report date, not the retrieval date |
| **Rate limits** | Respect reasonable request rates; bulk historical files available |
| **Coverage** | Gold (GC), Silver (SI), WTI Crude (CL), Natural Gas (NG), S&P 500 E-mini (ES), Nasdaq E-mini (NQ), EUR/USD, USD/JPY, others |
| **Revision behavior** | Occasional corrections; re-download full weekly file |
| **Last verified** | 2026-10-13 |
| **Note** | Never label as real-time; weekly lag is structural |

---

### SEC EDGAR
| Field | Value |
|---|---|
| **Status** | VERIFIED |
| **Datasets** | 13F (institutional holdings), 4 (insider transactions), 8-K, 10-K, 10-Q, SC 13D/G, and others |
| **Access** | EDGAR EFTS full-text search: `https://efts.sec.gov/LATEST/search-index?q=...`; Company facts API: `https://data.sec.gov/submissions/CIK{cik}.json`; bulk JSON data: `https://data.sec.gov/api/xbrl/frames/` |
| **Cost** | Free |
| **Terms** | Public data. Identify your requests with a User-Agent header (company name + contact email per EDGAR requirements). Fair access policy: max 10 requests/sec. See: https://www.sec.gov/developer |
| **Freshness** | 13F: quarterly, filed within 45 days of quarter end — always show the **as-of date** (end of reporting quarter) separately from the **filing date** |
| **Rate limits** | 10 requests/second; be conservative |
| **13F notes** | Covers only reportable US institutional investment managers (>$100M AUM). Does not capture: short positions, options fully, foreign holdings outside US-listed instruments. Always display interpretation limits. |
| **Last verified** | 2026-10-13 |

---

## B. Market data

### Alpha Vantage
| Field | Value |
|---|---|
| **Status** | UNVERIFIED — terms and data quality not yet confirmed for our specific use case |
| **Datasets** | Stocks, FX, commodities, technical indicators, economic indicators |
| **Access** | REST API, free tier requires API key |
| **Cost** | Free tier available; premium tiers for higher limits and more data |
| **Terms** | Review: https://www.alphavantage.co/terms_of_service/ — must verify: caching policy, display rights, redistribution, commercial use |
| **Rate limits** | Free tier: 25 requests/day (as of last public documentation — verify current limits) |
| **Freshness** | Intraday data may be delayed on free tier; EOD typically available. Must confirm per data type. |
| **Last verified** | NOT YET — required before Phase 3 implementation |
| **Action required** | Verify: (1) current free-tier rate limits, (2) whether EOD commodity data is available, (3) caching and display terms, (4) whether personal use is sufficient or commercial license needed |

---

### Yahoo Finance (unofficial)
| Field | Value |
|---|---|
| **Status** | UNVERIFIED — no official API; terms prohibit scraping |
| **Note** | Used in bvb_project for BVB .RO tickers as a fallback. Terms of service do not permit automated access. Not suitable as a primary or reliable source. Use only as last-resort fallback for development, clearly labeled, with a plan to replace. |
| **Action required** | Do not build production features that depend on this source |

---

### Stooq
| Field | Value |
|---|---|
| **Status** | UNVERIFIED |
| **Note** | Possible source for historical EOD data. Terms, rate limits and data quality not confirmed. |
| **Action required** | Review terms before any implementation |

---

### EIA (U.S. Energy Information Administration)
| Field | Value |
|---|---|
| **Status** | VERIFIED (documentation reviewed) |
| **Datasets** | Oil/gas production, storage, consumption, prices, electric power, renewables |
| **Access** | REST API v2 at `https://api.eia.gov/v2/` — free API key required |
| **Cost** | Free |
| **Terms** | Public data. Attribution: "Source: U.S. Energy Information Administration". See: https://www.eia.gov/about/copyrights_reuse.php |
| **Rate limits** | Documented in API; respect limits |
| **Key series** | Weekly petroleum status (crude, gasoline), natural gas storage, Henry Hub spot price history |
| **Freshness** | Weekly reports on official EIA schedule; some series daily |
| **Last verified** | 2026-10-13 |

---

## C. News and events

### GDELT Project
| Field | Value |
|---|---|
| **Status** | VERIFIED (documentation reviewed) |
| **Datasets** | Global news event monitoring, 100+ languages, entity extraction, tone, themes |
| **Access** | BigQuery (full), bulk file downloads at gdeltproject.org, and TV-API |
| **Cost** | Bulk files free; BigQuery has GCP costs above free tier |
| **Terms** | Open/public. Attribution: "GDELT Project". See: https://www.gdeltproject.org/about.html |
| **Freshness** | Updates every 15 minutes |
| **Use case** | Event discovery and clustering; NOT a primary factual source — cross-verify with official sources |
| **Rate limits** | Bulk files: no API key; BigQuery: standard GCP quotas |
| **Last verified** | 2026-10-13 |
| **Note** | Useful for discovering events at scale; must not be presented as authoritative. News tone and event codes can be noisy. |

---

### RSS / official releases
| Field | Value |
|---|---|
| **Status** | VERIFIED in principle — individual feeds must be confirmed |
| **Sources** | Federal Reserve, ECB, Bank of England, BOJ, U.S. Treasury, USTR, European Commission, IMF, World Bank, BIS, CFTC, SEC |
| **Access** | Standard RSS/Atom feeds; no API key for most |
| **Terms** | Public official releases; standard web terms apply. Do not republish full articles. Cache headlines and metadata only. |
| **Freshness** | Real-time on publication |
| **Implementation** | Polling interval: 5–15 minutes; deduplicate by `guid` or URL |

---

## D. Providers requiring further investigation before use

| Provider | What we need to verify |
|---|---|
| Frankfurter.app | Already used in bvb_project for ECB FX rates — confirm terms for GMIT use |
| ALFRED (St. Louis Fed) | Confirm vintage/as-of-date API availability for look-ahead-free backtesting |
| ETF flow data (any) | No confirmed free source for reliable net-creation/redemption data; needs investigation |
| Options/dealer positioning | No confirmed suitable free source; defer to Phase 7+ |
| WhatsApp Business API | Requires business account, template approval, per-message costs; verify before Phase 7 |

---

## Provider interface names (code)

| Interface | Purpose |
|---|---|
| `MacroSeriesProvider` | Official macro time series (FRED, BLS, ECB, etc.) |
| `MarketQuoteProvider` | Market prices, FX rates, commodity quotes |
| `HistoricalMarketDataProvider` | EOD bars and historical series |
| `NewsSearchProvider` | Event and news discovery |
| `OfficialReleaseProvider` | Central bank / government release parsing |
| `EconomicCalendarProvider` | Scheduled economic event calendar |
| `PositioningDataProvider` | CFTC COT and similar positioning data |
| `FilingsProvider` | SEC EDGAR, insider disclosures |
| `NotificationProvider` | In-app, email, WhatsApp delivery |
