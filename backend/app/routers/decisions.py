from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DecisionOut
from app.services import asset_service, decision_service

router = APIRouter(tags=["decisions"])


@router.get("/assets/{asset_id}/decisions", response_model=list[DecisionOut])
def get_decisions(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)  # 404 if missing
    return decision_service.list_decisions(db, asset_id)


@router.post("/decisions/{decision_id}/execute", response_model=DecisionOut)
def execute_decision(decision_id: str, db: Session = Depends(get_db)):
    return decision_service.execute_decision(db, decision_id)
