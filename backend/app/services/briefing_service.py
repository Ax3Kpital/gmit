"""Daily briefing generation service — rule-based, zero LLM cost."""
import logging
from datetime import datetime, timezone, date as date_type
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models.agent import AgentRun, Briefing
from app.db.models.smart_money import CotInstrument, CotReport
from app.analysis.signals import compute_signals
from app.analysis.briefing import build_briefing, DailyBriefingData

logger = logging.getLogger("gmit.briefing")


def _sentiment(pct: float | None) -> str | None:
    if pct is None:
        return None
    if pct >= 80:
        return "extreme_long"
    if pct >= 60:
        return "long"
    if pct <= 20:
        return "extreme_short"
    if pct <= 40:
        return "short"
    return "neutral"


def _get_latest_cot(db: Session) -> list[dict]:
    instruments = db.query(CotInstrument).all()
    result = []
    for inst in instruments:
        latest = (
            db.query(CotReport)
            .filter(CotReport.instrument_id == inst.id)
            .order_by(CotReport.report_date.desc())
            .first()
        )
        if not latest:
            continue
        history = (
            db.query(CotReport)
            .filter(CotReport.instrument_id == inst.id)
            .order_by(CotReport.report_date.desc())
            .limit(52)
            .all()
        )
        net_values = [r.net_noncomm for r in history if r.net_noncomm is not None]
        pct = None
        if len(net_values) >= 4 and latest.net_noncomm is not None:
            lo, hi = min(net_values), max(net_values)
            if hi != lo:
                pct = (latest.net_noncomm - lo) / (hi - lo) * 100
        pct_rounded = round(pct, 1) if pct is not None else None

        result.append({
            "display_name": inst.display_name,
            "cftc_code": inst.cftc_code,
            "net_noncomm": latest.net_noncomm,
            "percentile_52w": pct_rounded,
            "sentiment": _sentiment(pct_rounded),
        })
    return result


def _get_today_alerts(db: Session) -> list[dict]:
    from app.db.models.smart_money import AlertEvent
    today = date_type.today()
    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.triggered_at >= datetime(today.year, today.month, today.day,
                                                     tzinfo=timezone.utc))
        .order_by(AlertEvent.triggered_at.desc())
        .limit(10)
        .all()
    )
    return [{"message": e.message, "triggered_at": e.triggered_at.isoformat()} for e in events]


def _build_macro_context(db: Session) -> dict:
    from app.services.series_snapshot import build_snippets
    return {"macro_snippets": build_snippets(db)}


def generate_daily_briefing(db: Session) -> Briefing:
    started = datetime.now(timezone.utc)
    run = AgentRun(
        agent_type="daily_briefing",
        trigger="scheduled",
        status="running",
        provider="rules",
        model_name="briefing-engine-v1",
        started_at=started,
    )
    db.add(run)
    db.flush()

    try:
        ctx = _build_macro_context(db)
        signals = compute_signals(ctx.get("macro_snippets", []))
        cot_items = _get_latest_cot(db)
        alert_events = _get_today_alerts(db)

        data: DailyBriefingData = build_briefing(signals, cot_items, alert_events)

        sections = {
            "key_moves": data.key_moves,
            "cot_highlights": data.cot_highlights,
            "alert_summary": data.alert_summary,
            "watchlist": data.watchlist,
        }
        raw_data = asdict(signals)

        today = date_type.today()
        stmt = pg_insert(Briefing.__table__).values(
            date=today,
            macro_regime=data.macro_regime,
            headline=data.headline,
            sections=sections,
            raw_data=raw_data,
            agent_run_id=run.id,
            generated_at=datetime.now(timezone.utc),
        ).on_conflict_do_update(
            index_elements=["date"],
            set_={
                "macro_regime": data.macro_regime,
                "headline": data.headline,
                "sections": sections,
                "raw_data": raw_data,
                "agent_run_id": run.id,
                "generated_at": datetime.now(timezone.utc),
            },
        )
        db.execute(stmt)

        completed = datetime.now(timezone.utc)
        run.status = "completed"
        run.completed_at = completed
        run.duration_ms = int((completed - started).total_seconds() * 1000)
        run.result_summary = f"Briefing generated for {today}: regime={data.macro_regime}, {len(data.key_moves)} moves, {len(data.cot_highlights)} COT signals"
        db.commit()

        briefing = db.query(Briefing).filter(Briefing.date == today).first()
        logger.info("Daily briefing generated: regime=%s, date=%s", data.macro_regime, today)

        from app.services.notification_service import notify_briefing
        notify_briefing(
            date=str(today),
            regime=data.macro_regime,
            headline=data.headline,
            key_moves=data.key_moves,
            cot_highlights=data.cot_highlights,
            watchlist=data.watchlist,
        )
        return briefing

    except Exception as exc:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = str(exc)
        db.commit()
        logger.error("Daily briefing failed: %s", exc)
        raise


def log_thesis_run(
    db: Session,
    topic: str,
    user_id: str,
    provider: str,
    model_name: str,
    input_tokens: int | None,
    output_tokens: int | None,
    duration_ms: int,
    success: bool,
    error: str | None = None,
) -> None:
    run = AgentRun(
        agent_type="thesis",
        trigger=f"user:{user_id}",
        status="completed" if success else "failed",
        input_data={"topic": topic},
        provider=provider,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        error_message=error,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
