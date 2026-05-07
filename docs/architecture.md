# Architecture

> Placeholder — fleshed out in Phase 4.

## Components

- **Backend (FastAPI):** REST API for test cases, prompt templates, evaluation runs, and results.
- **Database (Postgres):** stores test cases, prompts, criteria, runs, and results.
- **LLM provider adapter:** thin abstraction (`openai`, `mock`) selected via `LLM_PROVIDER` env.
- **Frontend (React + Vite):** dashboard, run launcher, results review, and run comparison.

## Request flow (planned)

```
UI → POST /runs → backend renders prompt → provider.complete()
   → store output → run deterministic checks → aggregate status
   → return run summary → UI polls /runs/{id}
```
