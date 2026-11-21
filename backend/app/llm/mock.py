import asyncio
from app.llm.base import (
    LLMProvider, ThesisResult, EvidenceDTO, ScenarioDTO, CounterArgumentDTO,
)


class MockLLMProvider(LLMProvider):
    async def generate_thesis(self, topic: str, context: dict) -> ThesisResult:
        await asyncio.sleep(0.1)

        macro_snippets = context.get("macro_snippets", [])

        evidence: list[EvidenceDTO] = []
        for i, s in enumerate(macro_snippets[:3]):
            evidence.append(EvidenceDTO(
                description=s.get("display_name", s.get("series_id", f"Series {i}")),
                series_id=s.get("series_id"),
                value=s.get("latest_value"),
                obs_date=s.get("latest_date"),
                interpretation=f"[DEMO] {s.get('display_name', s.get('series_id', ''))} at {s.get('latest_value', 'N/A')} provides supporting context.",
            ))

        return ThesisResult(
            claim=f"[DEMO] Based on current macro conditions, {topic} warrants a cautiously constructive outlook.",
            confidence=55,
            time_horizon="3M",
            rationale=(
                "[DEMO] This is a mock thesis generated without a real LLM. "
                "Set LLM_PROVIDER=anthropic and add ANTHROPIC_API_KEY to .env to enable real AI analysis."
            ),
            catalysts=[
                "[DEMO] Catalyst A: central bank pivot",
                "[DEMO] Catalyst B: supply constraint easing",
            ],
            invalidation_conditions=[
                "[DEMO] Invalidation: sustained break below key support",
                "[DEMO] Invalidation: unexpected policy tightening",
            ],
            evidence=evidence,
            scenarios=[
                ScenarioDTO(
                    name="Base",
                    probability=60,
                    description="[DEMO] Gradual normalization continues.",
                    trigger="[DEMO] No material macro shock.",
                ),
                ScenarioDTO(
                    name="Bull",
                    probability=25,
                    description="[DEMO] Positive surprise accelerates move.",
                    trigger="[DEMO] Catalyst A materializes early.",
                ),
                ScenarioDTO(
                    name="Bear",
                    probability=15,
                    description="[DEMO] Risk-off episode reverses gains.",
                    trigger="[DEMO] Invalidation condition triggered.",
                ),
            ],
            counter_arguments=[
                CounterArgumentDTO(
                    argument="[DEMO] Valuations remain stretched relative to historical norms.",
                    strength="moderate",
                ),
                CounterArgumentDTO(
                    argument="[DEMO] Geopolitical tail risks are underpriced.",
                    strength="weak",
                ),
            ],
            model_name="mock",
            provider="mock",
            input_tokens=None,
            output_tokens=None,
            generation_ms=100,
        )
