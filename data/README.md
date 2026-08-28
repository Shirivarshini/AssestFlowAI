# AssetFlow AI — Member 4: Data & Integration Layer

Standalone, framework-free Python module implementing multi-source
simulation, normalization, reconciliation, and event simulation for
CSI ORIGIN 2026, Problem Statement 6.

No FastAPI, no SQLAlchemy, no React, no LLM SDK, no API keys, no
external services. Frontend, backend, and AI modules (Members 1–3)
have not been built yet — this module is a clean standalone boundary
they can integrate against later.

## Install / run

```bash
cd assetflow-data
pip install black mypy   # optional, for formatting/type-checking
python3 -m unittest discover -s tests -v
```

No other dependencies are required to run the module itself.

## Quick start

```python
from data import get_demo_scenario

scenario = get_demo_scenario("conflicting_sources")
state = scenario["reconciled_state"]

print(state.status)             # "OK" or "NEEDS_REVIEW"
print(state.state_confidence)   # overall confidence, 0-1
for conflict in state.conflicts:
    print(conflict.field, conflict.resolution_status, conflict.canonical_value)
```

## Public interface

```
load_source_records(scenario="healthy", sources=None) -> List[SourceRecord]
normalize_records(source_records)                     -> List[NormalizedRecord]
map_records(records)                                   -> Dict[asset_id, Dict[field, List[NormalizedRecord]]]
detect_conflicts(asset_fields)                         -> Dict[field, dict]
resolve_asset_fields(asset_id, asset_fields)            -> List[DataConflict]
get_provenance_for_asset(conflicts)                     -> List[FieldProvenance]
reconcile_asset(asset_id, scenario="healthy")           -> CanonicalAssetState
reconcile_all_assets(scenario="healthy")                -> Dict[asset_id, CanonicalAssetState]
create_event(asset_id, event_type, ...)                 -> LifecycleEvent
get_demo_scenario(name)                                 -> dict bundle
list_demo_scenarios()                                   -> List[str]
```

All return values are plain dataclasses (each with a `.to_dict()` that
is JSON-serializable) — no ORM objects, no framework types.

## Pipeline

```
raw source records (7 simulated connectors)
  -> normalize      (data/normalizer.py)
  -> map to asset    (data/mapper.py)
  -> detect conflicts (data/conflict_detector.py)
  -> resolve/qualify  (data/resolver.py)        <- PROTOTYPE POLICY, documented inline
  -> provenance       (data/provenance.py)
  -> canonical state  (data/reconciliation.py)
```

## Simulated sources

ERP, Purchase Orders, Invoices, Logistics, Warehouse, Telemetry,
Financing — all keyed to demo asset `AST-1001`. Each source module
exposes `get_records(scenario=...)`; the `scenario` argument selects
between deterministic dataset variants used by the demo fixtures.

## Conflict resolution policy (prototype, not an official rule)

1. No usable value anywhere → `NEEDS_REVIEW`, confidence 0.0
2. Only one source reports the field → `NO_CONFLICT`, confidence 0.95
3. All sources agree → `NO_CONFLICT`, confidence 0.95
4. Strict majority agrees → `RESOLVED` with the majority value, confidence 0.80
5. No majority → `QUALIFIED` using the most reliable source
   (reliability order: ERP > WAREHOUSE > PURCHASE_ORDER > INVOICE >
   FINANCING > LOGISTICS > TELEMETRY), confidence 0.55

Full rationale and code lives in `data/resolver.py`. This policy is
explicitly **not** claimed as an official CSI ORIGIN 2026 requirement
— the problem statement leaves the resolution formula as an
implementation decision (see `16_SOURCE_INDEX.md`).

## Event simulator

`create_event()` supports exactly the 9 documented event types
(`PRODUCTION_DELAY`, `SHIPMENT_DELAY`, `INVENTORY_DETERIORATION`,
`WAREHOUSE_EXCEPTION`, `DELIVERY_CONFIRMED`, `BUYER_RISK_CHANGED`,
`RECEIVABLE_DELAY`, `INVOICE_VERIFIED`, `DATA_CONFLICT`). It only
packages a structured `LifecycleEvent` — it never computes risk or
financing impact. It rejects backward/no-op lifecycle transitions
unless `payload={"allow_reversal": True}` is passed explicitly.

## Demo scenarios (`data/fixtures/demo_scenarios.py`)

| Name | Maps to |
|---|---|
| `healthy_lifecycle` | 15_DEMO_SCENARIOS.md Scenario 1 |
| `shipment_delay` | 15_DEMO_SCENARIOS.md Scenario 2 |
| `duplicate_financing` | 15_DEMO_SCENARIOS.md Scenario 3 |
| `conflicting_sources` | 15_DEMO_SCENARIOS.md Scenario 4 |

Each returns a dict with `reconciled_state`, `events`,
`lifecycle_transitions`, and `expected_notes` (plain-text pointers to
what the risk/financing engines are expected to do downstream — this
module does not compute those outcomes).

## Future integration contract (for Members 1–3)

- **Backend (Member 2):** call `reconcile_asset(asset_id)` /
  `reconcile_all_assets()` to populate `asset_states` /
  `data_conflicts` tables per `05_DATABASE_SCHEMA.md`; call
  `create_event(...)` from your event endpoint
  (`POST /api/v1/assets/{asset_id}/events`) and pass the result into
  your reassessment pipeline (`12_EVENT_SYSTEM.md`).
- **AI/Decision (Member 3):** `CanonicalAssetState.field_values`,
  `.conflicts`, and `.provenance` are the structured inputs your
  Reconciliation Agent should explain; `.state_confidence` and any
  `NEEDS_REVIEW` conflicts should feed your risk engine's "low
  confidence reduces capacity" safety principle (`08_RISK_ENGINE.md`).
- **Frontend (Member 1):** every dataclass here has `.to_dict()` for
  direct JSON use once the backend wraps these calls in FastAPI
  endpoints matching `04_API_CONTRACT.md`.

## Assumptions made (documented, not official requirements)

1. Demo asset ID is `AST-1001` (not specified by the problem statement).
2. Every payload key from a raw source record becomes its own
   normalized field observation (generic, source-agnostic normalizer).
3. `physical_state` / `financial_state` / `contractual_state` are
   represented as dicts of relevant resolved fields, not single
   strings — `05_DATABASE_SCHEMA.md` doesn't specify their shape.
4. Conflict resolution policy (majority vote, then reliability
   ranking) and overall confidence (mean of per-field confidences) are
   prototype policies — clearly labeled in code and docs.
5. Numeric field comparisons use a 0.1% relative tolerance so e.g.
   `1000` vs `1000.0` isn't a false conflict.
6. Default event severities are an implementation default and can be
   overridden per call.

## Tests

47 unit tests, all deterministic, covering: source loading,
normalization, asset mapping, conflict detection, conflict resolution,
confidence scoring, provenance, full reconciliation, event generation
(including invalid event types and invalid transitions), and all four
demo scenarios.

```
Ran 47 tests in 0.010s
OK
```
