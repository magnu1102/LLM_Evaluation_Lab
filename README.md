# LLM Evaluation Lab

A small, focused tool for evaluating LLM outputs across prompts, models and test cases.

This is a developer/evaluation tool — not a chatbot. It helps answer questions like:

- Did the LLM answer using the provided context, or invent facts?
- Did it include citations when required?
- Did it refuse or qualify the answer when context was insufficient?
- Did a new prompt version improve or worsen results compared to a previous one?
- Which test cases keep failing?

## Status

Phase 1 — project skeleton. Backend exposes `/health`; frontend renders a health badge; Postgres runs in Docker Compose. No LLM calls yet.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic
- **Frontend:** React + TypeScript + Vite
- **Database:** PostgreSQL 16
- **Local orchestration:** Docker Compose
- **LLM provider:** configured via env (`LLM_PROVIDER=openai|mock`)

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Backend: <http://localhost:8000/health>
- Frontend: <http://localhost:5173>

## Layout

```
backend/    FastAPI app + tests
frontend/   Vite + React + TS app
docs/       architecture, evaluation design, scoring, limitations
eval/       seed test cases, prompt templates, criteria (YAML)
scripts/    DB reset, seed, run-eval CLIs
```

## Evaluation model (preview)

Evaluation has layers, in order of confidence:

1. **Deterministic checks** — citation presence, refusal phrasing, length bounds, must/must-not include terms.
2. **Structured criteria** — named criteria with severities applied across runs.
3. **Human review** — first-class, stored alongside automatic checks; never overwritten.
4. **LLM-as-judge** — optional future addition with disclosed limitations.

Automatic checks are signals, not ground truth. The UI surfaces both automatic checks and human review and never silently merges them.

## Roadmap

See the build phases in the project notes. Phase 2 adds models, seed data, the evaluation runner, and the deterministic checks. Phase 3 brings the UI for running evaluations and reviewing results. Phase 4 adds run comparison and full docs.

## License

MIT — see [LICENSE](LICENSE).
