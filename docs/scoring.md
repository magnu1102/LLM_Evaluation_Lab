# Scoring

> Placeholder — implemented in Phase 2.

Each result has:

- a list of automatic check outcomes `{criterion, passed, severity, detail}`,
- an optional `human_rating` (`pass` | `fail` | `needs_review`),
- a derived `status` from `aggregate_status(checks, human_rating)`.

Aggregation rules (planned):

- Any failing check with severity `fail` → status `fail`.
- Any failing check with severity `warn` and no `fail` → status `needs_review`.
- All checks pass → status `pass`.
- A `human_rating`, when present, overrides the derived status (and is shown alongside it).
