from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import TestCase
from app.schemas import TestCaseRead

router = APIRouter(prefix="/test-cases", tags=["test-cases"])


@router.get("", response_model=list[TestCaseRead])
def list_test_cases(session: Session = Depends(get_session)) -> list[TestCase]:
    return list(session.scalars(select(TestCase).order_by(TestCase.id)).all())
