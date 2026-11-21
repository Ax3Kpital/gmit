from app.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    from app.core.config import settings

    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")
        from app.llm.anthropic_provider import AnthropicLLMProvider
        return AnthropicLLMProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    if settings.llm_provider == "rules":
        from app.llm.rules_provider import RulesProvider
        return RulesProvider()

    from app.llm.mock import MockLLMProvider
    return MockLLMProvider()
