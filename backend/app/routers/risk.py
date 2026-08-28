from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.enums import DecisionType
from app.core.errors import NotFoundError
from app.schemas import RiskAssessmentOut, RiskReassessRequest
from app.services import asset_service, risk_service, valuation_service, financing_service, decision_service

router = APIRouter(tags=["risk"])


def _to_out(risk) -> RiskAssessmentOut:
    return RiskAssessmentOut(
        overall_score=risk.overall_score,
        risk_level=risk.risk_level,
        components={
            "asset_risk": risk.asset_risk,
            "buyer_risk": risk.buyer_risk,
            "logistics_risk": risk.logistics_risk,
            "liquidity_risk": risk.liquidity_risk,
        },
        confidence=risk.confidence,
        triggers=risk.triggers or [],
    )


@router.get("/assets/{asset_id}/risk", response_model=RiskAssessmentOut)
def get_risk(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)  # 404 if missing
    risk = risk_service.latest_risk(db, asset_id)
    if risk is None:
        raise NotFoundError(f"No risk assessment exists yet for asset {asset_id}.", {"asset_id": asset_id})
    return _to_out(risk)


@router.post("/risk/reassess", response_model=RiskAssessmentOut)
def reassess_risk(payload: RiskReassessRequest, db: Session = Depends(get_db)):
    """SOURCE: 06_ASSET_LIFECYCLE.md "Event-triggered reassessment" /
    04_API_CONTRACT.md POST /risk/reassess. Also re-runs the financing
    evaluation so a manual reassessment behaves like the event-driven one."""
    asset = asset_service.get_asset(db, payload.asset_id)
    recent_events = [e.event_type for e in asset_service.get_timeline(db, asset.id)[-10:]]
    risk = risk_service.assess_risk(db, asset, recent_event_types=recent_events)

    evaluation = financing_service.evaluate_financing(
        db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
    )
    evaluation["risk_score"] = risk.overall_score
    evaluation["trigger"] = payload.reason or "MANUAL"
    decision_service.record_decision(db, asset, DecisionType.RISK_REASSESSMENT.value, evaluation)
    return _to_out(risk)
