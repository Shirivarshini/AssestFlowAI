from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.core.errors import register_error_handlers
from app.routers import assets, financing, risk, reconciliation, decisions, alerts, dashboard, operations

# Import models so they're registered on Base before create_all.
from app import models  # noqa: F401

app = FastAPI(title="AssetFlow AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.on_event("startup")
def on_startup():
    # Hackathon-simple table creation (no migration framework required for
    # MVP, per 02_PROJECT_SPEC.md hackathon principle). ASSUMPTION:
    # acceptable for a hackathon prototype; a real deployment would use
    # Alembic migrations. Deferred to startup (rather than import time) so
    # the test suite can point `app.database.engine` at SQLite before the
    # app starts, without the production default (Postgres) ever being
    # touched during import.
    Base.metadata.create_all(bind=engine)


app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(assets.router, prefix=settings.API_PREFIX)
app.include_router(financing.router, prefix=settings.API_PREFIX)
app.include_router(risk.router, prefix=settings.API_PREFIX)
app.include_router(reconciliation.router, prefix=settings.API_PREFIX)
app.include_router(decisions.router, prefix=settings.API_PREFIX)
app.include_router(alerts.router, prefix=settings.API_PREFIX)
app.include_router(operations.router, prefix=settings.API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
