import time

from app.config import settings

from .base import ProviderResponse


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        self.default_model = settings.anthropic_model
        self._api_key = settings.anthropic_api_key
        self._client = None  # lazy

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not configured")
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def complete(self, system: str, user: str, model: str | None = None) -> ProviderResponse:
        client = self._get_client()
        chosen = model or self.default_model
        start = time.perf_counter()
        resp = client.messages.create(
            model=chosen,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()
        return ProviderResponse(text=text, model=chosen, latency_ms=latency_ms)
