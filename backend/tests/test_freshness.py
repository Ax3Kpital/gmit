"""Freshness is judged from the observation date, never from the download time."""
from datetime import date, datetime, timezone

import pytest

from app.core import freshness as f


def utc(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


# 2026-11-20 is a Friday, 2026-11-21 a Saturday, 2026-11-23 a Monday.
@pytest.mark.parametrize("now,expected", [
    (utc(2026, 11, 21, 10, 28), date(2026, 11, 20)),   # Saturday -> Friday
    (utc(2026, 11, 22, 23, 59), date(2026, 11, 20)),   # Sunday -> Friday
    (utc(2026, 11, 23, 10, 0), date(2026, 11, 20)),    # Monday morning: Friday's close
    (utc(2026, 11, 23, 23, 0), date(2026, 11, 23)),    # Monday after the close
    (utc(2026, 11, 20, 12, 0), date(2026, 11, 19)),    # Friday midday: Thursday's close
    (utc(2026, 11, 18, 22, 31), date(2026, 11, 18)),   # just after the buffer
    (utc(2026, 11, 18, 22, 29), date(2026, 11, 17)),   # just before it
])
def test_last_expected_session(now, expected):
    assert f.last_expected_session(now) == expected


def test_weekdays_behind_skips_weekends():
    assert f.weekdays_behind(date(2026, 11, 20), date(2026, 11, 23)) == 1   # Fri -> Mon
    assert f.weekdays_behind(date(2026, 11, 19), date(2026, 11, 23)) == 2
    assert f.weekdays_behind(date(2026, 11, 20), date(2026, 11, 20)) == 0
    assert f.weekdays_behind(date(2026, 11, 23), date(2026, 11, 20)) == 0   # ahead is fine


SATURDAY = utc(2026, 11, 21, 10, 28)


@pytest.mark.parametrize("latest,status,lag", [
    (date(2026, 11, 20), "END_OF_DAY", 0),     # Friday close on Saturday: current
    (date(2026, 11, 19), "DELAYED", 1),        # one session late
    (date(2026, 11, 17), "STALE", 3),          # FRED WTI as the user saw it
    (date(2026, 11, 13), "STALE", 5),          # FRED FX as the user saw it
])
def test_classify_daily_on_saturday(latest, status, lag):
    r = f.classify_daily(latest, "END_OF_DAY", SATURDAY)
    assert (r.status, r.lag_sessions) == (status, lag)


def test_current_data_keeps_its_own_base_status():
    assert f.classify_daily(date(2026, 11, 20), "INDICATIVE", SATURDAY).status == "INDICATIVE"
    assert f.classify_daily(date(2026, 11, 20), "PERIODIC_OFFICIAL_RELEASE", SATURDAY).status == \
        "PERIODIC_OFFICIAL_RELEASE"


def test_live_bar_ahead_of_expected_is_current():
    midday = utc(2026, 11, 20, 14, 0)                       # Friday during the session
    assert f.classify_daily(date(2026, 11, 20), "DELAYED", midday).status == "DELAYED"


def test_missing_data_is_unavailable():
    assert f.classify_daily(None, "END_OF_DAY", SATURDAY).status == "UNAVAILABLE"


def test_recent_download_does_not_make_old_data_fresh():
    # The old bug: status followed `last_fetched_at`. Only the observation date counts now.
    assert f.classify_daily(date(2026, 11, 13), "END_OF_DAY", SATURDAY).status == "STALE"


@pytest.mark.parametrize("now,expected", [
    (utc(2026, 11, 21, 10, 0), date(2026, 11, 17)),    # released Fri 20 Nov for Tue 17 Nov
    (utc(2026, 11, 20, 12, 0), date(2026, 11, 10)),    # Friday before the release
    (utc(2026, 11, 20, 20, 31), date(2026, 11, 17)),   # right after the release
])
def test_expected_cot_report_date(now, expected):
    assert f.expected_cot_report_date(now) == expected


def test_classify_cot():
    now = utc(2026, 11, 21, 10, 0)
    assert f.classify_cot(date(2026, 11, 17), now) == "PERIODIC_OFFICIAL_RELEASE"
    assert f.classify_cot(date(2026, 11, 10), now) == "DELAYED"
    assert f.classify_cot(date(2026, 11, 3), now) == "STALE"
    assert f.classify_cot(None, now) == "UNAVAILABLE"


def test_age_label():
    assert f.age_label(date(2026, 11, 21), SATURDAY) == "today"
    assert f.age_label(date(2026, 11, 20), SATURDAY) == "1 day old"
    assert f.age_label(date(2026, 11, 13), SATURDAY) == "8 days old"
    assert f.age_label(None, SATURDAY) == "no data"


def test_cot_release_time_is_friday_for_the_tuesday_report():
    assert f.cot_release_time(date(2026, 11, 17)) == utc(2026, 11, 20, 20, 30)


def test_next_cot_release_is_a_week_after_the_newest_published():
    report, release = f.next_cot_release(utc(2026, 11, 21, 10, 0))         # Saturday after the 20th release
    assert report == date(2026, 11, 24) and release == utc(2026, 11, 27, 20, 30)
    report, release = f.next_cot_release(utc(2026, 11, 20, 12, 0))         # Friday before the release
    assert report == date(2026, 11, 17) and release == utc(2026, 11, 20, 20, 30)


@pytest.mark.parametrize("latest,now,status", [
    (date(2026, 10, 1), utc(2026, 11, 21), "PERIODIC_OFFICIAL_RELEASE"),    # October out by early November
    (date(2026, 9, 1), utc(2026, 11, 21), "DELAYED"),
    (date(2026, 8, 1), utc(2026, 11, 21), "STALE"),
    (date(2026, 10, 1), utc(2026, 11, 5), "PERIODIC_OFFICIAL_RELEASE"),     # grace period early in the month
    (date(2026, 9, 1), utc(2026, 11, 5), "PERIODIC_OFFICIAL_RELEASE"),
    (date(2026, 12, 1), utc(2027, 1, 20), "PERIODIC_OFFICIAL_RELEASE"),     # year boundary
    (date(2026, 11, 1), utc(2027, 1, 20), "DELAYED"),
    (None, utc(2026, 11, 21), "UNAVAILABLE"),
])
def test_classify_monthly(latest, now, status):
    assert f.classify_monthly(latest, now).status == status


def test_classify_fetch_age():
    now = utc(2026, 11, 21, 12, 0)
    assert f.classify_fetch_age(utc(2026, 11, 21, 10, 0), now, 8) == "DELAYED"
    assert f.classify_fetch_age(utc(2026, 11, 21, 3, 0), now, 8) == "STALE"
    assert f.classify_fetch_age(None, now, 8) == "UNAVAILABLE"


def test_cot_fetch_due_decision():
    from app.services.cot_ingestion import cot_fetch_due
    now = utc(2026, 11, 21, 12, 0)                                           # Saturday, report of the 17th is public
    fresh_fetch = utc(2026, 11, 21, 10, 0)
    assert cot_fetch_due(date(2026, 11, 17), fresh_fetch, now) is False      # up to date, fetched recently
    assert cot_fetch_due(date(2026, 11, 10), fresh_fetch, now) is True       # newer report should exist: keep polling
    assert cot_fetch_due(date(2026, 11, 17), utc(2026, 11, 20, 9, 0), now) is True   # >24 h: catch revisions
    assert cot_fetch_due(None, None, now) is True
    friday_before = utc(2026, 11, 20, 12, 0)                                 # release not due yet
    assert cot_fetch_due(date(2026, 11, 10), utc(2026, 11, 20, 11, 0), friday_before) is False
    friday_after = utc(2026, 11, 20, 20, 45)                                 # just after the release: poll
    assert cot_fetch_due(date(2026, 11, 10), utc(2026, 11, 20, 20, 20), friday_after) is True
