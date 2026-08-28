"""Feature 5-8 orchestration and deterministic financing action rules."""

from .financing_amount import calculate_dynamic_financing
from .financing_need import calculate_financing_need
from .instrument_selector import select_financing_instrument
from .risk_engine import calculate_risk
from .schemas import AssetState, FinancingAction, RiskLevel
from .value_engine import calculate_asset_value

LOW_DATA_CONFIDENCE_ACTION_THRESHOLD = 0.60


def evaluate_financing(asset: AssetState) -> dict:
    value_result = calculate_asset_value(asset)
    risk_result = calculate_risk(asset)
    need_result = calculate_financing_need(asset)

    instrument = select_financing_instrument(
        asset.stage,
        risk_result["risk_level"],
        asset,
    )

    amount_result = calculate_dynamic_financing(
        asset_value=value_result["asset_value"],
        risk_level=risk_result["risk_level"],
        data_confidence=asset.data_confidence,
        existing_financing=asset.existing_financing,
        financing_need=need_result["financing_need"],
    )

    action = _determine_action(
        financing_needed=need_result["financing_needed"],
        over_leveraged=amount_result["over_leveraged"],
        data_confidence=asset.data_confidence,
        risk_level=risk_result["risk_level"],
        available_financing=amount_result["available_financing"],
        financing_need=need_result["financing_need"],
    )

    return {
        "asset_id": asset.asset_id,
        "stage": asset.stage,
        "asset_value": value_result["asset_value"],
        "risk_score": risk_result["risk_score"],
        "risk_level": risk_result["risk_level"],
        "financing_needed": need_result["financing_needed"],
        "financing_need": need_result["financing_need"],
        "instrument": instrument,
        "maximum_safe_financing": amount_result["maximum_safe_financing"],
        "existing_financing": asset.existing_financing,
        "available_financing": amount_result["available_financing"],
        "recommended_amount": amount_result["recommended_amount"],
        "action": action,
        "risk_factors": risk_result["risk_factors"],
    }


def _determine_action(
    financing_needed: bool,
    over_leveraged: bool,
    data_confidence: float,
    risk_level: RiskLevel,
    available_financing: int,
    financing_need: int,
) -> FinancingAction:
    if not financing_needed:
        return FinancingAction.NO_FINANCING_NEEDED

    if over_leveraged:
        return FinancingAction.DO_NOT_FINANCE

    if data_confidence < LOW_DATA_CONFIDENCE_ACTION_THRESHOLD:
        return FinancingAction.NEEDS_REVIEW

    if risk_level == RiskLevel.HIGH:
        return FinancingAction.PAUSE

    if 0 < available_financing < financing_need:
        return FinancingAction.LIMIT

    return FinancingAction.FINANCE
