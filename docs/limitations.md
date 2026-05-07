# Limitations

This is a small, focused evaluation harness. The list below is what it intentionally does *not* do, and what readers should keep in mind when interpreting results.

## Evaluation limits

- **Deterministic checks are heuristics.** A regex-based citation check accepts `[1]` or `[source]` and rejects "see source 1". A refusal-phrase list will miss novel phrasings of "I don't know". Both false positives and false negatives are possible and expected.
- **Small sample sizes, no statistical claims.** The seed set is a handful of synthetic test cases. Pass rates from this set are not benchmarks and should not be presented as accuracy figures.
- **Status is triage, not a score.** `pass | fail | needs_review` is a routing signal. It is not weighted, not calibrated, and not comparable across very different test sets.
- **LLM-as-judge is one signal among others.** When `enable_llm_judge` is set on a run, the judge runs at severity `info`, so it never overrides deterministic checks or human review. Judge models tend to favour outputs that resemble their own style; using a different provider for the judge than for the answer is one way to reduce that bias, but it does not eliminate it.
- **No causal claims about prompt changes.** The Compare page surfaces which test cases changed status between two runs. With small samples, single-run noise can look like a regression. Reviewers are expected to confirm before drawing conclusions.

## System limits

- **In-process background work, no real queue.** `POST /runs` returns 202 immediately and the work runs via FastAPI `BackgroundTasks` inside the same process. That avoids long-blocking requests but won't survive a restart mid-run, won't fan out across workers, and won't retry on failure. For multi-worker or restart-tolerant deployments a real queue (e.g. ARQ + Redis) is the right next step.
- **Single provider per run.** Selected via `LLM_PROVIDER`. The provider abstraction is in place, but there is no per-run multi-provider routing.
- **No retries on provider failure.** A failing provider call propagates as a 500. There is no per-result retry policy.
- **No streaming output, no partial progress.** The UI shows a "running…" state and waits for the final response.

## Out-of-scope by design

- **Authentication, multi-tenant separation, RBAC.** This is a single-user local tool.
- **Production-grade secrets management.** API keys are read from environment; rotation, scoping, and audit are the operator's responsibility.
- **Real datasets.** All seed test cases are synthetic. No real personal data, no real case files. Importing real datasets would require, at minimum: PII scrubbing, retention rules, and access controls — none of which are in this codebase.
- **Public sharing of runs.** The dashboard lists runs without any access checks. Do not expose the backend on a public network.

## Things to be careful about reading

- A run's "passed" count includes results where every applicable deterministic check passed, *or* a reviewer manually marked it pass. The counts collapse those cases together — open the Run detail page to see which is which.
- Two runs can have identical pass counts and still differ on which test cases passed. Always compare runs case-by-case (the Compare page does this).
- A test case's `expected_behavior` is itself a piece of data that can be wrong. If a `must_include` term is misspelled or a `requires_citation` flag is set incorrectly, every run will look "wrong" for the same reason.
