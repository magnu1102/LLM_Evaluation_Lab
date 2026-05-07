from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .result import ResultRead


class RunCreate(BaseModel):
    prompt_template_id: int
    test_case_ids: list[int] = Field(default_factory=list, description="Empty means all")
    model: str | None = None  # override provider default


class RunSummary(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    needs_review: int = 0


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_template_id: int
    provider: str
    model: str
    started_at: datetime
    finished_at: datetime | None
    summary: RunSummary
    results: list[ResultRead] = Field(default_factory=list)
