from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import PromptTemplate
from app.schemas import PromptTemplateRead

router = APIRouter(prefix="/prompt-templates", tags=["prompt-templates"])


@router.get("", response_model=list[PromptTemplateRead])
def list_prompt_templates(session: Session = Depends(get_session)) -> list[PromptTemplate]:
    return list(
        session.scalars(
            select(PromptTemplate).order_by(PromptTemplate.name, PromptTemplate.version)
        ).all()
    )
