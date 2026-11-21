from app.services.series_catalog import LIVE_ALIAS, LIVE_IDS, LIVE_SERIES


def test_every_fred_series_has_exactly_one_live_counterpart():
    assert len(LIVE_ALIAS) == len(LIVE_SERIES) == len(LIVE_IDS)


def test_live_ids_never_collide_with_logical_ids():
    assert not (set(LIVE_ALIAS) & set(LIVE_IDS))


def test_units_orientation_matches_the_fred_series_they_replace():
    by_logical = {s.logical_id: s for s in LIVE_SERIES}
    assert by_logical["DEXUSEU"].units == "USD per EUR"     # DEXUSEU is USD per EUR
    assert by_logical["DEXJPUS"].units == "JPY per USD"     # DEXJPUS is JPY per USD
    assert by_logical["DEXUSUK"].units == "USD per GBP"
    assert by_logical["DEXCHUS"].units == "CNY per USD"
    assert by_logical["DCOILWTICO"].units == "USD per barrel"


def test_categories_are_the_ones_the_watchlist_shows():
    assert {s.category for s in LIVE_SERIES} <= {"commodity", "equity", "fx"}
