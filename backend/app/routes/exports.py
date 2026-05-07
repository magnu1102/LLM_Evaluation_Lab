"""Export a run as a downloadable JSON or CSV file.

JSON mirrors the GET /runs/{id} payload. CSV flattens results into one row per
test case with summary check counts and the full automatic_checks JSON.
"""
from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import EvaluationRun
from app.schemas import RunRead

router = APIRouter(prefix="/runs", tags=["runs"])

CSV_COLUMNS = (
    "run_id",
    "run_started_at",
    "prompt_name",
    "prompt_version",
    "provider",
    "model",
    "result_id",
    "test_case_id",
    "test_case_title",
    "test_case_tags",
    "status",
    "human_rating",
    "human_notes",
    "latency_ms",
    "checks_passed",
    "checks_failed",
    "checks_warned",
    "automatic_checks",
    "model_output",
)


def _filename(run: EvaluationRun, ext: str) -> str:
    return f"run-{run.id}.{ext}"


def _attachment_headers(filename: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}


@router.get("/{run_id}/export.json")
def export_run_json(run_id: int, session: Session = Depends(get_session)) -> Response:
    run = session.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")
    payload = RunRead.model_validate(run).model_dump(mode="json")
    body = json.dumps(payload, indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers=_attachment_headers(_filename(run, "json")),
    )


@router.get("/{run_id}/export.csv")
def export_run_csv(run_id: int, session: Session = Depends(get_session)) -> Response:
    run = session.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")

    prompt = run.prompt_template
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS)

    for r in run.results:
        checks = r.automatic_checks or []
        passed = sum(1 for c in checks if c.get("passed"))
        failed = sum(
            1 for c in checks if not c.get("passed") and c.get("severity") == "fail"
        )
        warned = sum(
            1 for c in checks if not c.get("passed") and c.get("severity") == "warn"
        )
        tc = r.test_case
        writer.writerow(
            [
                run.id,
                run.started_at.isoformat() if run.started_at else "",
                prompt.name if prompt else "",
                prompt.version if prompt else "",
                run.provider,
                run.model,
                r.id,
                r.test_case_id,
                tc.title if tc else "",
                ",".join(tc.tags) if tc and tc.tags else "",
                r.status,
                r.human_rating or "",
                r.human_notes or "",
                r.latency_ms,
                passed,
                failed,
                warned,
                json.dumps(checks, ensure_ascii=False),
                r.model_output or "",
            ]
        )

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers=_attachment_headers(_filename(run, "csv")),
    )
