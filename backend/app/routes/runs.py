from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.evaluation.runner import execute_pending_run
from app.models import EvaluationRun, PromptTemplate, TestCase
from app.providers import get_provider
from app.schemas import RunCreate, RunRead

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=202)
def create_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> EvaluationRun:
    prompt = session.get(PromptTemplate, payload.prompt_template_id)
    if not prompt:
        raise HTTPException(404, "prompt_template_id not found")

    if payload.test_case_ids:
        cases = list(
            session.scalars(
                select(TestCase).where(TestCase.id.in_(payload.test_case_ids))
            ).all()
        )
        if len(cases) != len(set(payload.test_case_ids)):
            raise HTTPException(404, "one or more test_case_ids not found")
    else:
        cases = list(session.scalars(select(TestCase).order_by(TestCase.id)).all())

    if not cases:
        raise HTTPException(400, "no test cases to evaluate")

    provider = get_provider()
    chosen_model = payload.model or provider.default_model

    run = EvaluationRun(
        prompt_template_id=prompt.id,
        provider=provider.name,
        model=chosen_model,
        state="pending",
        summary={"total": len(cases), "passed": 0, "failed": 0, "needs_review": 0},
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    background_tasks.add_task(
        execute_pending_run,
        run_id=run.id,
        test_case_ids=[c.id for c in cases],
        model=payload.model,
        enable_llm_judge=payload.enable_llm_judge,
    )
    return run


@router.get("", response_model=list[RunRead])
def list_runs(session: Session = Depends(get_session)) -> list[EvaluationRun]:
    return list(
        session.scalars(select(EvaluationRun).order_by(EvaluationRun.id.desc())).all()
    )


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, session: Session = Depends(get_session)) -> EvaluationRun:
    run = session.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return run
