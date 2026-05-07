# LLM Evaluation Lab

A small, focused tool for evaluating LLM outputs across prompts, models and test cases.

This is a developer/evaluation tool — not a chatbot. It helps answer questions like:

- Did the LLM answer using the provided context, or invent facts?
- Did it include citations when required?
- Did it refuse or qualify the answer when context was insufficient?
- Did a new prompt version improve or worsen results compared to a previous one?
- Which test cases keep failing?

## Why this exists

Most "is this LLM working?" answers are vibes. This project demonstrates a more honest workflow: define test cases, define what good looks like per case, run the model, run deterministic checks, and let a human review the results — with both signals stored side by side. It also supports comparing two runs (typically two prompt versions) to surface regressions.

It is meant as a portfolio piece for AI engineering, software development, and data/governance work, so the design choices and limitations are documented in [`docs/`](docs/).

## Features

- **Test cases as data** in [`eval/test_cases.yaml`](eval/test_cases.yaml) with explicit `expected_behavior` (must include / must not include, citation required, must refuse, length bounds).
- **Prompt templates with versions** in [`eval/prompt_templates.yaml`](eval/prompt_templates.yaml). Multiple versions of the same prompt can coexist and be compared.
- **Provider abstraction** with OpenAI, Anthropic, and a deterministic mock adapter, selected via `LLM_PROVIDER`. No hardcoded API keys; the mock provider lets the whole stack run without any.
- **Deterministic checks** for non-empty output, required citations, refusal-on-insufficient-context, must/must-not-include terms, and length bounds — each with a severity, each visible per result.
- **Optional LLM-as-judge** as a parallel signal at severity `info`: it is recorded with the deterministic checks but never overrides status or human review.
- **Human review** is first-class: a reviewer marks each result `pass / fail / needs review` with notes, and the underlying automatic checks remain visible.
- **Run comparison** groups test cases between two runs into Improved / Regressed / Other change / Unchanged.
- **Trends** view per prompt name@version: status strip + sparkline of pass rate over time, no chart dependencies.
- **Dataset import/export** of test cases as YAML or JSON, round-tripping with `eval/test_cases.yaml`.
- **Asynchronous runs.** `POST /runs` returns `202` immediately; the run progresses through `pending → running → completed | failed` via a FastAPI `BackgroundTasks` worker, with the UI polling while non-terminal.
- **CLI runner** for headless evaluation: `python scripts/run_eval.py --prompt name@version --all`.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic
- **Frontend:** React + TypeScript + Vite, TanStack Query, react-router-dom
- **Database:** PostgreSQL 16
- **Local orchestration:** Docker Compose
- **CI:** GitHub Actions (ruff + pytest, tsc + vitest + vite build)

## Architecture

```
React/Vite ── REST/JSON ──▶ FastAPI ──▶ Postgres
                              │
                              └──▶ LLM provider (openai | mock)
```

Detail and module map: [`docs/architecture.md`](docs/architecture.md).

## Evaluation model

Layered, in order of confidence:

1. **Deterministic checks** — heuristic but cheap and reproducible.
2. **Structured criteria** — named, severity-tagged, reviewable in YAML.
3. **Human review** — first-class, never overwritten by automation.
4. **LLM-as-judge** — explicitly *not* in this version. Future work.

Status (`pass | fail | needs_review`) is derived from check outcomes, with a human rating overriding when present. Full rules: [`docs/evaluation-design.md`](docs/evaluation-design.md), [`docs/scoring.md`](docs/scoring.md).

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Backend: <http://localhost:8000/health>
- Frontend: <http://localhost:5173>

The default config uses the **mock provider**, so no API key is needed to demo the app end-to-end. To use OpenAI:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Or Anthropic:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

On first start the backend runs `alembic upgrade head` automatically — Alembic owns the schema. **Wait for the backend to be up before seeding**, otherwise the seed script will refuse to run with a clear error. Then, from the repo root with backend deps installed in a local venv:

```bash
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt   # or .../bin/pip on macOS/Linux
```

PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://evaluser:evalpass@localhost:5432/evallab"
backend\.venv\Scripts\python scripts\seed.py
Remove-Item Env:DATABASE_URL
```

bash / zsh:

```bash
DATABASE_URL=postgresql+psycopg://evaluser:evalpass@localhost:5432/evallab \
  backend/.venv/bin/python scripts/seed.py
```

Seeding is idempotent: re-running it upserts changes. The dev Postgres credentials above are local-only and the container binds to `127.0.0.1`; change them if you deploy this anywhere.

## Example workflow

1. Open the **New run** page, pick a prompt template (e.g. `grounded-summarizer@1`), leave test cases unselected to run all, and click *Run evaluation*.
2. The runner calls the provider for each test case, stores the output, and runs the deterministic checks. You are taken to the **Run detail** page.
3. For any result that looks off, expand the question/context, read the model output, and check the per-criterion outcomes. Set a human rating and notes; submit.
4. Iterate on the prompt: edit `eval/prompt_templates.yaml`, bump the version, re-seed, and run again with `grounded-summarizer@2`.
5. Open the **Compare** page, pick the two runs, and confirm whether the new version actually improved things — and whether anything regressed.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Backend status, db connectivity, provider config |
| `GET` | `/test-cases` | List seeded test cases |
| `GET` | `/test-cases/export.yaml` | Download dataset as YAML (same shape as `eval/test_cases.yaml`) |
| `GET` | `/test-cases/export.json` | Download dataset as JSON |
| `POST` | `/test-cases/import` | Upsert test cases from a YAML or JSON upload (`multipart/form-data`, field `file`); matches by `title` |
| `GET` | `/prompt-templates` | List prompt templates (all versions) |
| `POST` | `/runs` | Queue an evaluation (returns `202` with `state=pending`); body `{prompt_template_id, test_case_ids?, model?, enable_llm_judge?}` |
| `GET` | `/runs` | List runs (newest first) |
| `GET` | `/runs/{id}` | Get a run with its results |
| `GET` | `/runs/{id}/export.json` | Download run + results as JSON |
| `GET` | `/runs/{id}/export.csv` | Download run + results as a flat CSV |
| `PATCH` | `/results/{id}/review` | Set `human_rating` and `human_notes`; recomputes status & summary |

## CLI

```bash
# Reset schema (destructive)
python scripts/reset_db.py

# Load eval/*.yaml into the DB (idempotent)
python scripts/seed.py

# Run an evaluation
LLM_PROVIDER=mock python scripts/run_eval.py --prompt grounded-summarizer@2 --all
LLM_PROVIDER=mock python scripts/run_eval.py --prompt support-reply@1 --case-ids 1 2
```

## Sample test cases

Five synthetic cases ship with the repo:

1. GDPR retention summary requiring citations.
2. Public-sector case-processing guidance summary.
3. Insufficient-context refusal scenario.
4. Length-bounded customer support reply.
5. Source-grounded Q&A that must refuse rather than invent a retention period.

Domains are deliberately bland and synthetic — no real personal data.

## Limitations

- Deterministic checks are heuristics, not ground truth.
- Sample size is small; pass rates are not benchmarks.
- Runs execute synchronously; large case sets will block the request.
- No auth, no multi-tenant, no RBAC. Local tool only.

Full list: [`docs/limitations.md`](docs/limitations.md).

## Future improvements

- A real job queue (e.g. ARQ + Redis) for restart-tolerant, multi-worker run execution.
- Dataset import/export so test cases can be shared across projects.

## Repository layout

```
backend/      FastAPI app, SQLAlchemy models, Alembic migrations, tests
frontend/     React + TS + Vite app, vitest suite
docs/         architecture, evaluation design, scoring, limitations
eval/         seed test cases, prompt templates, criteria (YAML)
scripts/      reset_db, seed, run_eval CLIs
```

## License

MIT — see [LICENSE](LICENSE).
