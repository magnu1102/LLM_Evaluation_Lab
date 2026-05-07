# Evaluation design

> Placeholder — fleshed out in Phase 4.

Evaluation in this project is layered. Each layer is treated as a signal, not as ground truth.

1. **Deterministic checks** — citations, refusal phrasing, length bounds, must / must-not include terms. Cheap, reproducible, narrow.
2. **Structured criteria** — named criteria with severities (`info`, `warn`, `fail`) applied per test case.
3. **Human review** — first-class, stored alongside automatic checks. Never overwritten by automation.
4. **LLM-as-judge (future)** — optional, with disclosed prompt and known biases. Never the sole signal.

The system records both automatic and human judgments. Disagreement is information, not a bug.
