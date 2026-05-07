from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import EvaluationResult, EvaluationRun, PromptTemplate, TestCase
from app.providers import LLMProvider, get_provider

from .checks import aggregate_status, run_checks
from .judge import judge_output

logger = logging.getLogger(__name__)


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


def _process_cases(
    session: Session,
    run: EvaluationRun,
    prompt: PromptTemplate,
    test_cases: list[TestCase],
    provider: LLMProvider,
    chosen_model: str,
    enable_llm_judge: bool,
) -> None:
    """Iterate test cases against the provider and persist a result row each.

    Pure work loop; does not touch run.state — callers manage that.
    """
    for tc in test_cases:
        user_prompt = render(prompt.user_template, tc.context, tc.question)
        resp = provider.complete(prompt.system_prompt, user_prompt, model=chosen_model)
        outcomes = run_checks(resp.text, tc.expected_behavior or {})
        if enable_llm_judge:
            outcomes.append(
                judge_output(
                    provider,
                    question=tc.question,
                    context=tc.context,
                    expected_behavior=tc.expected_behavior or {},
                    model_output=resp.text,
                )
            )
        status = aggregate_status(outcomes, None)
        session.add(
            EvaluationResult(
                run_id=run.id,
                test_case_id=tc.id,
                model_output=resp.text,
                latency_ms=resp.latency_ms,
                automatic_checks=outcomes,
                human_rating=None,
                human_notes="",
                status=status,
            )
        )


def execute_run(
    session: Session,
    prompt: PromptTemplate,
    test_cases: list[TestCase],
    provider: LLMProvider,
    model: str | None = None,
    enable_llm_judge: bool = False,
) -> EvaluationRun:
    """Synchronous helper used by the CLI and tests. Creates a run, runs every
    case inline, marks the run completed, and returns it.

    Production HTTP traffic uses the asynchronous execute_pending_run path
    instead — see backend/app/routes/runs.py.
    """
    chosen_model = model or provider.default_model
    run = EvaluationRun(
        prompt_template_id=prompt.id,
        provider=provider.name,
        model=chosen_model,
        state="running",
        summary={"total": 0, "passed": 0, "failed": 0, "needs_review": 0},
    )
    session.add(run)
    session.flush()

    _process_cases(session, run, prompt, test_cases, provider, chosen_model, enable_llm_judge)

    session.flush()
    run.finished_at = datetime.now(UTC)
    run.summary = _summary(run.results)
    run.state = "completed"
    session.commit()
    session.refresh(run)
    return run


def execute_pending_run(
    run_id: int,
    test_case_ids: list[int],
    model: str | None,
    enable_llm_judge: bool,
) -> None:
    """Background-task entry point. Opens its own session, runs the cases,
    and updates `state` to completed or failed.

    Errors are caught and recorded on the run (state="failed",
    summary["error"]=...) rather than propagating, so the request that
    scheduled the task isn't affected and the UI can render the failure.
    """
    from app.db import SessionLocal  # local import to avoid circular import at module load

    with SessionLocal() as session:
        run = session.get(EvaluationRun, run_id)
        if run is None:
            logger.warning("execute_pending_run: run %s disappeared", run_id)
            return
        prompt = session.get(PromptTemplate, run.prompt_template_id)
        cases = list(
            session.scalars(select(TestCase).where(TestCase.id.in_(test_case_ids))).all()
        )
        if prompt is None or not cases:
            run.state = "failed"
            run.summary = {**(run.summary or {}), "error": "prompt or test cases missing"}
            run.finished_at = datetime.now(UTC)
            session.commit()
            return

        run.state = "running"
        session.commit()

        try:
            provider = get_provider()
            chosen_model = model or provider.default_model
            run.model = chosen_model
            run.provider = provider.name

            _process_cases(session, run, prompt, cases, provider, chosen_model, enable_llm_judge)

            session.flush()
            run.summary = _summary(run.results)
            run.finished_at = datetime.now(UTC)
            run.state = "completed"
            session.commit()
        except Exception as exc:
            logger.exception("run %s failed", run_id)
            session.rollback()
            # Direct UPDATE so we don't fight ORM identity-map / JSON-column
            # change tracking after a rollback.
            existing_summary = session.scalar(
                select(EvaluationRun.summary).where(EvaluationRun.id == run_id)
            ) or {}
            session.execute(
                update(EvaluationRun)
                .where(EvaluationRun.id == run_id)
                .values(
                    state="failed",
                    finished_at=datetime.now(UTC),
                    summary={**existing_summary, "error": str(exc)[:500]},
                )
            )
            session.commit()


def recompute_summary(session: Session, run: EvaluationRun) -> EvaluationRun:
    run.summary = _summary(run.results)
    session.commit()
    session.refresh(run)
    return run
