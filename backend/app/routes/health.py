from fastapi import APIRouter

from app.config import settings
from app.db import db_ok

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "db": db_ok(),
        "provider": settings.llm_provider,
        "provider_configured": settings.provider_configured,
    }
