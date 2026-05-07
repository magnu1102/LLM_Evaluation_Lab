from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["pass", "fail", "needs_review"]


class CheckOutcome(BaseModel):
    criterion: str
    severity: str
    passed: bool
    detail: str = ""


class ResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    test_case_id: int
    model_output: str
    latency_ms: int
    automatic_checks: list[CheckOutcome]
    human_rating: Status | None
    human_notes: str
    status: Status


class ReviewIn(BaseModel):
    human_rating: Status | None = Field(default=None)
    human_notes: str = ""
