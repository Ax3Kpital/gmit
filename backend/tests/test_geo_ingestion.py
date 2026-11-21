"""Geo ingestion: only missing regions are fetched, failed fetches never hide good data."""
from datetime import date, datetime, timedelta, timezone

from app.api.routes.geo import get_risk_summary
from app.db.models.geo import GeoEvent
from app.providers.gdelt import REGIONS
from app.services.geo_ingestion import regions_needing_gdelt

NOW = datetime.now(timezone.utc)


def test_only_regions_without_fresh_data_are_fetched():
    keys = list(REGIONS)
    assert regions_needing_gdelt(set()) == keys
    assert regions_needing_gdelt(set(keys[:2])) == keys[2:]
    assert regions_needing_gdelt(set(keys)) == []


def event(db, key, tone, age_h, status="DELAYED"):
    db.add(GeoEvent(region_key=key, region_label=key, event_date=date.today(), avg_tone=tone,
                    data_status=status, retrieved_at=NOW - timedelta(hours=age_h)))
    db.flush()


def regions(db):
    return {r["region_key"]: r for r in get_risk_summary(_auth=None, db=db)["regions"]}


def test_summary_prefers_the_row_with_data_over_a_newer_failed_row(pg_db):
    event(pg_db, "middle_east", -6.0, 2)
    event(pg_db, "middle_east", None, 0.1, "UNAVAILABLE")            # newer, but a failed fetch
    r = regions(pg_db)["middle_east"]
    assert r["avg_tone"] == -6.0 and r["data_status"] == "DELAYED"
    assert r["risk_level"] == "critical"


def test_summary_labels_old_data_stale_and_missing_data_unavailable(pg_db):
    event(pg_db, "taiwan_strait", -3.0, 30)                          # older than the allowed age
    out = regions(pg_db)
    assert out["taiwan_strait"]["data_status"] == "STALE"
    assert out["taiwan_strait"]["avg_tone"] == -3.0                  # still shown, but flagged
    assert out["eastern_europe"]["data_status"] == "UNAVAILABLE"     # never fetched
    assert out["eastern_europe"]["avg_tone"] is None
