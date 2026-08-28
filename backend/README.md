# AssetFlow AI — Backend (Member 2)

Backend for CSI ORIGIN 2026 Problem Statement 6, implementing
`03_ARCHITECTURE.md`'s stack (FastAPI + Pydantic + SQLAlchemy + PostgreSQL)
and the API/database contracts in `04_API_CONTRACT.md` / `05_DATABASE_SCHEMA.md`.

## Install

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run with Docker (recommended — matches 03_ARCHITECTURE.md exactly)

```bash
docker compose up --build
```

API available at `http://localhost:8000/api/v1`, docs at `http://localhost:8000/docs`.

## Run locally against Postgres

Start Postgres yourself (or `docker compose up db`), set `DATABASE_URL`
in `.env`, then:

```bash
uvicorn app.main:app --reload
```

## Seed demo data

```bash
python -m app.seed
```

Creates one demo asset with conflicting simulated source records and an
initial financing evaluation, matching `15_DEMO_SCENARIOS.md`.

## Run tests

```bash
pytest -v
```

Tests use an in-memory SQLite database purely as a fast test double (see
`app/config.py` docstring) — the running application still defaults to
PostgreSQL.

## Example demo API calls

```bash
# Create an asset
curl -X POST localhost:8000/api/v1/assets -H "Content-Type: application/json" -d '{
  "product_name": "Cotton Yarn", "quantity": 5000, "unit": "KG",
  "current_lifecycle_stage": "SHIPMENT", "current_estimated_value": 2500000
}'

# Evaluate financing
curl -X POST localhost:8000/api/v1/financing/evaluate -H "Content-Type: application/json" \
  -d '{"asset_id": "AST-XXXXXXXXXX", "reason": "LIFECYCLE_CHANGE"}'

# Trigger a shipment delay event (Scenario 2)
curl -X POST localhost:8000/api/v1/assets/AST-XXXXXXXXXX/events -H "Content-Type: application/json" \
  -d '{"event_type": "SHIPMENT_DELAY", "severity": "MEDIUM"}'

# Dashboard
curl localhost:8000/api/v1/dashboard
```

## Assumptions made (see inline `ASSUMPTION` comments in code for detail)

- Financing formula weights (advance rate, risk factors) — `07_FINANCING_ENGINE.md`
  explicitly says no formula is mandated; the suggested prototype policy is used verbatim.
- Risk component weights — `08_RISK_ENGINE.md` specifies dimensions/output shape only.
- Valuation policy — `08_RISK_ENGINE.md` lists inputs only, no formula.
- `FinancingStatus`, `DecisionAction`, `AlertSeverity/Status`, `ConflictResolutionStatus`,
  `EventSeverity`, `DecisionType` enums — smallest sets needed to cover the required behavior.
- `PAYMENT_RECEIVED` event — added (also referenced in the Member-2 instructions doc)
  to close the settlement loop; not present in `12_EVENT_SYSTEM.md`'s list.
- Lifecycle transition validation allows forward-by-one or backward-by-one
  (as an explicit correction/reversal); larger jumps are rejected.
- "Financing opportunities" on the dashboard = assets with no currently active financing.
- Table creation via `Base.metadata.create_all` instead of Alembic migrations, for hackathon speed.

## Integration points

- **Member 1 (Frontend):** consumes only the documented `/api/v1/*` JSON responses;
  errors always follow the `{"error": {code, message, details}}` shape.
- **Member 3 (AI/Decision):** should call the service functions in `app/services/`
  (e.g. `financing_service.evaluate_financing`, `risk_service.assess_risk`) or the
  `/financing/evaluate`, `/risk/reassess`, `/assets/{id}/decisions` endpoints — never
  touch the DB directly. All numeric policy is deterministic; AI only explains/orchestrates.
- **Member 4 (Data/Integration):** writes rows into `source_records` (any DB session/future
  ingestion endpoint) and posts to `/assets/{asset_id}/events` for detected events; then
  calls `/reconciliation/run` to get canonical state + conflicts.

## Features 11–30 operational API

The original `/api/v1` contract remains intact. Additive endpoints provide
the extended deterministic controls and judge-facing traceability flows:

```text
GET   /api/v1/assets/{asset_id}/exposure
POST  /api/v1/assets/{asset_id}/duplicate-check
POST  /api/v1/assets/{asset_id}/leverage-check
POST  /api/v1/assets/{asset_id}/orchestrate
GET   /api/v1/assets/{asset_id}/evidence
GET   /api/v1/assets/{asset_id}/audit
GET   /api/v1/assets/{asset_id}/decision-history
GET   /api/v1/audit
PATCH /api/v1/alerts/{alert_id}
POST  /api/v1/events/simulate
```

The orchestrator and explanation generator require no external AI key. Core
risk, value, exposure and financing figures remain deterministic. Every
explanation is concise decision evidence, never hidden reasoning or a lending
approval.

For an existing PostgreSQL volume created before Features 11–30, apply the
additive migration before starting the upgraded backend:

```powershell
Get-Content migrations/001_features_11_30.sql | docker compose exec -T db psql -U assetflow -d assetflow
```

New databases receive the same columns through SQLAlchemy `create_all`.
