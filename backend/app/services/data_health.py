"""Platform-wide data freshness report: one row per data source, judged against what should exist now."""
from datetime import datetime, timedelta

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.core.freshness import (classify_cot, classify_daily, classify_monthly,
                                expected_cot_report_date, next_cot_release)
from app.db.models.agent import Briefing
from app.db.models.geo import GeoEvent, GeoRiskIndex
from app.db.models.macro import MacroSeries
from app.db.models.smart_money import CotReport
from app.providers.gdelt import REGIONS
from app.services.series_catalog import LIVE_IDS
from app.services.series_snapshot import latest_observation

# worst-first ordering used to roll several series up into one row
_SEVERITY = {"UNAVAILABLE": 3, "STALE": 3, "DELAYED": 1}
GDELT_MAX_AGE_HOURS = 8        # data older than this is labelled STALE


def _worst(statuses: list[str]) -> str:
    return max(statuses, key=lambda s: _SEVERITY.get(s, 0)) if statuses else "UNAVAILABLE"


def _iso(d) -> str | None:
    return d.isoformat() if d else None


def _series_row(db: Session, now: datetime, ids, *, provider_prefix: str | None = None):
    """(oldest latest-date, worst status, newest fetch time) across the given series."""
    dates, statuses, fetched = [], [], []
    for s in db.query(MacroSeries).filter(MacroSeries.series_id.in_(ids)).all():
        obs = latest_observation(db, s)
        if obs is None or (provider_prefix and not obs.provider.startswith(provider_prefix)):
            statuses.append("UNAVAILABLE")
            continue
        dates.append(obs.date)
        statuses.append(classify_daily(obs.date, obs.data_status, now).status)
        if s.last_fetched_at:
            fetched.append(s.last_fetched_at)
    return (min(dates) if dates else None), _worst(statuses), (max(fetched) if fetched else None)


def collect(db: Session, now: datetime, next_runs: dict[str, datetime | None] | None = None) -> dict:
    next_runs = next_runs or {}
    items: list[dict] = []

    def add(key, label, cadence, job, latest, expected, status, fetched, detail, fallback=False):
        nxt = next_runs.get(job)
        items.append({
            "key": key, "label": label, "cadence": cadence, "fallback": fallback,
            "latest_data": _iso(latest), "expected": _iso(expected), "status": status,
            "last_fetched_at": _iso(fetched), "next_run_at": _iso(nxt), "detail": detail,
        })

    # 1. live prices
    latest, status, fetched = _series_row(db, now, LIVE_IDS)
    expected = classify_daily(latest, "END_OF_DAY", now).expected_date
    add("live_prices", "Prices: oil, gas, indices, FX (Yahoo Finance)", "every 10 min", "live_market_ingestion",
        latest, expected, status, fetched, "Latest completed or in-progress session.")

    # 2. official Treasury yields
    latest, status, fetched = _series_row(db, now, ("DGS2", "DGS10"), provider_prefix="us_treasury")
    add("treasury_yields", "US Treasury yields 2Y / 10Y (official)", "every 30 min", "treasury_ingestion",
        latest, classify_daily(latest, "END_OF_DAY", now).expected_date, status, fetched,
        "Published the evening of each trading day.")

    # 3. FRED history (fallback only)
    fred_ids = [s.series_id for s in db.query(MacroSeries).all()
                if s.series_id not in LIVE_IDS and s.category in ("commodity", "equity", "fx")]
    latest, status, fetched = _series_row(db, now, fred_ids)
    add("fred_history", "FRED market series (history and fallback)", "hourly", "macro_ingestion",
        latest, classify_daily(latest, "END_OF_DAY", now).expected_date, status, fetched,
        "FRED publishes these with a delay of days; live prices take precedence.", fallback=True)

    # 4. COT (weekly)
    newest = db.query(func.max(CotReport.report_date)).scalar()
    fetched = db.query(func.max(CotReport.retrieved_at)).scalar()
    nxt_report, nxt_release = next_cot_release(now)
    add("cot", "CFTC Commitments of Traders (smart money)", "weekly: Fridays 20:30 UTC", "cot_ingestion",
        newest, expected_cot_report_date(now), classify_cot(newest, now), fetched,
        f"Weekly by design. Next report: positions of {nxt_report.isoformat()}, "
        f"published {nxt_release.strftime('%Y-%m-%d %H:%M UTC')}.")

    # 5. GPR (monthly)
    period = db.query(func.max(GeoRiskIndex.period)).scalar()
    fetched = db.query(func.max(GeoRiskIndex.retrieved_at)).scalar()
    fr = classify_monthly(period, now)
    add("gpr", "Geopolitical Risk Index (GPR)", "monthly release", "geo_ingestion",
        period, fr.expected_date, fr.status, fetched, "Published in the first days of the following month.")

    # 6. GDELT (news tone): every region should have recent data
    fetched = db.query(func.max(GeoEvent.retrieved_at)).filter(GeoEvent.avg_tone.isnot(None)).scalar()
    fresh_regions = (db.query(func.count(distinct(GeoEvent.region_key)))
                     .filter(GeoEvent.avg_tone.isnot(None),
                             GeoEvent.retrieved_at > now - timedelta(hours=GDELT_MAX_AGE_HOURS)).scalar() or 0)
    total = len(REGIONS)
    if fresh_regions == total:
        gstatus = "DELAYED"
    else:
        gstatus = "STALE" if fetched is not None else "UNAVAILABLE"
    add("gdelt", "GDELT news tone by region", "retries every 30 min", "geo_ingestion", None, None, gstatus, fetched,
        f"{fresh_regions}/{total} regions have tone data from the last {GDELT_MAX_AGE_HOURS} h; "
        "GDELT rate-limits clients, so missing regions show a labelled fallback.")

    # 7. daily briefing
    bdate = db.query(func.max(Briefing.date)).scalar()
    today = now.date()
    add("briefing", "Daily briefing", "daily 07:00 UTC and after the US close", "daily_briefing",
        bdate, today, "END_OF_DAY" if bdate == today else "STALE",
        db.query(func.max(Briefing.generated_at)).scalar(), "Built from the data above.")

    core = [i for i in items if not i["fallback"]]
    bad = [i for i in core if i["status"] in ("STALE", "UNAVAILABLE")]
    return {"as_of": now.isoformat(), "healthy": not bad,
            "attention": [i["key"] for i in bad], "items": items}
