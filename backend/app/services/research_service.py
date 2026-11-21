import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models.research import Thesis, EvidenceItem, ResearchScenario, CounterArgument
from app.llm import get_llm_provider, ThesisResult


def _build_macro_context(db: Session) -> dict:
    from app.services.series_snapshot import build_snippets
    return {"macro_snippets": build_snippets(db)}


async def create_thesis(db: Session, user_id: uuid.UUID, topic: str) -> Thesis:
    context = _build_macro_context(db)
    provider = get_llm_provider()
    t0 = datetime.now(timezone.utc)
    result: ThesisResult = await provider.generate_thesis(topic, context)
    duration_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
    from app.services.briefing_service import log_thesis_run
    log_thesis_run(
        db,
        topic=topic,
        user_id=str(user_id),
        provider=result.provider,
        model_name=result.model_name,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        duration_ms=duration_ms,
        success=True,
    )

    thesis = Thesis(
        user_id=user_id,
        topic=topic,
        claim=result.claim,
        confidence=result.confidence,
        time_horizon=result.time_horizon,
        rationale=result.rationale,
        catalysts=result.catalysts,
        invalidation_conditions=result.invalidation_conditions,
        model_name=result.model_name,
        provider=result.provider,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        generation_ms=result.generation_ms,
        status="completed",
        is_demo=(result.provider == "mock"),
    )
    db.add(thesis)
    db.flush()

    for i, e in enumerate(result.evidence):
        from datetime import date
        obs_date = None
        if e.obs_date:
            try:
                obs_date = date.fromisoformat(e.obs_date)
            except ValueError:
                pass
        db.add(EvidenceItem(
            thesis_id=thesis.id,
            description=e.description,
            series_id=e.series_id,
            value=e.value,
            obs_date=obs_date,
            interpretation=e.interpretation,
            sort_order=i,
        ))

    for i, s in enumerate(result.scenarios):
        db.add(ResearchScenario(
            thesis_id=thesis.id,
            name=s.name,
            probability=s.probability,
            description=s.description,
            trigger=s.trigger,
            sort_order=i,
        ))

    for i, c in enumerate(result.counter_arguments):
        db.add(CounterArgument(
            thesis_id=thesis.id,
            argument=c.argument,
            strength=c.strength,
            sort_order=i,
        ))

    db.commit()
    db.refresh(thesis)
    return thesis


def get_theses(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[Thesis]:
    return (
        db.query(Thesis)
        .filter(Thesis.user_id == user_id)
        .order_by(Thesis.created_at.desc())
        .limit(limit)
        .all()
    )


def get_thesis(db: Session, thesis_id: uuid.UUID, user_id: uuid.UUID) -> Thesis | None:
    return (
        db.query(Thesis)
        .filter(Thesis.id == thesis_id, Thesis.user_id == user_id)
        .first()
    )
