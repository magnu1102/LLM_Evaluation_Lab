from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import exports, health, prompt_templates, results, runs, test_cases


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Evaluation Lab", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(test_cases.router)
    app.include_router(prompt_templates.router)
    app.include_router(runs.router)
    app.include_router(exports.router)
    app.include_router(results.router)
    return app


app = create_app()
