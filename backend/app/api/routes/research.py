import uuid
from fastapi import APIRouter, Depends, HTTPException, Cookie, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import auth_service, research_service

router = APIRouter(prefix="/research")
_SESSION_COOKIE = "gmit_session"


def _get_user_id(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
) -> uuid.UUID:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = auth_service.get_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session.user_id


class CreateThesisRequest(BaseModel):
    topic: str


class EvidenceOut(BaseModel):
    id: str
    description: str
    series_id: str | None
    value: float | None
    obs_date: str | None
    interpretation: str


class ScenarioOut(BaseModel):
    id: str
    name: str
    probability: int
    description: str
    trigger: str


class CounterArgumentOut(BaseModel):
    id: str
    argument: str
    strength: str


class ThesisOut(BaseModel):
    id: str
    topic: str
    claim: str
    confidence: int
    time_horizon: str
    rationale: str
    catalysts: list[str]
    invalidation_conditions: list[str]
    model_name: str
    provider: str
    input_tokens: int | None
    output_tokens: int | None
    generation_ms: int | None
    status: str
    is_demo: bool
    created_at: str
    evidence_items: list[EvidenceOut]
    scenarios: list[ScenarioOut]
    counter_arguments: list[CounterArgumentOut]


class ThesisSummaryOut(BaseModel):
    id: str
    topic: str
    claim: str
    confidence: int
    time_horizon: str
    provider: str
    is_demo: bool
    created_at: str


def _thesis_to_out(t) -> ThesisOut:
    return ThesisOut(
        id=str(t.id),
        topic=t.topic,
        claim=t.claim,
        confidence=t.confidence,
        time_horizon=t.time_horizon,
        rationale=t.rationale,
        catalysts=t.catalysts or [],
        invalidation_conditions=t.invalidation_conditions or [],
        model_name=t.model_name,
        provider=t.provider,
        input_tokens=t.input_tokens,
        output_tokens=t.output_tokens,
        generation_ms=t.generation_ms,
        status=t.status,
        is_demo=t.is_demo,
        created_at=t.created_at.isoformat(),
        evidence_items=[
            EvidenceOut(
                id=str(e.id),
                description=e.description,
                series_id=e.series_id,
                value=e.value,
                obs_date=e.obs_date.isoformat() if e.obs_date else None,
                interpretation=e.interpretation,
            )
            for e in t.evidence_items
        ],
        scenarios=[
            ScenarioOut(
                id=str(s.id),
                name=s.name,
                probability=s.probability,
                description=s.description,
                trigger=s.trigger,
            )
            for s in t.scenarios
        ],
        counter_arguments=[
            CounterArgumentOut(id=str(c.id), argument=c.argument, strength=c.strength)
            for c in t.counter_arguments
        ],
    )


@router.post("/thesis", status_code=status.HTTP_201_CREATED)
async def post_create_thesis(
    req: CreateThesisRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=422, detail="topic is required")
    if len(topic) > 500:
        raise HTTPException(status_code=422, detail="topic too long (max 500 chars)")

    thesis = await research_service.create_thesis(db, user_id, topic)
    return _thesis_to_out(thesis)


@router.get("/theses")
def get_theses(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    theses = research_service.get_theses(db, user_id)
    return [
        ThesisSummaryOut(
            id=str(t.id),
            topic=t.topic,
            claim=t.claim,
            confidence=t.confidence,
            time_horizon=t.time_horizon,
            provider=t.provider,
            is_demo=t.is_demo,
            created_at=t.created_at.isoformat(),
        )
        for t in theses
    ]


@router.get("/theses/with-scenarios")
def get_theses_with_scenarios(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    from app.db.models.research import ResearchScenario
    theses = research_service.get_theses(db, user_id)
    result = []
    for t in theses:
        scenarios = (
            db.query(ResearchScenario)
            .filter(ResearchScenario.thesis_id == t.id)
            .order_by(ResearchScenario.sort_order)
            .all()
        )
        result.append({
            "id": str(t.id),
            "topic": t.topic,
            "claim": t.claim,
            "confidence": t.confidence,
            "time_horizon": t.time_horizon,
            "provider": t.provider,
            "created_at": t.created_at.isoformat(),
            "scenarios": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "probability": s.probability,
                    "description": s.description,
                    "trigger": s.trigger,
                }
                for s in scenarios
            ],
        })
    return result


@router.get("/thesis/{thesis_id}")
def get_thesis(
    thesis_id: str,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(_get_user_id),
):
    try:
        tid = uuid.UUID(thesis_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid thesis_id")

    thesis = research_service.get_thesis(db, tid, user_id)
    if not thesis:
        raise HTTPException(status_code=404, detail="thesis not found")
    return _thesis_to_out(thesis)
