from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.evaluation.checks import aggregate_status
from app.evaluation.runner import recompute_summary
from app.models import EvaluationResult
from app.schemas import ResultRead, ReviewIn

router = APIRouter(prefix="/results", tags=["results"])


@router.patch("/{result_id}/review", response_model=ResultRead)
def review_result(
    result_id: int,
    payload: ReviewIn,
    session: Session = Depends(get_session),
) -> EvaluationResult:
    result = session.get(EvaluationResult, result_id)
    if not result:
        raise HTTPException(404, "result not found")

    result.human_rating = payload.human_rating
    result.human_notes = payload.human_notes
    result.status = aggregate_status(result.automatic_checks, payload.human_rating)
    session.flush()
    recompute_summary(session, result.run)
    session.refresh(result)
    return result
