"""
Test configuration.

Points the application's own DATABASE_URL at a throwaway file-based
SQLite database *before* app.main is imported, purely as a fast,
dependency-free test double for CI (see the documented assumption in
app/config.py's docstring). Production/dev still default to PostgreSQL —
this only affects the test process's environment.
"""
import os
import pathlib

TEST_DB_PATH = pathlib.Path(__file__).parent / "test_assetflow.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal, get_db
from app.main import app


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
