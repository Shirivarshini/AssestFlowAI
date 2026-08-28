"""
Event & reassessment orchestration.

SOURCE: 12_EVENT_SYSTEM.md event flow:
Event -> validate -> update asset state -> reconcile -> reassess
value/risk -> reassess financing -> compare previous decision -> generate
action -> create alert if material -> audit.
"""
from sqlalchemy.orm import Session

from app.core.enums import EventType, AlertSeverity, DecisionType, LIFECYCLE_ORDER, LifecycleStage
from app.core.errors import ValidationError
from app.models import Asset, Alert
from app.schemas import LifecycleEventCreate
from app.services import asset_service, valuation_service, risk_service, financing_service, decision_service, audit_service

# ASSUMPTION: which events are "material" enough to raise an alert.
# SOURCE list of material events: 12_EVENT_SYSTEM.md.
MATERIAL_EVENTS = {
    EventType.PRODUCTION_DELAY,
    EventType.SHIPMENT_DELAY,
    EventType.INVENTORY_DETERIORATION,
    EventType.WAREHOUSE_EXCEPTION,
    EventType.BUYER_RISK_CHANGED,
    EventType.RECEIVABLE_DELAY,
    EventType.DATA_CONFLICT,
}

STAGE_ADVANCING_EVENTS = {
    EventType.DELIVERY_CONFIRMED: "DELIVERY",
    EventType.INVOICE_VERIFIED: "INVOICE",
    EventType.PAYMENT_RECEIVED: "CASH_REALISATION",
}


def process_event(db: Session, asset_id: str, payload: LifecycleEventCreate) -> dict:
    if payload.event_type not in EventType.__members__:
        raise ValidationError(
            f"Unknown event type '{payload.event_type}'.",
            {"allowed": [e.value for e in EventType]},
        )
    event_enum = EventType(payload.event_type)

    asset_before = asset_service.get_asset(db, asset_id)
    if event_enum == EventType.NEXT_LIFECYCLE_STAGE and payload.to_stage is None:
        current_index = LIFECYCLE_ORDER.index(LifecycleStage(asset_before.current_lifecycle_stage))
        if current_index >= len(LIFECYCLE_ORDER) - 1:
            raise ValidationError("Asset is already at CASH_REALISATION.")
        payload.to_stage = LIFECYCLE_ORDER[current_index + 1].value

    # Auto-advance lifecycle stage for confirmation-style events if the
    # caller didn't already specify a target stage. ASSUMPTION mapping.
    if payload.to_stage is None and event_enum in STAGE_ADVANCING_EVENTS:
        payload.to_stage = STAGE_ADVANCING_EVENTS[event_enum]

    event = asset_service.apply_lifecycle_event(db, asset_id, payload)
    asset = asset_service.get_asset(db, asset_id)

    # Preserve raw evidence and persist a separate canonical state snapshot.
    from app.services import reconciliation_service
    reconciliation = reconciliation_service.run_reconciliation(db, asset)

    # Reassess value & risk (12_EVENT_SYSTEM.md steps 5-6).
    recent_events = [e.event_type for e in asset_service.get_timeline(db, asset_id)[-10:]]
    condition_score = 0.6 if event_enum == EventType.INVENTORY_DETERIORATION else 1.0
    valuation = valuation_service.estimate_value(db, asset, condition_score=condition_score)
    risk = risk_service.assess_risk(db, asset, recent_event_types=recent_events)

    # Reassess financing (12_EVENT_SYSTEM.md step 6).
    evaluation = financing_service.evaluate_financing(
        db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
    )
    evaluation["risk_score"] = risk.overall_score
    evaluation["trigger"] = payload.event_type
    decision = decision_service.record_decision(db, asset, DecisionType.EVENT_REASSESSMENT.value, evaluation)

    if event_enum == EventType.PAYMENT_RECEIVED:
        for txn in financing_service.list_financing(db, asset.id):
            if txn.status in ("ACTIVE", "REDUCED"):
                financing_service.settle_financing(db, txn.id)
        evaluation = financing_service.evaluate_financing(
            db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
        )

    alert = None
    if event_enum in MATERIAL_EVENTS or evaluation["action"] in ("REDUCE_EXPOSURE", "BLOCK", "NEEDS_REVIEW"):
        severity = (
            AlertSeverity.CRITICAL.value if risk.risk_level in ("HIGH", "CRITICAL")
            else AlertSeverity.WARNING.value
        )
        alert = Alert(
            asset_id=asset.id,
            alert_type=event_enum.value,
            severity=severity,
            message=f"{event_enum.value} on asset {asset.id}: risk={risk.risk_level}, action={evaluation['action']}.",
            status="OPEN",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

    audit_service.record(
        db, "EVENT_PROCESSED", asset.id,
        details={"event_type": payload.event_type, "resulting_action": evaluation["action"]},
    )

    from app.services import agent_service
    agent_result = agent_service.orchestrate(db, asset, payload.event_type)
    return {
        "event": event,
        "valuation": valuation,
        "risk": risk,
        "financing_evaluation": evaluation,
        "decision": decision,
        "alert": alert,
        "reconciliation": reconciliation,
        "agent_result": agent_result,
    }
