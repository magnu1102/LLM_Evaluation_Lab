from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Criterion(Base):
    __tablename__ = "criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # deterministic|human|llm_judge
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # info|warn|fail
    examples: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
