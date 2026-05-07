# Evaluation design

The design principle of this project is that **evaluation is layered and visible**. Each layer is a signal with known limits; no layer is treated as ground truth. The system stores enough to disagree with itself — automatic outcomes and human ratings sit side by side, never overwriting each other.

## The four layers

### 1. Deterministic checks
Pure functions over the model output and the test case's `expected_behavior`. They are cheap, reproducible, and narrow. Current checks:

| Check | Severity | When it applies |
|-------|----------|----------------|
| `non_empty` | fail | Always |
| `required_citation` | fail | `expected.requires_citation == true` |
| `refusal_when_required` | fail | `expected.must_refuse == true` |
| `must_include` | fail | `expected.must_include` non-empty |
| `must_not_include` | fail | `expected.must_not_include` non-empty |
| `min_length` | warn | `expected.min_chars` set |
| `max_length` | warn | `expected.max_chars` set |

Each check returns `{criterion, severity, passed, detail}` and the runner stores the full list verbatim on the result row. Implementation: [`backend/app/evaluation/checks.py`](../backend/app/evaluation/checks.py).

These are heuristics. A regex-based citation detector accepts `[1]` and rejects "see source 1"; a refusal-phrase list will miss novel phrasing. False positives and false negatives are both possible and expected.

### 2. Structured criteria
The `criteria` table names each check, sets its severity, and carries a description and examples. This makes the evaluation rubric reviewable in YAML and visible to non-engineers, and keeps severity changes (warn ↔ fail) data-driven rather than spread through code.

### 3. Human review
Every result has `human_rating` (`pass` | `fail` | `needs_review` | `null`) and `human_notes`. Reviewers set them via the Run detail page. When `human_rating` is set, `aggregate_status` returns it directly — but the underlying automatic checks remain on the row, so disagreements stay visible rather than getting silently overwritten.

### 4. LLM-as-judge (optional)
Implemented as an opt-in criterion. When `enable_llm_judge` is set on a run, the runner makes one extra provider call per test case asking for a structured JSON verdict (`pass | fail | needs_review` plus a one-sentence reason). The verdict is stored in `automatic_checks` with `criterion = "llm_judge"` and `severity = "info"`, so it is **always visible but never moves status**. It is a parallel signal, not a tiebreaker.

The judge prompt lives in [`backend/app/evaluation/judge.py`](../backend/app/evaluation/judge.py). Parsing is permissive: strict JSON first, then a `{...}` substring match, falling back to `needs_review` with the raw text recorded in the detail. Judge models tend to favour outputs that resemble their own style; that's exactly why severity is `info` and why the deterministic checks remain the basis for the result's status.

## Status aggregation

`aggregate_status(checks, human_rating)` derives a single `pass | fail | needs_review` from the data:

1. If `human_rating` is `pass | fail | needs_review`, return it.
2. Else if any check with severity `fail` failed, return `fail`.
3. Else if any check with severity `warn` failed, return `needs_review`.
4. Else return `pass`.

This is intentionally simple. The status is a triage signal, not a score, and it is recomputed on every review change so the dashboard counts stay consistent.

## Comparing prompts

The Compare page groups test cases between two runs into:

- **Improved** — A wasn't pass, B is pass.
- **Regressed** — A was pass, B isn't pass.
- **Other change** — status changed but not in pass↔non-pass directions (e.g. `fail` → `needs_review`).
- **Unchanged** — same status.

Because runs typically differ only by prompt version (or by model), this surfaces prompt regressions directly. A clean improvement is "no Regressed cases, some Improved cases"; the reviewer's job is to confirm the Improved cases are real wins and not the heuristic flipping for the wrong reason.

## What would *not* be honest

- Reporting a percentage like "this prompt is 87% accurate" from a handful of seeded cases. Sample size is too small and the checks are heuristic.
- Treating LLM-as-judge agreement as a tiebreaker. Judge models drift toward outputs that resemble themselves.
- Hiding the deterministic checks behind a single status pill. The Run detail page always shows the full check list per result.
