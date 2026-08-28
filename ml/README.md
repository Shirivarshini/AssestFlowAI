# Finance AI — Member 3 MVP

This is the standalone AI + Finance module for the supply-chain financing hackathon.

## What it does

A physical asset moves through:

Purchase Order → Raw Material → Production → Finished Goods → Shipment → Warehouse → Delivery → Invoice → Payment

This module takes the current asset state and answers:

1. What is the asset worth now?
2. What is the risk?
3. Is financing needed?
4. Which financing instrument fits the current stage?
5. How much additional financing is safe?
6. Should financing be approved, limited, paused, reviewed or refused?

## Member 3 scope

- Feature 5 — Asset Value + Risk Engine
- Feature 6 — Financing Need Calculator
- Feature 7 — Financing Instrument Selector
- Feature 8 — Dynamic Financing Amount Calculator

The LLM is used only for explanation. All financial numbers are calculated deterministically.

## Architecture

Asset State
→ Value Engine
→ Risk Engine
→ Financing Need
→ Instrument Selector
→ Dynamic Financing Amount
→ Decision Engine
→ Optional AI Explanation

## Prototype formulas

### Asset value

`asset_value = purchase_value × lifecycle_stage_factor`

Stage factors are intentionally simple hackathon policies.

### Risk

`risk_score = buyer×20% + production×20% + shipment×25% + asset×20% + data×15%`

`data_risk = 100 - (data_confidence × 100)`

Shipment delays, damaged condition and low data confidence can raise the risk.

### Financing need

`financing_need = max(required_capital - existing_financing, 0)`

### Maximum safe financing

`maximum_safe_financing = asset_value × 70% × risk_factor × data_confidence`

Risk factors:

- LOW = 1.00
- MEDIUM = 0.80
- HIGH = 0.70

### Exposure protection

`available_financing = max(maximum_safe_financing - existing_financing, 0)`

`recommended_amount = min(financing_need, available_financing, maximum_safe_financing)`

If existing financing is already at or above the safe limit, recommended additional financing is zero.

## Run

From the project root:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Test

```bash
pytest backend/tests/test_finance.py -v
```

## API

### Health

`GET /health`

### Mock asset

`GET /api/finance/mock`

### Evaluate

`POST /api/finance/evaluate`

Send the JSON from:

`backend/data/mock_asset.json`

## Demo scenarios

### 1. Normal

Set:

```json
"shipment_status": "ON_TIME",
"data_confidence": 0.95
```

Expected: lower risk and financing may be available.

### 2. Shipment delay

Set:

```json
"shipment_status": "DELAYED"
```

Expected: risk increases and the safe financing limit falls.

### 3. Data conflict

Set:

```json
"data_confidence": 0.40
```

Expected: `NEEDS_REVIEW`.

### 4. Over-leverage

Set:

```json
"existing_financing": 50000000
```

Expected:

```text
recommended_amount = 0
action = DO_NOT_FINANCE
```

### 5. Payment

Set:

```json
"stage": "PAYMENT"
```

Expected:

```text
instrument = NONE
asset_value = 0
```

## AI explanation

Set `ANTHROPIC_API_KEY` if you want live Claude explanations.

The app still works without an API key because it uses a deterministic fallback explanation.

## Integration with Members 1 and 2

Do not rewrite the finance engine when their modules are ready.

They only need to map their final asset/data output into the `AssetState` request shape and call:

`POST /api/finance/evaluate`

The response is the `FinancingDecision` object.

This lets Features 1-4 feed this engine, while Features 9-10 can trigger another evaluation whenever an event changes the asset state.

## Important

The valuation factors, risk weights and financing formula are prototype/hackathon policies. They are not a real lending or credit underwriting model.
