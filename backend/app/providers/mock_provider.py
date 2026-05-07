import time

from .base import ProviderResponse


class MockProvider:
    """Deterministic provider for tests and demos without API keys.

    Returns canned outputs based on cues in the user prompt. Useful to
    exercise the runner, checks, and UI end-to-end offline.
    """

    name = "mock"
    default_model = "mock-1"

    def complete(self, system: str, user: str, model: str | None = None) -> ProviderResponse:
        start = time.perf_counter()
        text = self._respond(system, user)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ProviderResponse(text=text, model=model or self.default_model, latency_ms=latency_ms)

    def _respond(self, system: str, user: str) -> str:
        u = user.lower()
        if "[no context provided]" in u or "context: (none)" in u:
            return (
                "I don't have enough information in the provided context to answer this. "
                "Please supply the relevant source material."
            )
        if "cite" in u or "with citation" in u or "[n]" in u:
            return (
                "Personal data must be retained only as long as necessary [1]. "
                "Retention periods are documented in the records schedule [2]."
            )
        if "policy" in u or "guidance" in u:
            return (
                "Summary: process each case in order of receipt, document the decision, "
                "and notify the applicant within the statutory deadline."
            )
        if "support" in u or "customer" in u:
            return "Thanks for reaching out — please restart the device and try again."
        return "Acknowledged."
