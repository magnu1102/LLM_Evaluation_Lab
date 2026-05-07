# Architecture

## Components

```
┌────────────┐        REST/JSON        ┌─────────────────┐        ┌────────────┐
│  Frontend  │ ──────────────────────▶ │     Backend     │ ─────▶ │ PostgreSQL │
│ React+Vite │ ◀────────────────────── │ FastAPI + SQLA  │ ◀───── │            │
└────────────┘                         └────────┬────────┘        └────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │  LLM provider   │
                                       │  (openai|mock)  │
                                       └─────────────────┘
```

- **Frontend** (`frontend/`): React + TypeScript + Vite. Pages: Dashboard, New run, Run detail, Compare, Health. Data fetching via TanStack Query.
- **Backend** (`backend/`): FastAPI on Python 3.12 with SQLAlchemy 2.x and Alembic. Synchronous request/response — runs execute inline against the configured provider, then return the full run document.
- **Database**: PostgreSQL 16. Schema is owned by Alembic migrations (`backend/alembic/versions/`).
- **LLM provider** is selected at runtime by the `LLM_PROVIDER` env (`openai` or `mock`). The mock provider is deterministic and lets the whole stack run end-to-end with no API key.

## Request flow — `POST /runs`

`POST /runs` returns immediately and the work happens in a FastAPI `BackgroundTasks` worker. The run row carries a `state` column that progresses `pending → running → completed | failed`; the UI polls while the run is non-terminal.

1. UI submits `{prompt_template_id, test_case_ids?, model?, enable_llm_judge?}` from the New run page.
2. Backend validates the prompt and selected test cases, creates an `EvaluationRun` row with `state="pending"` and an empty result set, and returns `202 Accepted` with the queued run.
3. After the response is sent, `execute_pending_run(run_id, ...)` runs in the background: it opens its own session, marks `state="running"`, iterates the cases via the runner, and writes results as it goes.
4. On success the run is marked `state="completed"` with the final summary counts. On any exception the run is marked `state="failed"` with the error string captured in `summary.error` (truncated).
5. The UI's run-detail and dashboard queries poll while any run is non-terminal and stop polling once it reaches `completed` or `failed`.

## Review flow — `PATCH /results/{id}/review`

1. The Run detail page submits `{human_rating, human_notes}`.
2. The backend stores the rating/notes and re-derives `status` via `aggregate_status` (a human rating, when present, overrides the automatic status). The parent run's summary is recomputed.
3. The UI invalidates the run and runs queries; counts on the dashboard update.

## Module map

| Path | Responsibility |
|------|----------------|
| `backend/app/main.py` | App factory, CORS, router includes |
| `backend/app/config.py` | Env-driven settings (Pydantic Settings) |
| `backend/app/db.py` | Engine, `SessionLocal`, `Base`, `init_db()` |
| `backend/app/models/` | SQLAlchemy declarative models |
| `backend/app/schemas/` | Pydantic v2 request/response models |
| `backend/app/providers/` | `LLMProvider` protocol + OpenAI / mock adapters |
| `backend/app/evaluation/checks.py` | Pure deterministic checks + `aggregate_status` |
| `backend/app/evaluation/runner.py` | Orchestrates a run end-to-end |
| `backend/app/routes/` | FastAPI routers per resource |
| `backend/alembic/` | Schema migrations |
| `eval/*.yaml` | Seed test cases, prompt templates, criteria |
| `scripts/` | `seed.py`, `run_eval.py`, `reset_db.py` |
| `frontend/src/pages/` | Dashboard, New run, Run detail, Compare, Health |
| `frontend/src/lib/api.ts` | Typed API client |

## What's deliberately not here

- **Auth, multi-tenant, RBAC.** Out of scope; documented in [limitations.md](limitations.md).
- **External job queue.** Runs execute in-process via FastAPI `BackgroundTasks`. That's enough for a single-instance deployment and small case sets but won't survive a restart mid-run, won't scale to multiple workers, and won't retry on failure. A real queue (Celery / RQ / ARQ + Redis) is the right next step if this graduates beyond a portfolio piece.
- **Model routing / fallbacks.** A single provider per run, chosen by env. A second adapter would slot into `providers/` without changing the runner.
