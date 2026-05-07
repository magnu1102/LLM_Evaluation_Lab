from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpectedBehavior(BaseModel):
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    requires_citation: bool = False
    must_refuse: bool = False
    min_chars: int | None = None
    max_chars: int | None = None


class TestCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    context: str
    question: str
    expected_behavior: ExpectedBehavior
    tags: list[str]
    created_at: datetime
