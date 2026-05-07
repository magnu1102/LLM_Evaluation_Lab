from app.config import settings

from .base import LLMProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider


def get_provider(name: str | None = None) -> LLMProvider:
    chosen = (name or settings.llm_provider or "mock").lower()
    if chosen == "openai":
        return OpenAIProvider()
    if chosen == "mock":
        return MockProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {chosen!r}")
