"""Platform-wide freshness report against a throwaway Postgres."""
from datetime import date, datetime, timedelta, timezone

from app.db.models.agent import Briefing
from app.db.models.geo import GeoEvent, GeoRiskIndex
from app.db.models.macro import MacroObservation, MacroSeries
from app.db.models.smart_money import CotInstrument, CotReport
from app.providers.gdelt import REGIONS
from app.services import data_health

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)      # Saturday


def series(db, sid, provider, day, status="END_OF_DAY", category="commodity", fetched=NOW):
    s = MacroSeries(series_id=sid, display_name=sid, category=category, title=sid, provider=provider,
                    source_url="u", units="u", data_status=status, last_fetched_at=fetched)
    db.add(s)
    db.flush()
    db.add(MacroObservation(macro_series_id=s.id, date=day, value=1.0, provider=provider, source_url="u",
                            retrieved_at=NOW, data_status=status, units="u"))
    db.flush()


def by_key(report):
    return {i["key"]: i for i in report["items"]}


def test_empty_database_reports_everything_unavailable_or_stale(pg_db):
    rep = data_health.collect(pg_db, NOW)
    items = by_key(rep)
    assert rep["healthy"] is False
    assert items["live_prices"]["status"] == "UNAVAILABLE"
    assert items["cot"]["status"] == "UNAVAILABLE"
    assert items["briefing"]["status"] == "STALE"


def test_fresh_data_everywhere_is_healthy_and_fred_lag_is_only_a_fallback_note(pg_db):
    series(pg_db, "CL=F", "yahoo_finance", date(2026, 11, 20))
    series(pg_db, "DGS10", "us_treasury", date(2026, 11, 20), "PERIODIC_OFFICIAL_RELEASE", "macro")
    series(pg_db, "DCOILWTICO", "fred", date(2026, 11, 17))                 # lagging FRED copy
    inst = CotInstrument(cftc_code="067651", name="n", display_name="WTI", category="commodity", exchange="x")
    pg_db.add(inst)
    pg_db.flush()
    pg_db.add(CotReport(instrument_id=inst.id, report_date=date(2026, 11, 17), net_noncomm=1.0,
                        retrieved_at=NOW, source_url="u"))
    pg_db.add(GeoRiskIndex(period=date(2026, 10, 1), gpr_value=150.0, retrieved_at=NOW))
    for key in REGIONS:
        pg_db.add(GeoEvent(region_key=key, region_label=key, event_date=NOW.date(), avg_tone=-1.0,
                           data_status="DELAYED", retrieved_at=NOW - timedelta(hours=1)))
    pg_db.add(Briefing(date=NOW.date(), macro_regime="risk_off", headline="h", generated_at=NOW))
    pg_db.flush()

    rep = data_health.collect(pg_db, NOW)
    items = by_key(rep)
    assert rep["healthy"] is True and rep["attention"] == []
    assert items["live_prices"]["latest_data"] == "2026-11-20"
    assert items["cot"]["status"] == "PERIODIC_OFFICIAL_RELEASE"
    assert "2026-11-24" in items["cot"]["detail"] and "2026-11-27 20:30 UTC" in items["cot"]["detail"]
    assert items["fred_history"]["status"] == "STALE" and items["fred_history"]["fallback"] is True
    assert items["gpr"]["status"] == "PERIODIC_OFFICIAL_RELEASE"
    assert items["gdelt"]["status"] == "DELAYED"


def test_partial_gdelt_coverage_needs_attention(pg_db):
    keys = list(REGIONS)
    for key in keys[:2]:                                                     # only 2 regions fetched
        pg_db.add(GeoEvent(region_key=key, region_label=key, event_date=NOW.date(), avg_tone=-1.0,
                           data_status="DELAYED", retrieved_at=NOW - timedelta(hours=1)))
    pg_db.flush()
    gdelt = by_key(data_health.collect(pg_db, NOW))["gdelt"]
    assert gdelt["status"] == "STALE"
    assert gdelt["detail"].startswith(f"2/{len(keys)} regions")


def test_new_cot_report_due_but_missing_is_delayed(pg_db):
    inst = CotInstrument(cftc_code="067651", name="n", display_name="WTI", category="commodity", exchange="x")
    pg_db.add(inst)
    pg_db.flush()
    pg_db.add(CotReport(instrument_id=inst.id, report_date=date(2026, 11, 10), net_noncomm=1.0,
                        retrieved_at=NOW, source_url="u"))
    pg_db.flush()
    cot = by_key(data_health.collect(pg_db, NOW))["cot"]
    assert cot["status"] == "DELAYED" and cot["expected"] == "2026-11-17"
