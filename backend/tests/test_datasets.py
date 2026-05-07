import io
import json

import yaml

from app.models import TestCase


def _seed(session) -> None:
    session.add_all(
        [
            TestCase(
                title="Citation case",
                context="[1] retain only as long as necessary",
                question="Summarize with citation [n]",
                expected_behavior={"requires_citation": True, "max_chars": 600},
                tags=["citations", "gdpr"],
            ),
            TestCase(
                title="Refusal case",
                context="(none)",
                question="What is the deadline?",
                expected_behavior={"must_refuse": True},
                tags=["refusal"],
            ),
        ]
    )
    session.commit()


def test_export_yaml_round_trips_seed_format(client, session):
    _seed(session)
    resp = client.get("/test-cases/export.yaml")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/x-yaml")
    assert "test_cases.yaml" in resp.headers["content-disposition"]
    payload = yaml.safe_load(resp.text)
    assert isinstance(payload, dict) and "cases" in payload
    titles = [c["title"] for c in payload["cases"]]
    assert titles == ["Citation case", "Refusal case"]
    assert payload["cases"][0]["expected_behavior"]["requires_citation"] is True


def test_export_json_round_trips(client, session):
    _seed(session)
    resp = client.get("/test-cases/export.json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    payload = json.loads(resp.text)
    assert {c["title"] for c in payload["cases"]} == {"Citation case", "Refusal case"}


def test_import_creates_and_updates_by_title(client, session):
    _seed(session)
    payload = {
        "cases": [
            {
                "title": "Citation case",  # existing — should update
                "tags": ["citations"],
                "context": "(updated context)",
                "question": "(updated question)",
                "expected_behavior": {"requires_citation": True},
            },
            {
                "title": "Brand new case",  # new — should create
                "tags": ["new"],
                "context": "ctx",
                "question": "q?",
                "expected_behavior": {"max_chars": 100},
            },
        ]
    }
    body = yaml.safe_dump(payload).encode("utf-8")
    resp = client.post(
        "/test-cases/import",
        files={"file": ("upload.yaml", io.BytesIO(body), "application/x-yaml")},
    )
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary == {"created": 1, "updated": 1, "errors": []}

    titles = {tc.title for tc in session.scalars(__import__("sqlalchemy").select(TestCase)).all()}
    assert "Brand new case" in titles
    refreshed = session.query(TestCase).filter_by(title="Citation case").one()
    assert refreshed.context == "(updated context)"
    assert refreshed.question == "(updated question)"


def test_import_collects_per_entry_errors_without_failing_the_whole_upload(client, session):
    payload = {
        "cases": [
            {"title": "Good", "question": "q", "expected_behavior": {}, "tags": []},
            {"title": "", "question": "no title"},
            {"title": "no question"},
            {"title": "Bad expected", "question": "q", "expected_behavior": "should be a dict"},
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    resp = client.post(
        "/test-cases/import",
        files={"file": ("upload.json", io.BytesIO(body), "application/json")},
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["created"] == 1
    assert summary["updated"] == 0
    assert len(summary["errors"]) == 3
    assert {e["index"] for e in summary["errors"]} == {1, 2, 3}


def test_import_rejects_non_yaml(client):
    resp = client.post(
        "/test-cases/import",
        files={"file": ("upload.bin", io.BytesIO(b"\x00\x01\x02"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_import_rejects_wrong_top_level(client):
    body = yaml.safe_dump([{"title": "x"}]).encode("utf-8")
    resp = client.post(
        "/test-cases/import",
        files={"file": ("upload.yaml", io.BytesIO(body), "application/x-yaml")},
    )
    assert resp.status_code == 400
