"""Test case CRUD-lite + dataset import/export.

Export and import use the same shape as `eval/test_cases.yaml` so files
round-trip cleanly between the seed YAML and the API.
"""
from __future__ import annotations

import json

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import TestCase
from app.schemas import TestCaseRead

router = APIRouter(prefix="/test-cases", tags=["test-cases"])


def _serialize(tc: TestCase) -> dict:
    return {
        "title": tc.title,
        "tags": list(tc.tags or []),
        "context": tc.context or "",
        "question": tc.question,
        "expected_behavior": dict(tc.expected_behavior or {}),
    }


def _attachment(filename: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}


@router.get("", response_model=list[TestCaseRead])
def list_test_cases(session: Session = Depends(get_session)) -> list[TestCase]:
    return list(session.scalars(select(TestCase).order_by(TestCase.id)).all())


@router.get("/export.yaml")
def export_test_cases_yaml(session: Session = Depends(get_session)) -> Response:
    cases = list(session.scalars(select(TestCase).order_by(TestCase.id)).all())
    payload = {"cases": [_serialize(c) for c in cases]}
    body = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    return Response(
        content=body,
        media_type="application/x-yaml",
        headers=_attachment("test_cases.yaml"),
    )


@router.get("/export.json")
def export_test_cases_json(session: Session = Depends(get_session)) -> Response:
    cases = list(session.scalars(select(TestCase).order_by(TestCase.id)).all())
    payload = {"cases": [_serialize(c) for c in cases]}
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers=_attachment("test_cases.json"),
    )


@router.post("/import")
def import_test_cases(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict:
    """Upsert test cases from a YAML or JSON file matching the seed format.

    YAML is a superset of JSON for our shapes, so we parse with PyYAML and
    accept either. Rows are matched by `title`. Entries missing required
    fields are reported in `errors`; valid entries in the same upload still
    commit.
    """
    raw = file.file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, f"file must be UTF-8: {exc}") from exc
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise HTTPException(400, f"could not parse YAML/JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise HTTPException(400, "top-level must be a mapping with a `cases` key")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise HTTPException(400, "expected top-level `cases` list")

    created = 0
    updated = 0
    errors: list[dict] = []

    for i, entry in enumerate(cases):
        if not isinstance(entry, dict):
            errors.append({"index": i, "error": "entry must be a mapping"})
            continue
        title = str(entry.get("title", "") or "").strip()
        question = str(entry.get("question", "") or "").strip()
        if not title or not question:
            errors.append({"index": i, "error": "title and question are required"})
            continue
        expected = entry.get("expected_behavior") or {}
        if not isinstance(expected, dict):
            errors.append({"index": i, "error": "expected_behavior must be a mapping"})
            continue
        tags = entry.get("tags") or []
        if not isinstance(tags, list):
            errors.append({"index": i, "error": "tags must be a list"})
            continue

        context = str(entry.get("context", "") or "")
        existing = session.scalar(select(TestCase).where(TestCase.title == title))
        if existing is not None:
            existing.context = context
            existing.question = question
            existing.expected_behavior = expected
            existing.tags = list(tags)
            updated += 1
        else:
            session.add(
                TestCase(
                    title=title,
                    context=context,
                    question=question,
                    expected_behavior=expected,
                    tags=list(tags),
                )
            )
            created += 1

    session.commit()
    return {"created": created, "updated": updated, "errors": errors}
