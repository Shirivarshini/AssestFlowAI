"""
Configuration.

Source: 03_ARCHITECTURE.md specifies PostgreSQL + FastAPI + SQLAlchemy.
DATABASE_URL defaults to the docker-compose Postgres instance. This must
NOT be silently swapped for SQLite in the running application (per
14_AI_CODING_RULES.md "do not silently change database semantics").

The only exception is the pytest test-suite (see tests/conftest.py), which
uses an in-memory SQLite database purely for fast, dependency-free CI runs.
That is a testing convenience, not a change to the application's declared
architecture, and is documented here explicitly as an implementation
assumption.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://assetflow:assetflow@localhost:5432/assetflow",
    )
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


settings = Settings()
