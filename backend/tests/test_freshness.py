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
