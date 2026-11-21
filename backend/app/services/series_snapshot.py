"""Single source of truth for 'latest value + 30-day change' of each macro/market series.

Used by the signals endpoint, the briefing, the research engine, the watchlist and alerts so that
all of them see the same, freshest data. A FRED series is answered by its near-real-time
counterpart (see series_catalog) whenever that one is at least as recent.
"""
from datetime import date as date_type, timedelta

from sqlalchemy.orm import Session

from app.db.models.macro import MacroObservation, MacroSeries
from app.services.series_catalog import LIVE_ALIAS, LIVE_IDS

_CHANGE_WINDOW_DAYS = 35


def latest_observation(db: Session, series: MacroSeries) -> MacroObservation | None:
    return (db.query(MacroObservation)
            .filter(MacroObservation.macro_series_id == series.id, MacroObservation.value.isnot(None))
            .order_by(MacroObservation.date.desc()).first())


def _previous(db: Session, series: MacroSeries, cutoff: date_type) -> MacroObservation | None:
    return (db.query(MacroObservation)
            .filter(MacroObservation.macro_series_id == series.id, MacroObservation.value.isnot(None),
                    MacroObservation.date <= cutoff)
            .order_by(MacroObservation.date.desc()).first())


def resolve(db: Session, series: MacroSeries,
            by_id: dict[str, MacroSeries] | None = None) -> tuple[MacroSeries, MacroObservation | None]:
    """The series (itself or its fresher alias) that should answer for `series`, with its latest point."""
    latest = latest_observation(db, series)
    alias_id = LIVE_ALIAS.get(series.series_id)
    if alias_id:
        alias = (by_id or {}).get(alias_id) or db.query(MacroSeries).filter(
            MacroSeries.series_id == alias_id).first()
        if alias:
            alias_latest = latest_observation(db, alias)
            if alias_latest and (latest is None or alias_latest.date >= latest.date):
                return alias, alias_latest
    return series, latest


def build_snippets(db: Session) -> list[dict]:
    rows = db.query(MacroSeries).all()
    by_id = {s.series_id: s for s in rows}
    cutoff = date_type.today() - timedelta(days=_CHANGE_WINDOW_DAYS)
    snippets: list[dict] = []
    for s in rows:
        if s.series_id in LIVE_IDS:
            continue                     # answered through its FRED counterpart below
        chosen, latest = resolve(db, s, by_id)
        if latest is None:
            continue
        prev = _previous(db, chosen, cutoff)
        delta = delta_pct = None
        if prev and prev.value:
            delta = latest.value - prev.value
            delta_pct = delta / abs(prev.value) * 100
        snippets.append({
            "series_id": s.series_id,
            "source_series_id": chosen.series_id,
            "display_name": chosen.display_name or chosen.series_id,
            "latest_value": latest.value,
            "latest_date": latest.date.isoformat(),
            "delta30d": delta,
            "delta30d_pct": delta_pct,
            "units": chosen.units or "",
            "category": s.category,
            "provider": latest.provider,
            "data_status": latest.data_status,
        })
    return snippets
