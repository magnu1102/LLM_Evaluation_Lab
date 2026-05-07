# Scoring

This document describes how a single status is derived for each evaluation result, and why aggregation is kept deliberately simple.

## Per-result data

Every row in `evaluation_results` carries:

- `automatic_checks: list[{criterion, severity, passed, detail}]` — the full set of deterministic check outcomes that ran. Checks that don't apply to the test case (e.g. `required_citation` when `requires_citation` is false) are not stored, so the list reflects what was actually evaluated.
- `human_rating: "pass" | "fail" | "needs_review" | null`.
- `human_notes: str`.
- `status: "pass" | "fail" | "needs_review"` — derived; see below.

## Severities

Each check declares a severity:

- `fail` — a hard requirement; failing it should fail the result.
- `warn` — a soft signal; failing it should mark the result as needing review rather than failing it outright.
- `info` — informational only (reserved for future checks); does not affect status.

Current severity assignments live in [`eval/criteria.yaml`](../eval/criteria.yaml) and the matching check functions in [`backend/app/evaluation/checks.py`](../backend/app/evaluation/checks.py).

## `aggregate_status`

```
def aggregate_status(checks, human_rating):
    if human_rating in {"pass", "fail", "needs_review"}:
        return human_rating
    if any check with severity "fail" failed:
        return "fail"
    if any check with severity "warn" failed:
        return "needs_review"
    return "pass"
```

Properties this gives us:

- **Pure.** Takes the stored data, returns a status. Status can be recomputed at any time without re-running the model.
- **Human-overridable.** Reviewers can mark a result `pass` even if a `must_include` check failed — for example, when the check's word list is wrong. The underlying check outcomes remain visible.
- **No averaging.** There is no "score". Combining heuristic check results into a numeric score would imply more precision than the underlying signals warrant.

## When status changes

- After a run finishes, status is computed once for each result from its automatic checks.
- When `PATCH /results/{id}/review` is called, the result's status is recomputed using the new `human_rating`, and the parent run's `summary` counts (`passed`, `failed`, `needs_review`, `total`) are recomputed and saved.
- The dashboard and run detail pages invalidate their queries on review submit, so counts update without a manual refresh.

## What scoring deliberately does *not* do

- It does not weight checks. A single failed `must_include` and a single failed `required_citation` both produce `fail`; the reviewer reads the per-check details on the Run detail page to understand why.
- It does not produce a confidence number. The system has no calibrated probability to report and inventing one would be misleading.
- It does not collapse multiple runs into a leaderboard. Comparison is always between two specified runs (the Compare page), and the comparison is per-test-case rather than per-run aggregate.
