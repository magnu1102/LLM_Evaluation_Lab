import os

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.models import PromptTemplate, TestCase  # noqa: E402


def _seed(session) -> tuple[int, list[int]]:
    prompt = PromptTemplate(
        name="grounded-summarizer",
        version=2,
        system_prompt="be careful",
        user_template="Context:\n{{context}}\n\nTask: {{question}}",
        notes="",
    )
    tc1 = TestCase(
        title="policy",
        context="process each case in order before the deadline",
        question="Summarize the policy",
        expected_behavior={"must_include": ["order", "deadline"], "max_chars": 400},
        tags=["policy"],
    )
    tc2 = TestCase(
        title="support",
        context="restart the device",
        question="Draft a support reply",
        expected_behavior={"must_include": ["restart"], "max_chars": 240},
        tags=["support"],
    )
    session.add_all([prompt, tc1, tc2])
    session.commit()
    return prompt.id, [tc1.id, tc2.id]


def test_list_endpoints_empty(client):
    assert client.get("/test-cases").json() == []
    assert client.get("/prompt-templates").json() == []


def test_create_run_and_review_flow(client, session):
    prompt_id, case_ids = _seed(session)

    resp = client.post(
        "/runs",
        json={"prompt_template_id": prompt_id, "test_case_ids": case_ids},
    )
    # 202 Accepted: run is queued, BackgroundTasks runs synchronously under
    # TestClient so by the time we GET below, the run is finished.
    assert resp.status_code == 202, resp.text
    queued = resp.json()
    assert queued["state"] == "pending"
    assert queued["summary"]["total"] == 2
    assert queued["results"] == []

    run = client.get(f"/runs/{queued['id']}").json()
    assert run["state"] == "completed"
    assert run["summary"]["total"] == 2
    assert len(run["results"]) == 2

    target = run["results"][0]
    review = client.patch(
        f"/results/{target['id']}/review",
        json={"human_rating": "needs_review", "human_notes": "looked off"},
    )
    assert review.status_code == 200
    body = review.json()
    assert body["status"] == "needs_review"
    assert body["human_notes"] == "looked off"

    refreshed = client.get(f"/runs/{run['id']}").json()
    assert refreshed["summary"]["needs_review"] >= 1


def test_create_run_records_failed_state_on_provider_error(client, session, monkeypatch):
    prompt_id, case_ids = _seed(session)

    def boom(*_args, **_kwargs):
        raise RuntimeError("upstream is on fire")

    from app.providers.mock_provider import MockProvider

    monkeypatch.setattr(MockProvider, "complete", boom)

    resp = client.post(
        "/runs",
        json={"prompt_template_id": prompt_id, "test_case_ids": case_ids},
    )
    assert resp.status_code == 202
    run = client.get(f"/runs/{resp.json()['id']}").json()
    assert run["state"] == "failed"
    assert "upstream is on fire" in (run["summary"].get("error") or "")


def test_create_run_404_on_missing_prompt(client):
    resp = client.post("/runs", json={"prompt_template_id": 999, "test_case_ids": []})
    assert resp.status_code == 404
