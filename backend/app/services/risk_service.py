"""
Risk service.

SOURCE: 08_RISK_ENGINE.md defines the risk dimensions, the risk triggers,
and the required output shape (overall_score, risk_level, components,
confidence, triggers). No formula/weights are prescribed, so the weights
below are an explicit ASSUMPTION and must stay deterministic
(14_AI_CODING_RULES.md rule 10 / GPT-instructions "Do NOT use an LLM for
critical numerical financial calculations").
"""
from sqlalchemy.orm import Session

from app.core.enums import EventType, RiskLevel
from app.models import Asset, AssetLifecycleEvent, RiskAssessment, DataConflict

# ASSUMPTION: which recent event types bump which risk component, and by
# how much (0-100 scale per 04_API_CONTRACT.md "Risk scores use 0-100").
EVENT_RISK_IMPACT = {
    EventType.PRODUCTION_DELAY: ("asset_risk", 15),
    EventType.SHIPMENT_DELAY: ("logistics_risk", 20),
    EventType.INVENTORY_DETERIORATION: ("asset_risk", 25),
    EventType.WAREHOUSE_EXCEPTION: ("logistics_risk", 15),
    EventType.BUYER_RISK_CHANGED: ("buyer_risk", 25),
    EventType.RECEIVABLE_DELAY: ("liquidity_risk", 20),
    EventType.DATA_CONFLICT: ("asset_risk", 10),
}

BASE_RISK = 20.0  # ASSUMPTION: baseline component risk with no adverse signals


def _level_from_score(score: float) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def assess_risk(db: Session, asset: Asset, recent_event_types: list[str] | None = None) -> RiskAssessment:
    recent_event_types = recent_event_types or []

    components = {
        "asset_risk": BASE_RISK,
        "buyer_risk": BASE_RISK,
        "logistics_risk": BASE_RISK,
        "liquidity_risk": BASE_RISK,
    }
    triggers: list[str] = []

    for et in recent_event_types:
        try:
            event_enum = EventType(et)
        except ValueError:
            continue
        impact = EVENT_RISK_IMPACT.get(event_enum)
        if impact:
            key, amount = impact
            components[key] = min(100.0, components[key] + amount)
            triggers.append(et)

    # Unresolved conflicts reduce confidence and raise asset risk.
    # SOURCE: 08_RISK_ENGINE.md trigger "conflicting source records";
    # 09_RECONCILIATION_ENGINE.md rule 2 "Never claim certainty when
    # sources disagree."
    unresolved_conflicts = (
        db.query(DataConflict)
        .filter(DataConflict.asset_id == asset.id, DataConflict.resolution_status != "RESOLVED")
        .count()
    )
    if unresolved_conflicts:
        components["asset_risk"] = min(100.0, components["asset_risk"] + 10 * unresolved_conflicts)
        triggers.append("UNRESOLVED_DATA_CONFLICTS")

    # Existing exposure risk contributes to liquidity risk.
    # SOURCE: 08_RISK_ENGINE.md dimension "Existing exposure risk".
    exposure = asset.exposure.total_outstanding if asset.exposure else 0.0
    value = asset.current_estimated_value or 0.0
    if value > 0 and exposure / value > 0.6:
        components["liquidity_risk"] = min(100.0, components["liquidity_risk"] + 20)
        triggers.append("HIGH_EXISTING_EXPOSURE")

    overall_score = round(sum(components.values()) / len(components), 2)

    # Confidence drops with unresolved conflicts (data confidence risk dimension).
    confidence = round(max(0.3, 1.0 - 0.15 * unresolved_conflicts), 2)

    risk = RiskAssessment(
        asset_id=asset.id,
        overall_score=overall_score,
        asset_risk=components["asset_risk"],
        buyer_risk=components["buyer_risk"],
        logistics_risk=components["logistics_risk"],
        liquidity_risk=components["liquidity_risk"],
        confidence=confidence,
        risk_level=_level_from_score(overall_score).value,
        triggers=triggers,
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


def latest_risk(db: Session, asset_id: str) -> RiskAssessment | None:
    return (
        db.query(RiskAssessment)
        .filter(RiskAssessment.asset_id == asset_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )
