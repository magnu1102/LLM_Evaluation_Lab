from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_template_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_templates.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    state: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False
    )  # pending | running | completed | failed
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    prompt_template = relationship("PromptTemplate")
    results = relationship(
        "EvaluationResult",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.id",
    )
