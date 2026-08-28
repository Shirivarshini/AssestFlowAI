from sqlalchemy.orm import Session

from app.core.enums import DecisionType
from app.core.errors import NotFoundError, ValidationError
from app.models import AIDecision, Asset
from app.services import audit_service


def record_decision(db: Session, asset: Asset, decision_type: str, evaluation: dict) -> AIDecision:
    """SOURCE: 10_AI_AGENTS.md agent contract — "Agents should consume
    structured JSON and return structured JSON." This persists the
    deterministic engine's structured output as an auditable ai_decisions
    row; Member 3 layers natural-language explanation on top of this."""
    decision = AIDecision(
        asset_id=asset.id,
        decision_type=decision_type,
        recommendation=evaluation["action"],
        amount=evaluation.get("recommended_amount"),
        instrument=evaluation.get("recommended_instrument"),
        confidence=evaluation.get("confidence"),
        decision_factors=evaluation.get("decision_factors", []),
        trigger=evaluation.get("trigger", decision_type),
        lifecycle_stage=asset.current_lifecycle_stage,
        asset_value=asset.current_estimated_value,
        risk_score=evaluation.get("risk_score"),
        existing_exposure=evaluation.get("existing_exposure"),
        maximum_safe_exposure=evaluation.get("maximum_safe_amount"),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def list_decisions(db: Session, asset_id: str) -> list[AIDecision]:
    return (
        db.query(AIDecision)
        .filter(AIDecision.asset_id == asset_id)
        .order_by(AIDecision.created_at.desc())
        .all()
    )


def execute_decision(db: Session, decision_id: str) -> AIDecision:
    """SOURCE: 04_API_CONTRACT.md POST /decisions/{decision_id}/execute.
    ASSUMPTION: "executing" a decision here means committing it against
    the financing engine (open/transition financing) and flagging it
    executed=1 for audit purposes; a NEEDS_REVIEW decision cannot be
    auto-executed."""
    decision = db.get(AIDecision, decision_id)
    if not decision:
        raise NotFoundError(f"Decision {decision_id} not found.", {"decision_id": decision_id})
    if decision.recommendation == "NEEDS_REVIEW":
        raise ValidationError("A NEEDS_REVIEW decision requires human review and cannot be auto-executed.")

    from app.services import financing_service  # local import avoids circular import

    asset = db.get(Asset, decision.asset_id)
    if decision.recommendation in ("MAINTAIN", "INCREASE", "TRANSITION") and decision.instrument and decision.amount:
        financing_service.open_or_update_financing(db, asset, decision.instrument, decision.amount)
    elif decision.recommendation == "SETTLE":
        active = [t for t in financing_service.list_financing(db, asset.id) if t.status == "ACTIVE"]
        for t in active:
            financing_service.settle_financing(db, t.id)

    decision.executed = 1
    db.commit()
    db.refresh(decision)

    audit_service.record(db, "DECISION_EXECUTED", asset.id, details={"decision_id": decision_id}, related_decision_id=decision_id)
    return decision
