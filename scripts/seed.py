"""Load eval/*.yaml into the database. Idempotent: upserts by natural keys."""
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import Criterion, PromptTemplate, TestCase

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"


def _load_yaml(name: str) -> dict:
    with (EVAL_DIR / name).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def seed_test_cases(session) -> int:
    data = _load_yaml("test_cases.yaml").get("cases", []) or []
    n = 0
    for entry in data:
        existing = session.scalar(select(TestCase).where(TestCase.title == entry["title"]))
        if existing:
            existing.context = entry.get("context", "")
            existing.question = entry["question"]
            existing.expected_behavior = entry.get("expected_behavior", {})
            existing.tags = entry.get("tags", [])
        else:
            session.add(
                TestCase(
                    title=entry["title"],
                    context=entry.get("context", ""),
                    question=entry["question"],
                    expected_behavior=entry.get("expected_behavior", {}),
                    tags=entry.get("tags", []),
                )
            )
        n += 1
    return n


def seed_prompts(session) -> int:
    data = _load_yaml("prompt_templates.yaml").get("templates", []) or []
    n = 0
    for entry in data:
        existing = session.scalar(
            select(PromptTemplate).where(
                PromptTemplate.name == entry["name"],
                PromptTemplate.version == entry["version"],
            )
        )
        if existing:
            existing.system_prompt = entry["system_prompt"]
            existing.user_template = entry["user_template"]
            existing.notes = entry.get("notes", "")
        else:
            session.add(
                PromptTemplate(
                    name=entry["name"],
                    version=entry["version"],
                    system_prompt=entry["system_prompt"],
                    user_template=entry["user_template"],
                    notes=entry.get("notes", ""),
                )
            )
        n += 1
    return n


def seed_criteria(session) -> int:
    data = _load_yaml("criteria.yaml").get("criteria", []) or []
    n = 0
    for entry in data:
        existing = session.scalar(select(Criterion).where(Criterion.name == entry["name"]))
        if existing:
            existing.description = entry.get("description", "")
            existing.type = entry["type"]
            existing.severity = entry["severity"]
            existing.examples = entry.get("examples", [])
        else:
            session.add(
                Criterion(
                    name=entry["name"],
                    description=entry.get("description", ""),
                    type=entry["type"],
                    severity=entry["severity"],
                    examples=entry.get("examples", []),
                )
            )
        n += 1
    return n


def main() -> None:
    init_db()
    with SessionLocal() as session:
        tc = seed_test_cases(session)
        pt = seed_prompts(session)
        cr = seed_criteria(session)
        session.commit()
    print(f"Seeded {tc} test cases, {pt} prompt templates, {cr} criteria.")


if __name__ == "__main__":
    main()
