from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReconciliationRunRequest, ConflictOut
from app.services import asset_service, reconciliation_service

router = APIRouter(tags=["reconciliation"])


@router.post("/reconciliation/run")
def run_reconciliation(payload: ReconciliationRunRequest, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, payload.asset_id)
    result = reconciliation_service.run_reconciliation(db, asset)
    return {
        "asset_id": result["asset_id"],
        "canonical_state": result["canonical_state"],
        "confidence": result["confidence"],
        "conflicts": [ConflictOut.model_validate(c) for c in result["conflicts"]],
    }


@router.get("/assets/{asset_id}/conflicts", response_model=list[ConflictOut])
def get_conflicts(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)  # 404 if missing
    return reconciliation_service.list_conflicts(db, asset_id)
