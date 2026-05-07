from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.evaluation.runner import execute_run
from app.models import EvaluationRun, PromptTemplate, TestCase
from app.providers import get_provider
from app.schemas import RunCreate, RunRead

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=201)
def create_run(payload: RunCreate, session: Session = Depends(get_session)) -> EvaluationRun:
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
    return execute_run(
        session,
        prompt,
        cases,
        provider,
        model=payload.model,
        enable_llm_judge=payload.enable_llm_judge,
    )


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
