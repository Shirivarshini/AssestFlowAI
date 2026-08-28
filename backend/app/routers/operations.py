from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.database import get_db
from app.models import Alert, AuditLog, SourceRecord
from app.schemas import AlertOut, AlertUpdate, ControlCheckRequest, EventSimulateRequest, LifecycleEventCreate, OrchestrateRequest
from app.services import agent_service, asset_service, audit_service, control_service, event_service, risk_service

router = APIRouter(tags=["operations"])


@router.get("/assets/{asset_id}/exposure")
def get_exposure(asset_id: str, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    risk = risk_service.latest_risk(db, asset_id)
    return control_service.calculate_exposure(db, asset, risk.confidence if risk else 1.0, risk.risk_level if risk else "LOW")


@router.post("/assets/{asset_id}/duplicate-check")
def duplicate_check(asset_id: str, payload: ControlCheckRequest, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    result = control_service.detect_duplicate(db, asset, payload.instrument, payload.lender_id, payload.collateral_reference)
    audit_service.record(db, "DUPLICATE_FINANCING_CHECK", asset.id, details=result)
    if result["duplicate_detected"]:
        control_service.create_control_alert(db, asset.id, "DUPLICATE_FINANCING", result["severity"], result["reason"])
    return result


@router.post("/assets/{asset_id}/leverage-check")
def leverage_check(asset_id: str, payload: ControlCheckRequest, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    risk = risk_service.latest_risk(db, asset.id)
    result = control_service.detect_over_leverage(db, asset, payload.requested_amount, risk.confidence if risk else 1.0, risk.risk_level if risk else "LOW")
    audit_service.record(db, "OVER_LEVERAGE_CHECK", asset.id, details=result)
    if result["over_leveraged"]:
        control_service.create_control_alert(db, asset.id, "OVER_LEVERAGE", result["severity"], f"Exposure exceeds safe capacity by {result['excess_amount']}.")
    return result


@router.post("/assets/{asset_id}/orchestrate")
def orchestrate(asset_id: str, payload: OrchestrateRequest, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    result = agent_service.orchestrate(db, asset, payload.trigger)
    audit_service.record(db, "AGENT_ORCHESTRATION", asset.id, details={"trigger": payload.trigger, "action": result["decision"]["action"]})
    return result


@router.get("/assets/{asset_id}/audit")
def get_audit(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)
    return db.query(AuditLog).filter(AuditLog.asset_id == asset_id).order_by(AuditLog.created_at.desc()).all()


@router.get("/audit")
def list_audit(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(max(1, min(limit, 500))).all()


@router.get("/assets/{asset_id}/evidence")
def get_evidence(asset_id: str, db: Session = Depends(get_db)):
    asset_service.get_asset(db, asset_id)
    rows = db.query(SourceRecord).filter(SourceRecord.asset_id == asset_id).order_by(SourceRecord.received_at.desc()).all()
    return [{"id": r.id, "asset_id": r.asset_id, "source": r.source_name, "field": r.field, "value": r.value, "received_at": r.received_at, "reliability": 0.9 if r.source_name in ("ERP", "PURCHASE_ORDER", "FINANCIAL_INSTITUTION") else 0.8 if r.source_name in ("WAREHOUSE", "INVOICE", "LOGISTICS") else 0.7, "raw_payload": r.raw_payload, "data_mode": "SIMULATED"} for r in rows]


@router.get("/assets/{asset_id}/decision-history")
def decision_history(asset_id: str, db: Session = Depends(get_db)):
    from app.services import decision_service
    asset = asset_service.get_asset(db, asset_id)
    decisions = decision_service.list_decisions(db, asset_id)
    return [{"id": d.id, "timestamp": d.created_at, "trigger": d.trigger or d.decision_type, "lifecycle_stage": d.lifecycle_stage or asset.current_lifecycle_stage, "asset_value": d.asset_value if d.asset_value is not None else asset.current_estimated_value, "risk": d.risk_score, "existing_exposure": d.existing_exposure, "maximum_safe_exposure": d.maximum_safe_exposure, "recommended_amount": d.amount, "instrument": d.instrument, "action": d.recommendation, "confidence": d.confidence, "decision_factors": d.decision_factors or []} for d in decisions]


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: str, payload: AlertUpdate, db: Session = Depends(get_db)):
    if payload.status not in ("OPEN", "ACKNOWLEDGED", "RESOLVED"):
        raise ValidationError("Alert status must be OPEN, ACKNOWLEDGED or RESOLVED.")
    alert = db.get(Alert, alert_id)
    if not alert:
        from app.core.errors import NotFoundError
        raise NotFoundError(f"Alert {alert_id} not found.")
    from datetime import datetime
    alert.status = payload.status
    alert.resolved_at = datetime.utcnow() if payload.status == "RESOLVED" else None
    db.commit(); db.refresh(alert)
    audit_service.record(db, "ALERT_STATUS_CHANGED", alert.asset_id, details={"alert_id": alert.id, "status": payload.status})
    return alert


@router.post("/events/simulate")
def simulate_event(payload: EventSimulateRequest, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, payload.asset_id)
    before = agent_service.orchestrate(db, asset, "BEFORE_EVENT")
    result = event_service.process_event(db, asset.id, LifecycleEventCreate(event_type=payload.event_type, to_stage=payload.to_stage, severity=payload.severity, source_id="SIMULATOR", payload={"simulated": True}))
    db.refresh(asset)
    after = agent_service.orchestrate(db, asset, payload.event_type)
    audit_service.record(
        db, "EVENT_SIMULATED", asset.id,
        before_state={"stage": before["state_summary"]["lifecycle_stage"], "risk": before["risk"]["risk_score"], "decision": before["decision"]},
        after_state={"stage": after["state_summary"]["lifecycle_stage"], "risk": after["risk"]["risk_score"], "decision": after["decision"]},
        reason=payload.event_type, source_refs=after["state_summary"]["source_refs"], related_event_id=result["event"].id,
    )
    return {"event": result["event"], "before": before, "after": after, "alert": result["alert"]}
