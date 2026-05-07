from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderResponse:
    text: str
    model: str
    latency_ms: int


class LLMProvider(Protocol):
    name: str
    default_model: str

    def complete(self, system: str, user: str, model: str | None = None) -> ProviderResponse: ...
