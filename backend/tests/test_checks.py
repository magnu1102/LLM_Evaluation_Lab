from app.evaluation.checks import (
    aggregate_status,
    check_max_length,
    check_min_length,
    check_must_include,
    check_must_not_include,
    check_non_empty,
    check_refusal_when_required,
    check_required_citation,
    run_checks,
)


def test_non_empty():
    assert check_non_empty("hi", {})["passed"]
    assert not check_non_empty("   ", {})["passed"]


def test_required_citation_only_when_required():
    assert check_required_citation("text [1]", {"requires_citation": True})["passed"]
    assert not check_required_citation("text", {"requires_citation": True})["passed"]
    assert check_required_citation("text", {}) is None


def test_refusal_when_required():
    assert check_refusal_when_required(
        "I don't have enough information.", {"must_refuse": True}
    )["passed"]
    assert not check_refusal_when_required("It's 30 days.", {"must_refuse": True})["passed"]
    assert check_refusal_when_required("anything", {}) is None


def test_must_include_and_exclude():
    out = check_must_include("Process in order before deadline.", {"must_include": ["order"]})
    assert out["passed"]
    out = check_must_include("nope", {"must_include": ["order"]})
    assert not out["passed"]
    out = check_must_not_include("offers a refund", {"must_not_include": ["refund"]})
    assert not out["passed"]


def test_length_bounds():
    assert check_min_length("12345", {"min_chars": 3})["passed"]
    assert not check_min_length("ab", {"min_chars": 3})["passed"]
    assert check_max_length("ab", {"max_chars": 5})["passed"]
    assert not check_max_length("a" * 10, {"max_chars": 5})["passed"]


def test_run_checks_skips_inapplicable():
    outcomes = run_checks("hello", {})
    names = {o["criterion"] for o in outcomes}
    assert names == {"non_empty"}


def test_aggregate_status_priority():
    fail = {"criterion": "x", "severity": "fail", "passed": False, "detail": ""}
    warn = {"criterion": "y", "severity": "warn", "passed": False, "detail": ""}
    ok = {"criterion": "z", "severity": "fail", "passed": True, "detail": ""}
    assert aggregate_status([ok]) == "pass"
    assert aggregate_status([warn, ok]) == "needs_review"
    assert aggregate_status([fail, warn]) == "fail"


def test_human_rating_overrides():
    fail = {"criterion": "x", "severity": "fail", "passed": False, "detail": ""}
    assert aggregate_status([fail], human_rating="pass") == "pass"
