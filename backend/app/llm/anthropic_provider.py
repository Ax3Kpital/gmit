import json
import time
import anthropic
from app.llm.base import (
    LLMProvider, ThesisResult, EvidenceDTO, ScenarioDTO, CounterArgumentDTO,
)

_TOOL_SCHEMA = {
    "name": "create_thesis",
    "description": "Create a structured macro investment thesis with evidence, scenarios, and counter-arguments.",
    "input_schema": {
        "type": "object",
        "required": ["claim", "confidence", "time_horizon", "rationale", "catalysts",
                     "invalidation_conditions", "evidence", "scenarios", "counter_arguments"],
        "properties": {
            "claim": {"type": "string", "description": "One-sentence investment thesis claim."},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100,
                          "description": "Confidence 0–100."},
            "time_horizon": {
                "type": "string",
                "enum": ["1W", "1M", "3M", "6M", "1Y", "2Y+"],
                "description": "Investment time horizon.",
            },
            "rationale": {"type": "string", "description": "2–4 paragraph analytical rationale."},
            "catalysts": {
                "type": "array", "items": {"type": "string"},
                "minItems": 2, "maxItems": 5,
                "description": "Key catalysts that would support the thesis.",
            },
            "invalidation_conditions": {
                "type": "array", "items": {"type": "string"},
                "minItems": 1, "maxItems": 4,
                "description": "Conditions that would invalidate this thesis.",
            },
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["description", "interpretation"],
                    "properties": {
                        "description": {"type": "string"},
                        "series_id": {"type": "string", "nullable": True},
                        "value": {"type": "number", "nullable": True},
                        "obs_date": {"type": "string", "nullable": True,
                                    "description": "ISO date (YYYY-MM-DD)"},
                        "interpretation": {"type": "string"},
                    },
                },
                "minItems": 1, "maxItems": 6,
            },
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "probability", "description", "trigger"],
                    "properties": {
                        "name": {"type": "string"},
                        "probability": {"type": "integer", "minimum": 1, "maximum": 98},
                        "description": {"type": "string"},
                        "trigger": {"type": "string"},
                    },
                },
                "minItems": 2, "maxItems": 4,
                "description": "Scenario probabilities must sum to 100.",
            },
            "counter_arguments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["argument", "strength"],
                    "properties": {
                        "argument": {"type": "string"},
                        "strength": {"type": "string", "enum": ["weak", "moderate", "strong"]},
                    },
                },
                "minItems": 1, "maxItems": 4,
            },
        },
    },
}

_SYSTEM_PROMPT = """You are a rigorous macro research analyst. When generating an investment thesis:
- Base all claims strictly on the provided data context.
- Be precise about time horizons and confidence levels.
- Counter-arguments must be genuine bear cases, not strawmen.
- Scenario probabilities must sum to exactly 100.
- Do not fabricate data points. Only reference series provided in the context.
- Language: respond entirely in English regardless of input language."""


def _build_user_prompt(topic: str, context: dict) -> str:
    snippets = context.get("macro_snippets", [])
    lines = [f"**Research topic:** {topic}", "", "**Current macro data context:**"]
    for s in snippets:
        val = s.get("latest_value")
        date = s.get("latest_date", "")
        name = s.get("display_name") or s.get("series_id", "")
        sid = s.get("series_id", "")
        units = s.get("units", "")
        if val is not None:
            lines.append(f"- {name} ({sid}): {val} {units} as of {date}")
    lines.append("")
    lines.append("Generate a comprehensive macro investment thesis using the create_thesis tool.")
    return "\n".join(lines)


class AnthropicLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    async def generate_thesis(self, topic: str, context: dict) -> ThesisResult:
        import asyncio

        def _sync_call() -> anthropic.types.Message:
            return self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                tools=[_TOOL_SCHEMA],
                tool_choice={"type": "tool", "name": "create_thesis"},
                messages=[{"role": "user", "content": _build_user_prompt(topic, context)}],
            )

        t0 = time.monotonic()
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(None, _sync_call)
        generation_ms = int((time.monotonic() - t0) * 1000)

        tool_input: dict = {}
        for block in msg.content:
            if block.type == "tool_use" and block.name == "create_thesis":
                tool_input = block.input  # type: ignore[attr-defined]
                break

        if not tool_input:
            raise ValueError("No create_thesis tool_use block in Anthropic response")

        evidence = [
            EvidenceDTO(
                description=e["description"],
                series_id=e.get("series_id"),
                value=e.get("value"),
                obs_date=e.get("obs_date"),
                interpretation=e["interpretation"],
            )
            for e in tool_input.get("evidence", [])
        ]
        scenarios = [
            ScenarioDTO(
                name=s["name"],
                probability=s["probability"],
                description=s["description"],
                trigger=s["trigger"],
            )
            for s in tool_input.get("scenarios", [])
        ]
        counter_arguments = [
            CounterArgumentDTO(argument=c["argument"], strength=c["strength"])
            for c in tool_input.get("counter_arguments", [])
        ]

        return ThesisResult(
            claim=tool_input["claim"],
            confidence=tool_input["confidence"],
            time_horizon=tool_input["time_horizon"],
            rationale=tool_input["rationale"],
            catalysts=tool_input.get("catalysts", []),
            invalidation_conditions=tool_input.get("invalidation_conditions", []),
            evidence=evidence,
            scenarios=scenarios,
            counter_arguments=counter_arguments,
            model_name=self._model,
            provider="anthropic",
            input_tokens=msg.usage.input_tokens if msg.usage else None,
            output_tokens=msg.usage.output_tokens if msg.usage else None,
            generation_ms=generation_ms,
        )
