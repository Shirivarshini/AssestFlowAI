"""Structured, deterministic agent orchestration with no required LLM."""
from sqlalchemy.orm import Session

from app.models import Asset, AssetState, SourceRecord
from app.services import control_service, financing_service, reconciliation_service, risk_service


def orchestrate(db: Session, asset: Asset, trigger: str = "MANUAL") -> dict:
    state = db.query(AssetState).filter(AssetState.asset_id == asset.id).order_by(AssetState.effective_at.desc()).first()
    risk = risk_service.latest_risk(db, asset.id) or risk_service.assess_risk(db, asset)
    exposure = control_service.calculate_exposure(db, asset, risk.confidence, risk.risk_level)
    financing = financing_service.evaluate_financing(db, asset, risk.overall_score, risk.risk_level, risk.confidence)
    duplicate = control_service.detect_duplicate(db, asset, financing.get("recommended_instrument"))
    leverage = control_service.detect_over_leverage(db, asset, financing["recommended_amount"], risk.confidence, risk.risk_level)
    if duplicate["recommended_action"] == "BLOCK" or leverage["action"] == "BLOCK":
        financing["recommended_amount"] = 0.0; financing["action"] = "BLOCK"
    elif duplicate["duplicate_detected"] or leverage["over_leveraged"]:
        financing["action"] = "NEEDS_REVIEW"
        financing["recommended_amount"] = min(financing["recommended_amount"], exposure["available_safe_capacity"])
    factors = list(financing["decision_factors"])
    if duplicate["duplicate_detected"]: factors.append(duplicate["reason"])
    if leverage["over_leveraged"]: factors.append(f"Requested exposure exceeds safe capacity by {leverage['excess_amount']}")
    financing["decision_factors"] = factors
    source_refs = [r.id for r in db.query(SourceRecord).filter(SourceRecord.asset_id == asset.id).all()]
    state_summary = {
        "asset_id": asset.id, "lifecycle_stage": asset.current_lifecycle_stage,
        "physical_state": state.physical_state if state and state.physical_state else "UNKNOWN",
        "financial_state": state.financial_state if state and state.financial_state else exposure,
        "contractual_state": state.contractual_state if state and state.contractual_state else "INSUFFICIENT_DATA",
        "state_confidence": state.state_confidence if state and state.state_confidence is not None else risk.confidence,
        "material_changes": [trigger] if trigger != "MANUAL" else [], "source_refs": source_refs,
    }
    explanation = explain(trigger, financing, exposure, duplicate, leverage, risk.overall_score)
    conflicts = reconciliation_service.list_conflicts(db, asset.id)
    reconciliation = {
        "conflicts_found": len(conflicts),
        "canonical_state": {
            "physical_state": state.physical_state if state else "UNKNOWN",
            "financial_state": state.financial_state if state else "UNKNOWN",
            "contractual_state": state.contractual_state if state else "UNKNOWN",
        },
        "confidence": state_summary["state_confidence"],
        "conflicts": [{"field": c.field, "sources": [c.source_a, c.source_b], "values": [c.value_a, c.value_b], "canonical_value": c.value_a, "status": c.resolution_status, "reason": c.resolution_reason} for c in conflicts],
        "source_refs": source_refs,
        "explanation": f"{len(conflicts)} preserved source conflict(s); canonical values use the deterministic reliability policy.",
    }
    return {
        "asset_id": asset.id, "trigger": trigger, "state_summary": state_summary,
        "reconciliation": reconciliation,
        "risk": {"risk_score": risk.overall_score, "risk_level": risk.risk_level, "triggers": risk.triggers or [], "confidence": risk.confidence, "recommended_next_step": financing["action"]},
        "financing": {**financing, "existing_exposure": exposure["total_outstanding"], "available_capacity": exposure["available_safe_capacity"], "eligible_instruments": [financing["recommended_instrument"]] if financing["recommended_instrument"] else []},
        "duplicate_check": duplicate, "leverage_check": leverage,
        "decision": {"action": financing["action"], "amount": financing["recommended_amount"], "instrument": financing["recommended_instrument"], "confidence": financing["confidence"], "factors": factors},
        "explanation": explanation,
    }


def explain(trigger: str, financing: dict, exposure: dict, duplicate: dict, leverage: dict, risk_score: float) -> dict:
    blockers = []
    if duplicate["duplicate_detected"]: blockers.append(duplicate["reason"])
    if leverage["over_leveraged"]: blockers.append(f"Exposure exceeds the deterministic safe limit by {leverage['excess_amount']}")
    return {
        "mode": "DETERMINISTIC_TEMPLATE", "action": financing["action"],
        "summary": f"{financing['action']} {financing.get('recommended_instrument') or 'financing'} after {trigger}; risk is {risk_score}/100.",
        "existing_exposure": exposure["total_outstanding"], "available_capacity": exposure["available_safe_capacity"],
        "key_factors": financing["decision_factors"], "blocking_conditions": blockers,
        "disclaimer": "Prototype decision support only; this is not a lending approval.",
    }
