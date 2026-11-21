import logging
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.db.models.macro import MacroSeries, MacroObservation
from app.providers.fred import FredProvider
from app.core.config import settings

logger = logging.getLogger("gmit.ingestion")

# All FRED series to ingest — macro + market instruments
_ALL_FRED_SERIES = [
    # Macro
    {"series_id": "DGS10",  "data_status": "PERIODIC_OFFICIAL_RELEASE"},
    {"series_id": "DGS2",   "data_status": "PERIODIC_OFFICIAL_RELEASE"},
    {"series_id": "T10Y2Y", "data_status": "PERIODIC_OFFICIAL_RELEASE"},
    # Commodities
    {"series_id": "DCOILWTICO",   "data_status": "END_OF_DAY"},
    {"series_id": "DCOILBRENTEU", "data_status": "END_OF_DAY"},
    {"series_id": "DHHNGSP",      "data_status": "END_OF_DAY"},
    # Equities
    {"series_id": "SP500",     "data_status": "END_OF_DAY"},
    {"series_id": "NASDAQCOM", "data_status": "END_OF_DAY"},
    # FX
    {"series_id": "DEXUSEU", "data_status": "END_OF_DAY"},
    {"series_id": "DEXJPUS", "data_status": "END_OF_DAY"},
    {"series_id": "DEXUSUK", "data_status": "END_OF_DAY"},
    {"series_id": "DEXCHUS", "data_status": "END_OF_DAY"},
]


async def ingest_series(series_id: str, data_status: str) -> None:
    db = SessionLocal()
    try:
        series_row = db.query(MacroSeries).filter(MacroSeries.series_id == series_id).first()
        if not series_row:
            logger.warning("Series %s not in DB — skipping", series_id)
            return

        logger.info("FRED fetch: %s", series_id)
        fred = FredProvider()
        observations = await fred.fetch_observations(series_id, limit=365)

        source_url = f"https://fred.stlouisfed.org/series/{series_id}"
        now = datetime.now(timezone.utc)
        upserted = 0

        for obs in observations:
            if obs.value is None:
                continue
            stmt = (
                insert(MacroObservation)
                .values(
                    macro_series_id=series_row.id,
                    date=obs.date,
                    value=obs.value,
                    provider="fred",
                    source_url=source_url,
                    retrieved_at=now,
                    data_status=data_status,
                    units=series_row.units,
                )
                .on_conflict_do_update(
                    constraint="uq_macro_obs_series_date",
                    set_={"value": obs.value, "retrieved_at": now},
                )
            )
            db.execute(stmt)
            upserted += 1

        series_row.last_fetched_at = now
        series_row.data_status = data_status
        db.commit()
        logger.info("FRED %s: upserted %d observations", series_id, upserted)
    except Exception:
        logger.exception("Ingestion failed for %s", series_id)
        db.rollback()
    finally:
        db.close()


async def run_macro_ingestion() -> None:
    if not settings.fred_api_key:
        logger.info("FRED_API_KEY not configured — skipping ingestion")
        return
    for cfg in _ALL_FRED_SERIES:
        await ingest_series(cfg["series_id"], cfg["data_status"])
