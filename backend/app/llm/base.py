from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EvidenceDTO:
    description: str
    series_id: str | None
    value: float | None
    obs_date: str | None  # ISO date string
    interpretation: str


@dataclass
class ScenarioDTO:
    name: str
    probability: int
    description: str
    trigger: str


@dataclass
class CounterArgumentDTO:
    argument: str
    strength: str  # "weak" | "moderate" | "strong"


@dataclass
class ThesisResult:
    claim: str
    confidence: int  # 0-100
    time_horizon: str  # "1W" | "1M" | "3M" | "6M" | "1Y" | "2Y+"
    rationale: str
    catalysts: list[str]
    invalidation_conditions: list[str]
    evidence: list[EvidenceDTO]
    scenarios: list[ScenarioDTO]
    counter_arguments: list[CounterArgumentDTO]
    model_name: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    generation_ms: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate_thesis(self, topic: str, context: dict) -> ThesisResult: ...
