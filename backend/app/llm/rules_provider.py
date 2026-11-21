from app.llm.base import LLMProvider, ThesisResult
from app.analysis.signals import compute_signals
from app.analysis.engine import build_thesis


class RulesProvider(LLMProvider):
    async def generate_thesis(self, topic: str, context: dict) -> ThesisResult:
        snippets = context.get("macro_snippets", [])
        signals = compute_signals(snippets)
        return build_thesis(topic, signals)
