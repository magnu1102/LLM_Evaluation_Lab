"""Run an evaluation from the CLI.

Usage:
  python scripts/run_eval.py --prompt grounded-summarizer@2 --provider mock --all
  python scripts/run_eval.py --prompt support-reply@1 --provider mock --case-ids 1 2
"""
from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from sqlalchemy import select

from app.db import SessionLocal
from app.evaluation.runner import execute_run
from app.models import PromptTemplate, TestCase
from app.providers import get_provider


def parse_prompt_ref(ref: str) -> tuple[str, int]:
    if "@" not in ref:
        raise SystemExit("--prompt must be in the form name@version, e.g. support-reply@1")
    name, version_str = ref.rsplit("@", 1)
    return name, int(version_str)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="prompt template ref, e.g. name@version")
    ap.add_argument("--provider", default=None, help="override LLM_PROVIDER env (mock|openai)")
    ap.add_argument("--model", default=None, help="override the provider's default model")
    ap.add_argument("--case-ids", nargs="*", type=int, help="specific test case ids")
    ap.add_argument("--all", action="store_true", help="run all test cases")
    ap.add_argument(
        "--judge",
        action="store_true",
        help="also run LLM-as-judge per test case (extra model call)",
    )
    args = ap.parse_args()

    if not args.all and not args.case_ids:
        raise SystemExit("provide --all or --case-ids")

    name, version = parse_prompt_ref(args.prompt)
    with SessionLocal() as session:
        prompt = session.scalar(
            select(PromptTemplate).where(
                PromptTemplate.name == name, PromptTemplate.version == version
            )
        )
        if not prompt:
            raise SystemExit(f"prompt template not found: {name}@{version}")

        if args.case_ids:
            cases = list(
                session.scalars(select(TestCase).where(TestCase.id.in_(args.case_ids))).all()
            )
        else:
            cases = list(session.scalars(select(TestCase).order_by(TestCase.id)).all())
        if not cases:
            raise SystemExit("no test cases found")

        provider = get_provider(args.provider)
        run = execute_run(
            session, prompt, cases, provider, model=args.model, enable_llm_judge=args.judge
        )

        run_id = run.id
        provider_name = run.provider
        model_used = run.model
        summary = dict(run.summary)
        result_rows = [
            (r.test_case_id, r.status, len(r.automatic_checks)) for r in run.results
        ]
        prompt_label = f"{prompt.name}@{prompt.version}"

    print(f"Run #{run_id}: {prompt_label} via {provider_name}/{model_used}")
    print(f"  summary: {summary}")
    for tc_id, status, n_checks in result_rows:
        print(f"  - case {tc_id}: {status}  ({n_checks} checks)")


if __name__ == "__main__":
    main()
