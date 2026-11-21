"""Data freshness classification.

Freshness is judged from the *observation date* against the latest date we could reasonably
expect today, never from the time we last downloaded the data. (A download that returns
8-day-old numbers is still 8-day-old data.)
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

# US cash close is 21:00 UTC (20:00 in summer); allow a buffer before today's close counts as expected.
_SESSION_CLOSED_UTC = time(22, 30)
# CFTC publishes Commitments of Traders on Friday 15:30 US Eastern (<= 20:30 UTC) for the prior Tuesday.
_COT_RELEASE_UTC = time(20, 30)


def last_expected_session(now: datetime) -> date:
    """Most recent weekday whose US market close has happened (holidays are not modelled)."""
    now = now.astimezone(timezone.utc)
    d = now.date()
    if now.time() < _SESSION_CLOSED_UTC:
        d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def weekdays_behind(latest: date, expected: date) -> int:
    """How many weekdays `latest` lags behind `expected` (0 when current or ahead)."""
    n, d = 0, latest
    while d < expected:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


@dataclass(frozen=True)
class Freshness:
    status: str          # one of the CLAUDE.md freshness labels
    lag_sessions: int    # weekdays behind the latest expected session
    expected_date: date


def classify_daily(latest: date | None, base_status: str, now: datetime) -> Freshness:
    """Daily market/macro series: current -> base status, one session late -> DELAYED, else STALE."""
    expected = last_expected_session(now)
    if latest is None:
        return Freshness("UNAVAILABLE", 0, expected)
    lag = weekdays_behind(latest, expected)
    if lag == 0:
        return Freshness(base_status, 0, expected)
    if lag == 1:
        return Freshness("DELAYED", 1, expected)
    return Freshness("STALE", lag, expected)


def expected_cot_report_date(now: datetime) -> date:
    """Report date (a Tuesday) of the newest COT release that should already be public."""
    now = now.astimezone(timezone.utc)
    d = now.date()
    for _ in range(21):
        if d.weekday() == 1:
            released = datetime.combine(d + timedelta(days=3), _COT_RELEASE_UTC, tzinfo=timezone.utc)
            if released <= now:
                return d
        d -= timedelta(days=1)
    return d


def cot_release_time(report_date: date) -> datetime:
    """When the COT report for a given Tuesday becomes public (Friday of that week)."""
    return datetime.combine(report_date + timedelta(days=3), _COT_RELEASE_UTC, tzinfo=timezone.utc)


def next_cot_release(now: datetime) -> tuple[date, datetime]:
    """(report date, release time) of the next COT report that is not public yet."""
    nxt = expected_cot_report_date(now) + timedelta(days=7)
    return nxt, cot_release_time(nxt)


def classify_cot(report_date: date | None, now: datetime) -> str:
    if report_date is None:
        return "UNAVAILABLE"
    expected = expected_cot_report_date(now)
    if report_date >= expected:
        return "PERIODIC_OFFICIAL_RELEASE"
    if report_date >= expected - timedelta(days=7):
        return "DELAYED"
    return "STALE"


def age_label(latest: date | None, now: datetime) -> str:
    """Human-readable age of the latest observation, for the UI."""
    if latest is None:
        return "no data"
    days = (now.astimezone(timezone.utc).date() - latest).days
    if days <= 0:
        return "today"
    if days == 1:
        return "1 day old"
    return f"{days} days old"


def _month_start(d: date, back: int = 0) -> date:
    m = d.year * 12 + (d.month - 1) - back
    return date(m // 12, m % 12 + 1, 1)


def classify_monthly(latest_period: date | None, now: datetime, publish_by_day: int = 10) -> Freshness:
    """Monthly releases (e.g. GPR): month M is expected early in M+1, so allow `publish_by_day`."""
    today = now.astimezone(timezone.utc).date()
    expected = _month_start(today, 1 if today.day > publish_by_day else 2)
    if latest_period is None:
        return Freshness("UNAVAILABLE", 0, expected)
    behind = (expected.year * 12 + expected.month) - (latest_period.year * 12 + latest_period.month)
    if behind <= 0:
        return Freshness("PERIODIC_OFFICIAL_RELEASE", 0, expected)
    if behind == 1:
        return Freshness("DELAYED", 1, expected)
    return Freshness("STALE", behind, expected)


def classify_fetch_age(last_fetched: datetime | None, now: datetime, max_age_hours: float,
                       base_status: str = "DELAYED") -> str:
    """Event/news feeds with no 'observation date': judged by how recently we fetched real data."""
    if last_fetched is None:
        return "UNAVAILABLE"
    age_h = (now - last_fetched).total_seconds() / 3600
    return base_status if age_h <= max_age_hours else "STALE"
