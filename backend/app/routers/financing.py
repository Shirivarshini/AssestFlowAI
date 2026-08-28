from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.enums import DecisionType
from app.schemas import (
    FinancingEvaluateRequest, FinancingEvaluateResponse, FinancingTransactionOut, FinancingTransitionRequest,
)
from app.services import asset_service, risk_service, valuation_service, financing_service, decision_service

router = APIRouter(tags=["financing"])


@router.get("/assets/{asset_id}/financing", response_model=list[FinancingTransactionOut])
def get_asset_financing(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)  # 404 if missing
    return financing_service.list_financing(db, asset_id)


@router.get("/assets/{asset_id}/financing/evaluation", response_model=FinancingEvaluateResponse)
def get_financing_evaluation(asset_id: str, db: Session = Depends(get_db)):
    """Calculate the current recommendation without recording a new decision."""
    asset = asset_service.get_asset(db, asset_id)
    if not asset.current_estimated_value:
        valuation_service.estimate_value(db, asset)
    risk = risk_service.latest_risk(db, asset.id)
    if risk is None:
        risk = risk_service.assess_risk(db, asset)
    return financing_service.evaluate_financing(
        db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
    )


@router.post("/financing/evaluate", response_model=FinancingEvaluateResponse)
def evaluate_financing(payload: FinancingEvaluateRequest, db: Session = Depends(get_db)):
    """SOURCE: 04_API_CONTRACT.md — exact request/response shape for
    POST /financing/evaluate, including the worked example."""
    asset = asset_service.get_asset(db, payload.asset_id)

    if not asset.current_estimated_value:
        valuation_service.estimate_value(db, asset)

    risk = risk_service.latest_risk(db, asset.id)
    if risk is None:
        risk = risk_service.assess_risk(db, asset)

    evaluation = financing_service.evaluate_financing(
        db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
    )
    evaluation["risk_score"] = risk.overall_score
    evaluation["trigger"] = payload.reason
    decision_service.record_decision(db, asset, DecisionType.FINANCING_EVALUATION.value, evaluation)
    return evaluation


@router.post("/financing/{financing_id}/transition", response_model=FinancingTransactionOut)
def transition_financing(financing_id: str, payload: FinancingTransitionRequest, db: Session = Depends(get_db)):
    return financing_service.transition_financing(
        db, financing_id, payload.new_instrument, payload.new_status, payload.reason,
    )
