import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.session import SessionLocal
from app.db.models.smart_money import CotInstrument, CotReport
from app.providers.cftc import CftcProvider

log = logging.getLogger("gmit.cot")

_ALL_INSTRUMENTS: list[dict] = [
    {"cftc_code": "088691", "display_name": "Gold", "category": "commodity", "exchange": "COMEX", "related_series_id": None},
    {"cftc_code": "067651", "display_name": "WTI Crude Oil", "category": "commodity", "exchange": "NYMEX", "related_series_id": "DCOILWTICO"},
    {"cftc_code": "13874A", "display_name": "S&P 500 E-mini", "category": "equity", "exchange": "CME", "related_series_id": "SP500"},
    {"cftc_code": "099741", "display_name": "Euro FX", "category": "fx", "exchange": "CME", "related_series_id": "DEXUSEU"},
    {"cftc_code": "043602", "display_name": "10-Year T-Note", "category": "rates", "exchange": "CBOT", "related_series_id": "DGS10"},
    {"cftc_code": "023651", "display_name": "Natural Gas", "category": "commodity", "exchange": "NYMEX", "related_series_id": "DHHNGSP"},
]


async def run_cot_ingestion() -> None:
    provider = CftcProvider()
    try:
        db = SessionLocal()
        try:
            instruments = db.query(CotInstrument).filter(CotInstrument.enabled == True).all()
            if not instruments:
                log.info("COT: no instruments seeded — skipping")
                return
            for inst in instruments:
                await _ingest_instrument(provider, inst.cftc_code)
        finally:
            db.close()
    finally:
        await provider.aclose()


async def _ingest_instrument(provider: CftcProvider, cftc_code: str) -> None:
    log.info("COT fetch: %s", cftc_code)
    db = SessionLocal()
    try:
        inst = db.query(CotInstrument).filter(CotInstrument.cftc_code == cftc_code).first()
        if not inst:
            return

        try:
            observations = await provider.fetch_observations(cftc_code, limit=104)
        except Exception as exc:
            log.warning("COT fetch failed for %s: %s", cftc_code, exc)
            return

        upserted = 0
        for obs in observations:
            if obs.noncomm_long is None or obs.noncomm_short is None:
                continue
            net = obs.noncomm_long - obs.noncomm_short
            pct_oi = None
            if obs.open_interest and obs.open_interest > 0:
                pct_oi = net / obs.open_interest * 100

            stmt = pg_insert(CotReport).values(
                instrument_id=inst.id,
                report_date=obs.report_date,
                open_interest=obs.open_interest,
                noncomm_long=obs.noncomm_long,
                noncomm_short=obs.noncomm_short,
                noncomm_spread=obs.noncomm_spread,
                comm_long=obs.comm_long,
                comm_short=obs.comm_short,
                net_noncomm=net,
                net_noncomm_pct_oi=pct_oi,
                change_noncomm_long=obs.change_noncomm_long,
                change_noncomm_short=obs.change_noncomm_short,
                retrieved_at=obs.retrieved_at,
                source_url=obs.source_url,
            ).on_conflict_do_update(
                constraint="uq_cot_instrument_date",
                set_={
                    "open_interest": obs.open_interest,
                    "noncomm_long": obs.noncomm_long,
                    "noncomm_short": obs.noncomm_short,
                    "net_noncomm": net,
                    "net_noncomm_pct_oi": pct_oi,
                    "retrieved_at": obs.retrieved_at,
                },
            )
            db.execute(stmt)
            upserted += 1

        db.commit()
        log.info("COT %s: upserted %d reports", cftc_code, upserted)
    finally:
        db.close()
