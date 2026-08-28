"""Feature 5b — deterministic weighted risk engine."""

from .schemas import AssetState, Condition, RiskLevel, ShipmentStatus

WEIGHT_BUYER = 0.20
WEIGHT_PRODUCTION = 0.20
WEIGHT_SHIPMENT = 0.25
WEIGHT_ASSET = 0.20
WEIGHT_DATA = 0.15

SHIPMENT_DELAY_RISK_FLOOR = 65
DAMAGED_ASSET_RISK_FLOOR = 85
LOW_DATA_CONFIDENCE_THRESHOLD = 0.75
DATA_RISK_ELEVATION_MULTIPLIER = 1.20
HIGH_COMPONENT_RISK_CALLOUT = 60


def _risk_level_from_score(score: float) -> RiskLevel:
    if score <= 30:
        return RiskLevel.LOW
    if score <= 60:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def calculate_risk(asset: AssetState) -> dict:
    risk_factors = []

    buyer = asset.buyer_risk
    production = asset.production_risk
    shipment = asset.shipment_risk
    asset_condition_risk = asset.asset_risk

    if asset.shipment_status == ShipmentStatus.DELAYED:
        shipment = max(shipment, SHIPMENT_DELAY_RISK_FLOOR)
        risk_factors.append("Shipment delay detected")

    if asset.condition == Condition.DAMAGED:
        asset_condition_risk = max(
            asset_condition_risk,
            DAMAGED_ASSET_RISK_FLOOR,
        )
        risk_factors.append("Asset condition reported as damaged")

    data_risk = 100 - (asset.data_confidence * 100)

    if asset.data_confidence < LOW_DATA_CONFIDENCE_THRESHOLD:
        data_risk = min(100, data_risk * DATA_RISK_ELEVATION_MULTIPLIER)
        risk_factors.append("Data confidence below acceptable threshold")

    risk_score = (
        buyer * WEIGHT_BUYER
        + production * WEIGHT_PRODUCTION
        + shipment * WEIGHT_SHIPMENT
        + asset_condition_risk * WEIGHT_ASSET
        + data_risk * WEIGHT_DATA
    )
    risk_score = round(risk_score, 2)
    risk_level = _risk_level_from_score(risk_score)

    if shipment >= HIGH_COMPONENT_RISK_CALLOUT and "Shipment delay detected" not in risk_factors:
        risk_factors.append("Elevated shipment risk")
    if buyer >= HIGH_COMPONENT_RISK_CALLOUT:
        risk_factors.append("Elevated buyer risk")
    if production >= HIGH_COMPONENT_RISK_CALLOUT:
        risk_factors.append("Elevated production risk")
    if asset_condition_risk >= HIGH_COMPONENT_RISK_CALLOUT and "Asset condition reported as damaged" not in risk_factors:
        risk_factors.append("Elevated asset condition risk")

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "components": {
            "buyer": buyer,
            "production": production,
            "shipment": shipment,
            "asset": asset_condition_risk,
            "data": round(data_risk, 2),
        },
        "risk_factors": risk_factors,
    }
