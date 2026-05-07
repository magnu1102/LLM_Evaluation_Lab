import time

from app.config import settings

from .base import ProviderResponse


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        self.default_model = settings.openai_model
        self._api_key = settings.openai_api_key
        self._client = None  # lazy

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def complete(self, system: str, user: str, model: str | None = None) -> ProviderResponse:
        client = self._get_client()
        chosen = model or self.default_model
        start = time.perf_counter()
        resp = client.chat.completions.create(
            model=chosen,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        return ProviderResponse(text=text, model=chosen, latency_ms=latency_ms)
