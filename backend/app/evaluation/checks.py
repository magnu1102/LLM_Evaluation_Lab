"""Deterministic checks. Each returns a dict the runner stores verbatim.

A check outcome is `{criterion, severity, passed, detail}`. Heuristics, not truth —
that distinction is documented in docs/evaluation-design.md.
"""
from __future__ import annotations

import re

CITATION_RE = re.compile(r"\[(?:\d+|[a-zA-Z][\w\s-]{0,30})\]")

REFUSAL_PHRASES = (
    "i don't have enough information",
    "i do not have enough information",
    "cannot determine",
    "not specified",
    "insufficient context",
    "unable to answer",
    "no relevant information",
)


def _outcome(name: str, severity: str, passed: bool, detail: str = "") -> dict:
    return {"criterion": name, "severity": severity, "passed": passed, "detail": detail}


def check_required_citation(output: str, expected: dict) -> dict | None:
    if not expected.get("requires_citation"):
        return None
    has = bool(CITATION_RE.search(output))
    detail = "" if has else "no citation marker like [1] or [source] found"
    return _outcome("required_citation", "fail", has, detail)


def check_refusal_when_required(output: str, expected: dict) -> dict | None:
    if not expected.get("must_refuse"):
        return None
    text = output.lower()
    has = any(p in text for p in REFUSAL_PHRASES)
    detail = "" if has else "no refusal/uncertainty phrasing detected"
    return _outcome("refusal_when_required", "fail", has, detail)


def check_min_length(output: str, expected: dict) -> dict | None:
    min_chars = expected.get("min_chars")
    if not min_chars:
        return None
    ok = len(output) >= min_chars
    return _outcome(
        "min_length",
        "warn",
        ok,
        "" if ok else f"output is {len(output)} chars, expected at least {min_chars}",
    )


def check_max_length(output: str, expected: dict) -> dict | None:
    max_chars = expected.get("max_chars")
    if not max_chars:
        return None
    ok = len(output) <= max_chars
    return _outcome(
        "max_length",
        "warn",
        ok,
        "" if ok else f"output is {len(output)} chars, expected at most {max_chars}",
    )


def check_must_include(output: str, expected: dict) -> dict | None:
    terms = expected.get("must_include") or []
    if not terms:
        return None
    text = output.lower()
    missing = [t for t in terms if t.lower() not in text]
    return _outcome(
        "must_include",
        "fail",
        not missing,
        "" if not missing else f"missing terms: {missing}",
    )


def check_must_not_include(output: str, expected: dict) -> dict | None:
    terms = expected.get("must_not_include") or []
    if not terms:
        return None
    text = output.lower()
    found = [t for t in terms if t.lower() in text]
    return _outcome(
        "must_not_include",
        "fail",
        not found,
        "" if not found else f"forbidden terms present: {found}",
    )


def check_non_empty(output: str, _expected: dict) -> dict:
    ok = bool(output and output.strip())
    return _outcome("non_empty", "fail", ok, "" if ok else "model output is empty")


ALL_CHECKS = (
    check_non_empty,
    check_required_citation,
    check_refusal_when_required,
    check_must_include,
    check_must_not_include,
    check_min_length,
    check_max_length,
)


def run_checks(output: str, expected: dict) -> list[dict]:
    outcomes: list[dict] = []
    for fn in ALL_CHECKS:
        result = fn(output, expected)
        if result is not None:
            outcomes.append(result)
    return outcomes


def aggregate_status(outcomes: list[dict], human_rating: str | None = None) -> str:
    """Derive a single status from check outcomes. Human rating, when set, wins."""
    if human_rating in ("pass", "fail", "needs_review"):
        return human_rating
    has_fail = any(not o["passed"] and o["severity"] == "fail" for o in outcomes)
    if has_fail:
        return "fail"
    has_warn = any(not o["passed"] and o["severity"] == "warn" for o in outcomes)
    if has_warn:
        return "needs_review"
    return "pass"
