from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import EvaluationResult, EvaluationRun, PromptTemplate, TestCase
from app.providers import LLMProvider

from .checks import aggregate_status, run_checks


def render(template: str, context: str, question: str) -> str:
    return template.replace("{{context}}", context or "").replace("{{question}}", question or "")


def _summary(results: list[EvaluationResult]) -> dict:
    summary = {"total": len(results), "passed": 0, "failed": 0, "needs_review": 0}
    for r in results:
        if r.status == "pass":
            summary["passed"] += 1
        elif r.status == "fail":
            summary["failed"] += 1
        else:
            summary["needs_review"] += 1
    return summary


def execute_run(
    session: Session,
    prompt: PromptTemplate,
    test_cases: list[TestCase],
    provider: LLMProvider,
    model: str | None = None,
) -> EvaluationRun:
    chosen_model = model or provider.default_model
    run = EvaluationRun(
        prompt_template_id=prompt.id,
        provider=provider.name,
        model=chosen_model,
        summary={"total": 0, "passed": 0, "failed": 0, "needs_review": 0},
    )
    session.add(run)
    session.flush()

    for tc in test_cases:
        user_prompt = render(prompt.user_template, tc.context, tc.question)
        resp = provider.complete(prompt.system_prompt, user_prompt, model=chosen_model)
        outcomes = run_checks(resp.text, tc.expected_behavior or {})
        status = aggregate_status(outcomes, None)
        result = EvaluationResult(
            run_id=run.id,
            test_case_id=tc.id,
            model_output=resp.text,
            latency_ms=resp.latency_ms,
            automatic_checks=outcomes,
            human_rating=None,
            human_notes="",
            status=status,
        )
        session.add(result)

    session.flush()
    run.finished_at = datetime.now(UTC)
    run.summary = _summary(run.results)
    session.commit()
    session.refresh(run)
    return run


def recompute_summary(session: Session, run: EvaluationRun) -> EvaluationRun:
    run.summary = _summary(run.results)
    session.commit()
    session.refresh(run)
    return run
