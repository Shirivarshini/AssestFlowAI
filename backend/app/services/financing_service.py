"""
Financing service.

SOURCE: 07_FINANCING_ENGINE.md — decision sequence, candidate instruments,
and the explicitly-labeled "Suggested prototype policy":

    safe_exposure = asset_value * advance_rate * confidence_factor * risk_factor
    available_capacity = max(0, safe_exposure - existing_exposure)
    recommended_amount = min(financing_need, available_capacity)

The document is explicit that this formula and any numeric weights are
implementation assumptions, not official challenge rules — reproduced
verbatim below and marked ASSUMPTION at each tunable constant.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import (
    LifecycleStage, FinancingInstrument, FinancingStatus, DecisionAction, RiskLevel,
)
from app.core.errors import NotFoundError, ValidationError, InvalidTransitionError, OverLeverageError
from app.models import Asset, FinancingTransaction, FinancingExposure
from app.services import audit_service

# ASSUMPTION: which instrument is eligible/recommended at which lifecycle stage.
# SOURCE for the instrument list: 07_FINANCING_ENGINE.md "Candidate instruments".
STAGE_INSTRUMENT_MAP: dict[LifecycleStage, FinancingInstrument] = {
    LifecycleStage.PURCHASE_ORDER: FinancingInstrument.PURCHASE_ORDER_FINANCING,
    LifecycleStage.RAW_MATERIAL: FinancingInstrument.PROCUREMENT_FINANCING,
    LifecycleStage.PRODUCTION: FinancingInstrument.PROCUREMENT_FINANCING,
    LifecycleStage.FINISHED_GOODS: FinancingInstrument.INVENTORY_FINANCING,
    LifecycleStage.SHIPMENT: FinancingInstrument.IN_TRANSIT_FINANCING,
    LifecycleStage.WAREHOUSE: FinancingInstrument.WAREHOUSE_FINANCING,
    LifecycleStage.DELIVERY: FinancingInstrument.TRADE_FINANCING,
    LifecycleStage.INVOICE: FinancingInstrument.INVOICE_FINANCING,
    LifecycleStage.RECEIVABLE: FinancingInstrument.RECEIVABLES_FINANCING,
    LifecycleStage.CASH_REALISATION: None,
}

# ASSUMPTION: base advance rate (% of asset value safely financeable).
ADVANCE_RATE = 0.70
# ASSUMPTION: liquidity need as a fraction of asset value, used when caller
# doesn't specify an explicit financing_need.
DEFAULT_NEED_RATIO = 0.80

RISK_FACTOR_BY_LEVEL = {
    RiskLevel.LOW: 1.0,
    RiskLevel.MEDIUM: 0.85,
    RiskLevel.HIGH: 0.6,
    RiskLevel.CRITICAL: 0.25,
}


def get_existing_exposure(db: Session, asset: Asset) -> float:
    if asset.exposure:
        return asset.exposure.total_outstanding
    return 0.0


def _sync_exposure(db: Session, asset_id: str) -> None:
    total = (
        db.query(FinancingTransaction)
        .filter(
            FinancingTransaction.asset_id == asset_id,
            FinancingTransaction.status.in_([FinancingStatus.ACTIVE.value, FinancingStatus.REDUCED.value]),
        )
        .all()
    )
    outstanding_sum = sum(t.outstanding_amount for t in total)
    exposure = db.query(FinancingExposure).filter(FinancingExposure.asset_id == asset_id).first()
    if exposure:
        exposure.total_outstanding = outstanding_sum
        exposure.updated_at = datetime.utcnow()
        db.commit()


def evaluate_financing(db: Session, asset: Asset, risk_score: float, risk_level: str, confidence: float, financing_need: float | None = None):
    """Deterministic financing decision. Returns a dict matching
    04_API_CONTRACT.md's financing-evaluation response shape exactly."""
    stage = LifecycleStage(asset.current_lifecycle_stage)
    instrument = STAGE_INSTRUMENT_MAP.get(stage)

    asset_value = asset.current_estimated_value or 0.0
    existing_exposure = get_existing_exposure(db, asset)

    risk_factor = RISK_FACTOR_BY_LEVEL.get(RiskLevel(risk_level), 0.5)
    confidence_factor = max(0.0, min(1.0, confidence))

    safe_exposure = round(asset_value * ADVANCE_RATE * confidence_factor * risk_factor, 2)
    available_capacity = max(0.0, round(safe_exposure - existing_exposure, 2))

    need = financing_need if financing_need is not None else round(asset_value * DEFAULT_NEED_RATIO, 2)
    recommended_amount = round(min(need, available_capacity), 2)

    financing_required = stage != LifecycleStage.CASH_REALISATION and need > 0 and recommended_amount > 0

    decision_factors = ["Asset physical/lifecycle state verified"]
    if instrument:
        decision_factors.append(f"Lifecycle stage {stage.value} maps to {instrument.value}")
    if existing_exposure > 0:
        decision_factors.append(f"Existing exposure of {existing_exposure} considered")
    if risk_level in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value):
        decision_factors.append(f"Elevated risk level ({risk_level}) reduced safe exposure")
    if confidence_factor < 0.7:
        decision_factors.append("Low data confidence reduced safe exposure")

    # Action determination — ASSUMPTION mapping, smallest reasonable policy
    # covering 07_FINANCING_ENGINE.md's required action set.
    active_txn = (
        db.query(FinancingTransaction)
        .filter(FinancingTransaction.asset_id == asset.id, FinancingTransaction.status == FinancingStatus.ACTIVE.value)
        .order_by(FinancingTransaction.start_date.desc())
        .first()
    )

    if stage == LifecycleStage.CASH_REALISATION:
        action = DecisionAction.SETTLE
    elif not financing_required:
        action = DecisionAction.NEEDS_REVIEW if asset_value == 0 else DecisionAction.MAINTAIN
    elif active_txn and instrument and active_txn.instrument != instrument.value:
        action = DecisionAction.TRANSITION
    elif active_txn and recommended_amount < active_txn.outstanding_amount:
        action = DecisionAction.REDUCE_EXPOSURE
    elif active_txn and recommended_amount > active_txn.outstanding_amount:
        action = DecisionAction.INCREASE
    elif active_txn:
        action = DecisionAction.MAINTAIN
    else:
        action = DecisionAction.MAINTAIN if recommended_amount > 0 else DecisionAction.NEEDS_REVIEW

    # Additive Feature 11-13 controls. Imported locally to avoid a module
    # cycle because the control service reuses this module's policy constants.
    from app.services import control_service
    exposure = control_service.calculate_exposure(db, asset, confidence_factor, risk_level)
    duplicate = control_service.detect_duplicate(db, asset, instrument.value if instrument else None)
    leverage = control_service.detect_over_leverage(db, asset, recommended_amount, confidence_factor, risk_level)
    if stage == LifecycleStage.CASH_REALISATION:
        action = DecisionAction.SETTLE
        recommended_amount = 0.0
    elif leverage["over_leveraged"]:
        action = DecisionAction.BLOCK if leverage["action"] == "BLOCK" else DecisionAction.REDUCE_EXPOSURE
        recommended_amount = min(recommended_amount, exposure["available_safe_capacity"])
        decision_factors.append(f"Over-leverage control: excess amount {leverage['excess_amount']}")
    elif duplicate["duplicate_detected"]:
        action = DecisionAction.NEEDS_REVIEW
        decision_factors.append(duplicate["reason"])

    return {
        "asset_id": asset.id,
        "financing_required": financing_required,
        "recommended_instrument": instrument.value if instrument else None,
        "maximum_safe_amount": safe_exposure,
        "recommended_amount": recommended_amount,
        "risk_level": risk_level,
        "confidence": confidence_factor,
        "action": action.value,
        "decision_factors": decision_factors,
        "existing_exposure": exposure["total_outstanding"],
        "available_capacity": exposure["available_safe_capacity"],
        "duplicate_check": duplicate,
        "leverage_check": leverage,
    }


def open_or_update_financing(db: Session, asset: Asset, instrument: str, amount: float) -> FinancingTransaction:
    """Duplicate/over-leverage protection.
    SOURCE: 01_PROBLEM_STATEMENT.md req 8 ("Track existing exposure to
    reduce duplicate financing and over-leverage"); 15_DEMO_SCENARIOS.md
    Scenario 3."""
    existing_exposure = get_existing_exposure(db, asset)
    asset_value = asset.current_estimated_value or 0.0
    hard_cap = asset_value * ADVANCE_RATE  # ASSUMPTION ceiling regardless of risk adjustment

    if existing_exposure + amount > hard_cap:
        raise OverLeverageError(
            f"Requested amount {amount} would push total exposure "
            f"({existing_exposure + amount}) above the safe cap ({hard_cap}) for asset {asset.id}.",
            {"existing_exposure": existing_exposure, "requested_amount": amount, "safe_cap": hard_cap},
        )

    active_txn = (
        db.query(FinancingTransaction)
        .filter(
            FinancingTransaction.asset_id == asset.id,
            FinancingTransaction.instrument == instrument,
            FinancingTransaction.status == FinancingStatus.ACTIVE.value,
        )
        .first()
    )
    if active_txn:
        # Duplicate prevention: update existing rather than opening a second
        # active line for the same instrument.
        active_txn.outstanding_amount = amount
        active_txn.principal = max(active_txn.principal, amount)
        db.commit()
        db.refresh(active_txn)
        txn = active_txn
    else:
        txn = FinancingTransaction(
            asset_id=asset.id,
            instrument=instrument,
            principal=amount,
            outstanding_amount=amount,
            currency=asset.currency,
            status=FinancingStatus.ACTIVE.value,
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)

    _sync_exposure(db, asset.id)
    audit_service.record(db, "FINANCING_OPENED_OR_UPDATED", asset.id, details={"instrument": instrument, "amount": amount})
    return txn


def list_financing(db: Session, asset_id: str) -> list[FinancingTransaction]:
    return (
        db.query(FinancingTransaction)
        .filter(FinancingTransaction.asset_id == asset_id)
        .order_by(FinancingTransaction.start_date.desc())
        .all()
    )


def get_financing(db: Session, financing_id: str) -> FinancingTransaction:
    txn = db.get(FinancingTransaction, financing_id)
    if not txn:
        raise NotFoundError(f"Financing transaction {financing_id} not found.", {"financing_id": financing_id})
    return txn


def transition_financing(db: Session, financing_id: str, new_instrument: str | None, new_status: str | None, reason: str | None) -> FinancingTransaction:
    txn = get_financing(db, financing_id)

    if new_instrument is not None:
        if new_instrument not in FinancingInstrument.__members__:
            raise ValidationError(f"Unknown financing instrument '{new_instrument}'.")
        txn.instrument = new_instrument
        txn.status = FinancingStatus.TRANSITIONED.value

    if new_status is not None:
        if new_status not in FinancingStatus.__members__:
            raise ValidationError(f"Unknown financing status '{new_status}'.")
        if txn.status == FinancingStatus.SETTLED.value:
            raise InvalidTransitionError(f"Financing {financing_id} is already settled and cannot change state.")
        txn.status = new_status
        if new_status == FinancingStatus.SETTLED.value:
            txn.outstanding_amount = 0.0

    db.commit()
    db.refresh(txn)
    _sync_exposure(db, txn.asset_id)

    audit_service.record(
        db, "FINANCING_TRANSITIONED", txn.asset_id,
        details={"financing_id": financing_id, "new_instrument": new_instrument, "new_status": new_status, "reason": reason},
    )
    return txn


def settle_financing(db: Session, financing_id: str) -> FinancingTransaction:
    return transition_financing(db, financing_id, new_instrument=None, new_status=FinancingStatus.SETTLED.value, reason="SETTLEMENT")
