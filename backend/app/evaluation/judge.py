"""Optional LLM-as-judge check.

The judge takes a single test case (context, question, expected behaviour) and
the model output, and asks the configured provider for a structured verdict.
Its outcome is appended to the result's automatic_checks list with
severity "info" so it is visible but never overrides status — see
docs/evaluation-design.md.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.providers import LLMProvider

JUDGE_SYSTEM = (
    "You are an evaluation judge. Given a test case and a candidate answer, "
    "decide whether the answer satisfies the expected behaviour. "
    "Respond ONLY with a single JSON object on one line, no prose, no code fences, "
    "matching this schema:\n"
    '{"verdict": "pass" | "fail" | "needs_review", "reason": "<one short sentence>"}'
)


JUDGE_USER_TEMPLATE = """\
Question:
{question}

Context provided to the model:
{context}

Expected behaviour (machine-readable):
{expected}

Candidate answer:
{output}

Return only the JSON verdict object.
"""


_VALID_VERDICTS = {"pass", "fail", "needs_review"}


def _parse_verdict(raw: str) -> tuple[str, str]:
    """Extract (verdict, reason) from a free-form judge response.

    Tries strict JSON first, then a permissive {...} extraction. On failure,
    returns ("needs_review", "<unparseable judge response>") so the result
    surfaces in the UI rather than being silently dropped.
    """
    text = (raw or "").strip()
    candidates: list[str] = []
    if text:
        candidates.append(text)
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            candidates.append(match.group(0))

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        verdict = str(payload.get("verdict", "")).strip().lower()
        reason = str(payload.get("reason", "")).strip()
        if verdict in _VALID_VERDICTS:
            return verdict, reason or "(no reason given)"

    snippet = text[:120].replace("\n", " ")
    return "needs_review", f"unparseable judge response: {snippet!r}"


def judge_output(
    provider: LLMProvider,
    *,
    question: str,
    context: str,
    expected_behavior: dict[str, Any],
    model_output: str,
) -> dict:
    user = JUDGE_USER_TEMPLATE.format(
        question=question,
        context=context or "(none)",
        expected=json.dumps(expected_behavior or {}, ensure_ascii=False),
        output=model_output,
    )
    resp = provider.complete(JUDGE_SYSTEM, user)
    verdict, reason = _parse_verdict(resp.text)
    return {
        "criterion": "llm_judge",
        "severity": "info",
        "passed": verdict == "pass",
        "detail": f"verdict={verdict}; {reason}",
    }
