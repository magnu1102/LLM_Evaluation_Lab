from app.evaluation.judge import _parse_verdict, judge_output
from app.evaluation.runner import execute_run
from app.models import PromptTemplate, TestCase
from app.providers.base import ProviderResponse
from app.providers.mock_provider import MockProvider


class _StubProvider:
    name = "stub"
    default_model = "stub-1"

    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, str]] = []

    def complete(self, system, user, model=None):
        self.calls.append((system, user))
        return ProviderResponse(text=self.text, model=model or self.default_model, latency_ms=1)


def test_parse_verdict_strict_json():
    verdict, reason = _parse_verdict('{"verdict":"pass","reason":"all good"}')
    assert verdict == "pass"
    assert reason == "all good"


def test_parse_verdict_extracts_json_from_prose():
    verdict, reason = _parse_verdict(
        'Sure! Here is my verdict:\n{"verdict": "fail", "reason": "invents a date"}\nThanks.'
    )
    assert verdict == "fail"
    assert "invents a date" in reason


def test_parse_verdict_falls_back_on_garbage():
    verdict, reason = _parse_verdict("the model is fine i guess")
    assert verdict == "needs_review"
    assert "unparseable" in reason


def test_judge_output_structure():
    provider = _StubProvider('{"verdict":"pass","reason":"meets criteria"}')
    outcome = judge_output(
        provider,
        question="q",
        context="c",
        expected_behavior={"requires_citation": True},
        model_output="answer [1]",
    )
    assert outcome["criterion"] == "llm_judge"
    assert outcome["severity"] == "info"
    assert outcome["passed"] is True
    assert "verdict=pass" in outcome["detail"]
    assert "evaluation judge" in provider.calls[0][0].lower()


def test_runner_appends_judge_check_when_enabled(session):
    prompt = PromptTemplate(
        name="grounded-summarizer",
        version=2,
        system_prompt="be careful",
        user_template="Context:\n{{context}}\n\nTask: {{question}}",
        notes="",
    )
    tc = TestCase(
        title="cite",
        context="[1] retain only as long as necessary",
        question="Summarize with citation [n]",
        expected_behavior={"requires_citation": True, "max_chars": 600},
        tags=["citations"],
    )
    session.add_all([prompt, tc])
    session.commit()

    run = execute_run(session, prompt, [tc], MockProvider(), enable_llm_judge=True)
    result = run.results[0]
    judge_checks = [c for c in result.automatic_checks if c["criterion"] == "llm_judge"]
    assert len(judge_checks) == 1
    assert judge_checks[0]["severity"] == "info"
    # severity=info must not move status; deterministic checks all pass on this case
    assert result.status == "pass"


def test_runner_skips_judge_when_disabled(session):
    prompt = PromptTemplate(
        name="grounded-summarizer",
        version=2,
        system_prompt="be careful",
        user_template="{{question}}",
        notes="",
    )
    tc = TestCase(
        title="x",
        context="",
        question="q",
        expected_behavior={},
        tags=[],
    )
    session.add_all([prompt, tc])
    session.commit()

    run = execute_run(session, prompt, [tc], MockProvider())
    assert all(c["criterion"] != "llm_judge" for c in run.results[0].automatic_checks)
