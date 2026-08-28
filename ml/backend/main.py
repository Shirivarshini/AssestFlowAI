"""FastAPI entry point for Member 3's finance engine."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.finance.decision_engine import evaluate_financing
from backend.finance.explanation import generate_explanation
from backend.finance.schemas import AssetState, FinancingDecision

app = FastAPI(
    title="Supply Chain Finance AI — Member 3",
    description="Features 5-8: value, risk, financing need, instrument and dynamic amount.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/finance/mock", response_model=AssetState)
def get_mock_asset():
    path = Path(__file__).parent / "data" / "mock_asset.json"
    try:
        return AssetState(**json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Mock asset could not be loaded: {exc}")


@app.post("/api/finance/evaluate", response_model=FinancingDecision)
def evaluate(asset: AssetState):
    decision = evaluate_financing(asset)
    decision["explanation"] = generate_explanation(decision)
    return decision


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
