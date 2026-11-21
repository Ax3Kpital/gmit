"""Phase 8 — Geopolitics ingestion: GDELT tone/articles + GPR Index."""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.geo import GeoEvent, GeoRiskIndex, GeoNewsArticle
from app.db.session import SessionLocal
from app.providers.gdelt import REGIONS, fetch_all_regions
from app.providers.gpr import fetch_gpr_index

log = logging.getLogger("gmit.geo")


async def run_geo_ingestion() -> None:
    """Runs every 30 minutes. Cheap when everything is fresh: GDELT only fetches regions that lack
    recent tone data, and the monthly GPR file is only downloaded when our copy is a day old."""
    log.info("Geo ingestion check")
    await _ingest_gdelt()
    if _gpr_due():
        await _ingest_gpr()
    log.info("Geo ingestion complete")


# GDELT throttles clients hard (HTTP 429): never re-fetch a region that already has recent data.
_GDELT_MIN_AGE = timedelta(hours=3)
_GPR_MIN_AGE = timedelta(hours=24)


def regions_needing_gdelt(fresh_keys: set[str]) -> list[str]:
    return [k for k in REGIONS if k not in fresh_keys]


def _fresh_gdelt_regions() -> set[str]:
    db: Session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - _GDELT_MIN_AGE
        rows = db.execute(
            select(GeoEvent.region_key).where(
                GeoEvent.avg_tone.is_not(None), GeoEvent.retrieved_at > cutoff
            ).distinct()
        ).all()
        return {r[0] for r in rows}
    finally:
        db.close()


def _gpr_due() -> bool:
    db: Session = SessionLocal()
    try:
        last = db.execute(select(func.max(GeoRiskIndex.retrieved_at))).scalar()
        return last is None or datetime.now(timezone.utc) - last > _GPR_MIN_AGE
    finally:
        db.close()


async def _ingest_gdelt() -> None:
    missing = regions_needing_gdelt(_fresh_gdelt_regions())
    if not missing:
        log.info("GDELT: all %d regions fresher than %s; nothing to fetch", len(REGIONS), _GDELT_MIN_AGE)
        return
    log.info("GDELT: fetching %d region(s): %s", len(missing), ", ".join(missing))
    results = await fetch_all_regions(timespan="2weeks", keys=missing)
    today = date.today()
    db: Session = SessionLocal()
    try:
        for r in results:
            if r.avg_tone is None:
                # a failed fetch stores nothing: it must never shadow earlier good data
                log.info("GDELT %s: no tone data this time (status=%s)", r.region_key, r.data_status)
                continue
            db.add(GeoEvent(
                region_key=r.region_key, region_label=r.region_label, event_date=today,
                article_count=r.article_count, avg_tone=round(r.avg_tone, 4), top_themes=[],
                query_used=r.query, data_status=r.data_status, retrieved_at=r.retrieved_at,
            ))
            if r.articles:                       # keep the previous articles when this fetch found none
                db.query(GeoNewsArticle).filter(GeoNewsArticle.region_key == r.region_key).delete(
                    synchronize_session=False)
                for art in r.articles:
                    if not art.url:
                        continue
                    db.add(GeoNewsArticle(
                        region_key=r.region_key, url=art.url, title=art.title, domain=art.domain,
                        source_country=art.source_country, language=art.language,
                        published_at=art.published_at, retrieved_at=r.retrieved_at,
                    ))
            log.info("GDELT %s: tone=%.2f articles=%s status=%s", r.region_key, r.avg_tone,
                     r.article_count or 0, r.data_status)
        db.commit()
    except Exception as exc:
        db.rollback()
        log.error("GDELT ingestion DB error: %s", exc)
    finally:
        db.close()


async def _ingest_gpr() -> None:
    result = await fetch_gpr_index(last_n_months=60)
    if result.data_status == "UNAVAILABLE":
        log.warning("GPR: data unavailable — skipping DB write")
        return

    db: Session = SessionLocal()
    try:
        upserted = 0
        for pt in result.series:
            stmt = (
                pg_insert(GeoRiskIndex)
                .values(
                    period=pt.period,
                    gpr_value=pt.gpr_value,
                    gpr_threat=pt.gpr_threat,
                    gpr_act=pt.gpr_act,
                    data_status=result.data_status,
                    retrieved_at=result.retrieved_at,
                )
                .on_conflict_do_update(
                    index_elements=["period"],
                    set_={
                        "gpr_value": pt.gpr_value,
                        "gpr_threat": pt.gpr_threat,
                        "gpr_act": pt.gpr_act,
                        "retrieved_at": result.retrieved_at,
                    },
                )
            )
            db.execute(stmt)
            upserted += 1

        db.commit()
        log.info("GPR: upserted %d months", upserted)
    except Exception as exc:
        db.rollback()
        log.error("GPR ingestion DB error: %s", exc)
    finally:
        db.close()
