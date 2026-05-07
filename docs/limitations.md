# Limitations

> Placeholder — expanded in Phase 4.

This project is a small evaluation harness, not a benchmark suite. Honest limits:

- **Deterministic checks are heuristics.** Citation regexes, refusal-phrase lists, and length bounds are easy to game and easy to false-positive. Treat them as signals.
- **Small samples, no statistical claims.** A run over a handful of seeded cases is not a benchmark; do not present pass rates as accuracy.
- **LLM-as-judge (when added) has bias.** It tends to agree with similar-style outputs and with itself. It will not be used as a tiebreaker.
- **No multi-tenant, no auth, no model routing.** Out of scope by design.
- **Synthetic test data only.** No real personal data, no real case files.
