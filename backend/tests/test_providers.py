import pytest

from app.providers import get_provider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider


def test_factory_returns_known_providers():
    assert isinstance(get_provider("mock"), MockProvider)
    assert isinstance(get_provider("openai"), OpenAIProvider)
    assert isinstance(get_provider("anthropic"), AnthropicProvider)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        get_provider("does-not-exist")


def test_anthropic_requires_key_to_call(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "anthropic_api_key", "")
    provider = AnthropicProvider()
    with pytest.raises(RuntimeError):
        provider.complete("sys", "user")
