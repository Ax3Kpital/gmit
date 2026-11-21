"""Phase 8 — Geopolitics ingestion: GDELT tone/articles + GPR Index."""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.geo import GeoEvent, GeoRiskIndex, GeoNewsArticle
from app.db.session import SessionLocal
from app.providers.gdelt import fetch_all_regions
from app.providers.gpr import fetch_gpr_index

log = logging.getLogger("gmit.geo")


async def run_geo_ingestion() -> None:
    """Fetch GDELT + GPR data and upsert into DB."""
    log.info("Geo ingestion starting")

    await _ingest_gdelt()
    await _ingest_gpr()

    log.info("Geo ingestion complete")


# GDELT throttles clients hard (HTTP 429), and dev restarts re-run ingestion immediately.
# Skip the GDELT pass when real tone data was already stored recently.
_GDELT_MIN_AGE = timedelta(hours=3)


def _recent_gdelt_data_exists() -> bool:
    db: Session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - _GDELT_MIN_AGE
        row = db.execute(
            select(GeoEvent.id).where(
                GeoEvent.avg_tone.is_not(None), GeoEvent.retrieved_at > cutoff
            ).limit(1)
        ).first()
        return row is not None
    finally:
        db.close()


async def _ingest_gdelt() -> None:
    if _recent_gdelt_data_exists():
        log.info("GDELT data fresher than %s already stored; skipping GDELT fetch", _GDELT_MIN_AGE)
        return
    results = await fetch_all_regions(timespan="2weeks")
    today = date.today()
    db: Session = SessionLocal()
    try:
        for r in results:
            # Upsert GeoEvent for today (one row per region per day)
            stmt = (
                pg_insert(GeoEvent)
                .values(
                    region_key=r.region_key,
                    region_label=r.region_label,
                    event_date=today,
                    article_count=r.article_count,
                    avg_tone=round(r.avg_tone, 4) if r.avg_tone is not None else None,
                    top_themes=[],
                    query_used=r.query,
                    data_status=r.data_status,
                    retrieved_at=r.retrieved_at,
                )
                .on_conflict_do_nothing()  # keep first fetch of the day
            )
            db.execute(stmt)

            # Replace today's articles for this region
            db.query(GeoNewsArticle).filter(
                GeoNewsArticle.region_key == r.region_key,
                GeoNewsArticle.retrieved_at >= datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc),
            ).delete(synchronize_session=False)

            for art in r.articles:
                if not art.url:
                    continue
                db.add(
                    GeoNewsArticle(
                        region_key=r.region_key,
                        url=art.url,
                        title=art.title,
                        domain=art.domain,
                        source_country=art.source_country,
                        language=art.language,
                        published_at=art.published_at,
                        retrieved_at=r.retrieved_at,
                    )
                )

            log.info(
                "GDELT %s: tone=%.2f articles=%s status=%s",
                r.region_key,
                r.avg_tone or 0.0,
                r.article_count or 0,
                r.data_status,
            )

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
