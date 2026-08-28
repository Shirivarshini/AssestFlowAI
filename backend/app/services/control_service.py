"""Deterministic exposure, duplicate-financing and leverage controls."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import FinancingStatus, RiskLevel
from app.models import Asset, FinancingTransaction, FinancingExposure, Alert
from app.services.financing_service import ADVANCE_RATE, RISK_FACTOR_BY_LEVEL

ACTIVE_STATUSES = (FinancingStatus.ACTIVE.value, FinancingStatus.REDUCED.value)


def calculate_exposure(db: Session, asset: Asset, confidence: float = 1.0, risk_level: str = "LOW") -> dict:
    transactions = db.query(FinancingTransaction).filter(
        FinancingTransaction.asset_id == asset.id,
        FinancingTransaction.status.in_(ACTIVE_STATUSES),
    ).all()
    principal = round(sum(t.principal for t in transactions), 2)
    outstanding = round(sum(t.outstanding_amount for t in transactions), 2)
    factor = RISK_FACTOR_BY_LEVEL.get(RiskLevel(risk_level), 0.5)
    maximum = round((asset.current_estimated_value or 0) * ADVANCE_RATE * max(0, min(1, confidence)) * factor, 2)
    available = max(0.0, round(maximum - outstanding, 2))
    utilization = round(outstanding / maximum * 100, 2) if maximum else (100.0 if outstanding else 0.0)
    row = db.query(FinancingExposure).filter(FinancingExposure.asset_id == asset.id).first()
    if row:
        row.total_outstanding = outstanding
        row.updated_at = datetime.utcnow()
        db.commit()
    return {
        "asset_id": asset.id, "total_principal": principal, "total_outstanding": outstanding,
        "active_financing_count": len(transactions), "available_safe_capacity": available,
        "maximum_safe_exposure": maximum, "utilization_percentage": utilization,
        "currency": asset.currency, "updated_at": (row.updated_at if row else datetime.utcnow()),
    }


def detect_duplicate(db: Session, asset: Asset, instrument: str | None = None, lender_id: str | None = None, collateral_reference: str | None = None) -> dict:
    active = db.query(FinancingTransaction).filter(
        FinancingTransaction.asset_id == asset.id,
        FinancingTransaction.status.in_(ACTIVE_STATUSES),
    ).all()
    related = [t for t in active if (not instrument or t.instrument == instrument) and (not lender_id or t.lender_id == lender_id) and (not collateral_reference or t.collateral_reference == collateral_reference)]
    detected = bool(related and (instrument or collateral_reference))
    severity = "HIGH" if len(related) > 1 or (detected and lender_id is not None) else "MEDIUM" if detected else "LOW"
    return {
        "duplicate_detected": detected, "severity": severity,
        "related_financing_ids": [t.id for t in related],
        "reason": "An overlapping active financing claim exists for this asset and instrument." if detected else "No overlapping active financing claim matched.",
        "recommended_action": "BLOCK" if severity == "HIGH" else "REVIEW" if detected else "ALLOW",
    }


def detect_over_leverage(db: Session, asset: Asset, requested_amount: float, confidence: float = 1.0, risk_level: str = "LOW") -> dict:
    exposure = calculate_exposure(db, asset, confidence, risk_level)
    existing, safe = exposure["total_outstanding"], exposure["maximum_safe_exposure"]
    excess = max(0.0, round(existing + requested_amount - safe, 2))
    over = existing > safe or existing + requested_amount > safe
    utilization = round((existing + requested_amount) / safe * 100, 2) if safe else (100.0 if existing + requested_amount else 0.0)
    severity = "CRITICAL" if utilization >= 125 else "HIGH" if over else "LOW"
    return {
        "over_leveraged": over, "safe_exposure": safe, "existing_exposure": existing,
        "requested_amount": requested_amount, "excess_amount": excess, "utilization": utilization,
        "severity": severity, "action": "BLOCK" if severity == "CRITICAL" else "REDUCE" if over else "ALLOW",
    }


def create_control_alert(db: Session, asset_id: str, alert_type: str, severity: str, message: str) -> Alert:
    existing = db.query(Alert).filter(Alert.asset_id == asset_id, Alert.alert_type == alert_type, Alert.status == "OPEN").first()
    if existing:
        return existing
    alert = Alert(asset_id=asset_id, alert_type=alert_type, severity=severity, message=message, status="OPEN")
    db.add(alert); db.commit(); db.refresh(alert)
    return alert
