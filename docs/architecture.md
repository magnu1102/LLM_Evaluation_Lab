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

1. UI submits `{prompt_template_id, test_case_ids?, model?}` from the New run page.
2. Backend loads the prompt template and the selected test cases.
3. For each test case, the runner (`backend/app/evaluation/runner.py`) renders the user template (`{{context}}` and `{{question}}` placeholders), calls `provider.complete(system, user)`, and stores the model output, latency, automatic check outcomes, and a derived status.
4. After all cases, the run's summary counts are written and the full `RunRead` document is returned.
5. The UI invalidates the runs query and navigates to `/runs/{id}`.

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
- **Async / queued runs.** Runs execute synchronously inside the request. With a real provider and many cases this becomes a bottleneck; that's acceptable for the current scale and surfaces clearly to the user via the loading state.
- **Model routing / fallbacks.** A single provider per run, chosen by env. A second adapter would slot into `providers/` without changing the runner.
