"""Near-real-time market data: Yahoo Finance (oil, gas, indices, FX) and U.S. Treasury yields."""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models.macro import MacroObservation, MacroSeries
from app.db.session import SessionLocal
from app.providers import treasury, yahoo
from app.services.series_catalog import LIVE_SERIES, LiveSeries

logger = logging.getLogger("gmit.live")

_PAUSE_BETWEEN_SYMBOLS_S = 1.0


def _upsert_observation(db: Session, series: MacroSeries, *, day, value: float, provider: str,
                        source_url: str, now: datetime, status: str,
                        published_at: datetime | None = None) -> None:
    values = dict(macro_series_id=series.id, date=day, value=value, provider=provider,
                  source_url=source_url, retrieved_at=now, published_at=published_at,
                  data_status=status, units=series.units)
    update = {k: values[k] for k in ("value", "provider", "source_url", "retrieved_at",
                                     "published_at", "data_status", "units")}
    db.execute(insert(MacroObservation).values(**values)
               .on_conflict_do_update(constraint="uq_macro_obs_series_date", set_=update))


def _ensure_series(db: Session, spec: LiveSeries) -> MacroSeries:
    row = db.query(MacroSeries).filter(MacroSeries.series_id == spec.series_id).first()
    if row:
        return row
    row = MacroSeries(series_id=spec.series_id, display_name=spec.display_name, title=spec.title,
                      description="Near-real-time market data; see docs/DATA_SOURCE_REGISTER.md.",
                      provider="yahoo_finance", source_url=yahoo.source_url(spec.series_id),
                      units=spec.units, frequency="Daily (intraday updates)",
                      data_status=spec.base_status, stale_after_hours=24, category=spec.category)
    db.add(row)
    db.flush()
    return row


def store_quote(db: Session, spec: LiveSeries, q: yahoo.Quote, now: datetime) -> int:
    series = _ensure_series(db, spec)
    live = q.is_live(now)
    n = 0
    for i, bar in enumerate(q.bars):
        newest = i == len(q.bars) - 1
        status = "DELAYED" if (newest and live) else spec.base_status
        _upsert_observation(db, series, day=bar.date, value=bar.close, provider="yahoo_finance",
                            source_url=q.source_url, now=now, status=status,
                            published_at=q.last_time if newest else None)
        n += 1
    series.last_fetched_at = now
    series.data_status = spec.base_status
    return n


async def run_live_market_ingestion() -> None:
    """Refresh every live series. A failing symbol keeps its old data (it then ages to STALE)."""
    ok = failed = 0
    async with httpx.AsyncClient(timeout=20) as client:
        for spec in LIVE_SERIES:
            now = datetime.now(timezone.utc)
            try:
                q = await yahoo.fetch_quote(client, spec.series_id)
            except yahoo.YahooError as exc:
                failed += 1
                logger.warning("Live quote failed: %s", exc)
            else:
                db = SessionLocal()
                try:
                    store_quote(db, spec, q, now)
                    db.commit()
                    ok += 1
                except Exception:
                    db.rollback()
                    failed += 1
                    logger.exception("Storing live quote failed for %s", spec.series_id)
                finally:
                    db.close()
            await asyncio.sleep(_PAUSE_BETWEEN_SYMBOLS_S)
    logger.info("Live market ingestion: %d ok, %d failed", ok, failed)


def store_yields(db: Session, points: list[treasury.YieldPoint], now: datetime) -> int:
    """Write official Treasury yields into DGS2 / DGS10 and the computed T10Y2Y spread."""
    rows = {s.series_id: s for s in db.query(MacroSeries).filter(
        MacroSeries.series_id.in_(("DGS2", "DGS10", "T10Y2Y"))).all()}
    n = 0
    for p in points:
        url = treasury.source_url(p.date.strftime("%Y%m"))
        for sid, value, provider in (("DGS2", p.y2, "us_treasury"), ("DGS10", p.y10, "us_treasury"),
                                     ("T10Y2Y", None if p.y2 is None or p.y10 is None
                                      else round(p.y10 - p.y2, 2), "us_treasury (computed 10Y-2Y)")):
            row = rows.get(sid)
            if row is None or value is None:
                continue
            _upsert_observation(db, row, day=p.date, value=value, provider=provider, source_url=url,
                                now=now, status="PERIODIC_OFFICIAL_RELEASE")
            n += 1
    for row in rows.values():
        row.last_fetched_at = now
    return n


async def run_treasury_ingestion() -> None:
    now = datetime.now(timezone.utc)
    async with httpx.AsyncClient(timeout=25) as client:
        points = await treasury.fetch_recent_yields(client, now)
    if not points:
        logger.warning("Treasury yields unavailable; keeping existing data")
        return
    db = SessionLocal()
    try:
        n = store_yields(db, points, now)
        db.commit()
        logger.info("Treasury yields: %d observations up to %s", n, points[-1].date)
    except Exception:
        db.rollback()
        logger.exception("Storing Treasury yields failed")
    finally:
        db.close()
