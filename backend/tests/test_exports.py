import csv
import io
import json

from app.evaluation.runner import execute_run
from app.models import PromptTemplate, TestCase
from app.providers.mock_provider import MockProvider


def _seed_run(session):
    prompt = PromptTemplate(
        name="grounded-summarizer",
        version=2,
        system_prompt="be careful",
        user_template="Context:\n{{context}}\n\nTask: {{question}}",
        notes="",
    )
    tc = TestCase(
        title="cite",
        context="[1] retain only as long as necessary",
        question="Summarize with citation [n]",
        expected_behavior={"requires_citation": True, "max_chars": 600},
        tags=["citations", "gdpr"],
    )
    session.add_all([prompt, tc])
    session.commit()
    return execute_run(session, prompt, [tc], MockProvider())


def test_export_json_returns_attachment(client, session):
    run = _seed_run(session)

    resp = client.get(f"/runs/{run.id}/export.json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert f"run-{run.id}.json" in resp.headers["content-disposition"]
    body = json.loads(resp.text)
    assert body["id"] == run.id
    assert body["summary"]["total"] == 1
    assert len(body["results"]) == 1


def test_export_csv_flattens_results(client, session):
    run = _seed_run(session)

    resp = client.get(f"/runs/{run.id}/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert f"run-{run.id}.csv" in resp.headers["content-disposition"]

    rows = list(csv.DictReader(io.StringIO(resp.text)))
    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == str(run.id)
    assert row["prompt_name"] == "grounded-summarizer"
    assert row["prompt_version"] == "2"
    assert row["test_case_title"] == "cite"
    assert "citations" in row["test_case_tags"]
    assert row["status"] in {"pass", "fail", "needs_review"}
    assert int(row["checks_passed"]) >= 1
    assert json.loads(row["automatic_checks"])  # parses


def test_export_404_when_run_missing(client):
    assert client.get("/runs/999/export.json").status_code == 404
    assert client.get("/runs/999/export.csv").status_code == 404
