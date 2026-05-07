"""Shared test fixtures.

Tests run against a fresh in-memory SQLite per test, with the app's engine
and SessionLocal swapped out so routes and the runner see the same DB.
"""
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  register models on Base
from app import db as app_db
from app.db import Base
from app.main import app


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    original_engine = app_db.engine
    original_factory = app_db.SessionLocal
    app_db.engine = engine
    app_db.SessionLocal = TestSession

    try:
        with TestSession() as s:
            yield s
    finally:
        app_db.engine = original_engine
        app_db.SessionLocal = original_factory


@pytest.fixture()
def client(session: Session) -> TestClient:  # noqa: ARG001  ensures app_db patched
    return TestClient(app)
