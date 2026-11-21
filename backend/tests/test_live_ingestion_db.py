"""Live-market storage and freshest-series resolution, against a real (throwaway) Postgres."""
from datetime import date, datetime, timedelta, timezone

from app.db.models.macro import MacroObservation, MacroSeries
from app.providers import treasury, yahoo
from app.services import live_market_ingestion as live
from app.services.series_catalog import LIVE_SERIES
from app.services.series_snapshot import build_snippets, resolve

NOW = datetime(2026, 11, 21, 10, 30, tzinfo=timezone.utc)      # Saturday
WTI = next(s for s in LIVE_SERIES if s.series_id == "CL=F")


def fred_series(db, sid, category="commodity", units="USD"):
    s = MacroSeries(series_id=sid, display_name=sid, category=category, title=sid, provider="fred",
                    source_url="https://fred.example/" + sid, units=units, data_status="END_OF_DAY")
    db.add(s)
    db.flush()
    return s


def add_obs(db, series, day, value, provider="fred", status="END_OF_DAY"):
    db.add(MacroObservation(macro_series_id=series.id, date=day, value=value, provider=provider,
                            source_url="u", retrieved_at=NOW, data_status=status, units=series.units))
    db.flush()


def quote(last_time, closes):
    days = sorted(closes)
    return yahoo.Quote("CL=F", [yahoo.Bar(d, closes[d]) for d in days], closes[days[-1]],
                       last_time, "https://finance.yahoo.com/quote/CL%3DF", NOW)


def test_store_quote_creates_series_and_observations(pg_db):
    q = quote(NOW - timedelta(hours=12), {date(2026, 11, 19): 83.2, date(2026, 11, 20): 83.98})
    assert live.store_quote(pg_db, WTI, q, NOW) == 2
    s = pg_db.query(MacroSeries).filter_by(series_id="CL=F").one()
    assert s.provider == "yahoo_finance" and s.units == "USD per barrel" and s.category == "commodity"
    obs = {o.date: o for o in pg_db.query(MacroObservation).filter_by(macro_series_id=s.id)}
    assert obs[date(2026, 11, 20)].value == 83.98
    assert obs[date(2026, 11, 20)].data_status == "END_OF_DAY"          # market closed: not live


def test_open_session_bar_is_marked_delayed_not_end_of_day(pg_db):
    q = quote(NOW - timedelta(minutes=5), {date(2026, 11, 20): 83.9, date(2026, 11, 21): 84.1})
    live.store_quote(pg_db, WTI, q, NOW)
    s = pg_db.query(MacroSeries).filter_by(series_id="CL=F").one()
    obs = {o.date: o for o in pg_db.query(MacroObservation).filter_by(macro_series_id=s.id)}
    assert obs[date(2026, 11, 21)].data_status == "DELAYED"
    assert obs[date(2026, 11, 21)].published_at is not None
    assert obs[date(2026, 11, 20)].data_status == "END_OF_DAY"


def test_store_quote_is_idempotent_and_updates_values(pg_db):
    live.store_quote(pg_db, WTI, quote(NOW, {date(2026, 11, 20): 83.0}), NOW)
    live.store_quote(pg_db, WTI, quote(NOW, {date(2026, 11, 20): 83.5}), NOW)
    s = pg_db.query(MacroSeries).filter_by(series_id="CL=F").one()
    rows = pg_db.query(MacroObservation).filter_by(macro_series_id=s.id).all()
    assert len(rows) == 1 and rows[0].value == 83.5


def test_store_yields_writes_official_values_and_computed_spread(pg_db):
    for sid in ("DGS2", "DGS10", "T10Y2Y"):
        fred_series(pg_db, sid, "macro", "Percent")
    pts = [treasury.YieldPoint(date(2026, 11, 20), 4.63, 4.92),
           treasury.YieldPoint(date(2026, 11, 19), None, 5.04)]
    assert live.store_yields(pg_db, pts, NOW) == 4          # the point without a 2Y skips DGS2 and the spread
    by = {s.series_id: s for s in pg_db.query(MacroSeries)}
    spread = pg_db.query(MacroObservation).filter_by(macro_series_id=by["T10Y2Y"].id).one()
    assert spread.value == 0.29 and spread.date == date(2026, 11, 20)
    assert spread.provider.startswith("us_treasury")
    dgs10 = pg_db.query(MacroObservation).filter_by(macro_series_id=by["DGS10"].id).count()
    assert dgs10 == 2


def test_fresher_live_series_answers_for_the_fred_series(pg_db):
    fred = fred_series(pg_db, "DCOILWTICO")
    add_obs(pg_db, fred, date(2026, 11, 17), 89.53)
    add_obs(pg_db, fred, date(2026, 10, 1), 80.0)
    lv = fred_series(pg_db, "CL=F")
    add_obs(pg_db, lv, date(2026, 11, 20), 83.98, "yahoo_finance")
    add_obs(pg_db, lv, date(2026, 10, 1), 79.0, "yahoo_finance")

    series, latest = resolve(pg_db, fred)
    assert series.series_id == "CL=F" and latest.date == date(2026, 11, 20)

    snips = build_snippets(pg_db)
    assert [s["series_id"] for s in snips] == ["DCOILWTICO"]          # no duplicate live entry
    wti = snips[0]
    assert wti["source_series_id"] == "CL=F" and wti["latest_value"] == 83.98
    assert wti["latest_date"] == "2026-11-20" and wti["provider"] == "yahoo_finance"
    # the 30-day change is taken inside the live series (83.98 vs 79.0), never mixed with FRED spot
    assert round(wti["delta30d"], 2) == 4.98


def test_fred_is_used_when_it_is_newer_or_live_has_no_data(pg_db):
    fred = fred_series(pg_db, "DCOILWTICO")
    add_obs(pg_db, fred, date(2026, 11, 20), 84.0)
    lv = fred_series(pg_db, "CL=F")
    add_obs(pg_db, lv, date(2026, 11, 18), 83.0, "yahoo_finance")
    assert resolve(pg_db, fred)[0].series_id == "DCOILWTICO"

    pg_db.query(MacroObservation).filter_by(macro_series_id=lv.id).delete()
    assert resolve(pg_db, fred)[0].series_id == "DCOILWTICO"


def test_series_without_alias_resolve_to_themselves(pg_db):
    dgs10 = fred_series(pg_db, "DGS10", "macro", "Percent")
    add_obs(pg_db, dgs10, date(2026, 11, 20), 4.92, "us_treasury", "PERIODIC_OFFICIAL_RELEASE")
    series, latest = resolve(pg_db, dgs10)
    assert series is dgs10 and latest.value == 4.92
