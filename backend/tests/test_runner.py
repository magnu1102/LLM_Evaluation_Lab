from app.evaluation.runner import execute_run, render
from app.models import PromptTemplate, TestCase
from app.providers.mock_provider import MockProvider


def test_render_substitutes_placeholders():
    out = render("Ctx: {{context}} | Q: {{question}}", "C1", "Q1")
    assert out == "Ctx: C1 | Q: Q1"


def test_execute_run_persists_results_and_summary(session):
    prompt = PromptTemplate(
        name="grounded-summarizer",
        version=2,
        system_prompt="be careful",
        user_template="Context:\n{{context}}\n\nTask: {{question}}",
        notes="",
    )
    tc_cite = TestCase(
        title="cite",
        context="[1] retain only as long as necessary",
        question="Summarize with citation [n]",
        expected_behavior={
            "must_include": ["retain"],
            "requires_citation": True,
            "max_chars": 600,
        },
        tags=["citations"],
    )
    tc_refuse = TestCase(
        title="refuse",
        context="(none)",
        question="What is the deadline? [no context provided]",
        expected_behavior={"must_refuse": True, "max_chars": 400},
        tags=["refusal"],
    )
    session.add_all([prompt, tc_cite, tc_refuse])
    session.commit()

    run = execute_run(session, prompt, [tc_cite, tc_refuse], MockProvider())

    assert run.id is not None
    assert run.provider == "mock"
    assert run.summary["total"] == 2
    statuses = {r.test_case_id: r.status for r in run.results}
    assert statuses[tc_cite.id] == "pass"
    assert statuses[tc_refuse.id] == "pass"
    summed = run.summary["passed"] + run.summary["failed"] + run.summary["needs_review"]
    assert summed == 2
