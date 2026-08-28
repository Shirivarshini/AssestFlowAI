"""
Valuation service.

SOURCE: 08_RISK_ENGINE.md — "The prototype may estimate current economic
value using a transparent policy based on: quantity, reference unit
value, condition, lifecycle stage, expected realizability, discounts or
deterioration." No formula is prescribed, so the policy below is an
explicit ASSUMPTION, labeled as such and kept fully deterministic per
14_AI_CODING_RULES.md rule 10.
"""
from sqlalchemy.orm import Session

from app.core.enums import LifecycleStage
from app.models import Asset, AssetValuation

# ASSUMPTION: reference unit value per unit of product, used only when the
# asset does not already carry an estimated value. In a real system this
# would come from Member 4's ERP/market-price source records.
DEFAULT_REFERENCE_UNIT_VALUE = 100.0

# ASSUMPTION: realizability multiplier increases as the asset gets closer
# to cash, reflecting lower timing/liquidity risk later in the lifecycle.
LIFECYCLE_REALIZABILITY = {
    LifecycleStage.PURCHASE_ORDER: 0.55,
    LifecycleStage.RAW_MATERIAL: 0.60,
    LifecycleStage.PRODUCTION: 0.65,
    LifecycleStage.FINISHED_GOODS: 0.75,
    LifecycleStage.SHIPMENT: 0.80,
    LifecycleStage.WAREHOUSE: 0.82,
    LifecycleStage.DELIVERY: 0.90,
    LifecycleStage.INVOICE: 0.95,
    LifecycleStage.RECEIVABLE: 0.97,
    LifecycleStage.CASH_REALISATION: 1.0,
}


def estimate_value(db: Session, asset: Asset, condition_score: float = 1.0) -> AssetValuation:
    unit_value = (
        asset.current_estimated_value / asset.quantity
        if asset.current_estimated_value and asset.quantity
        else DEFAULT_REFERENCE_UNIT_VALUE
    )
    stage = LifecycleStage(asset.current_lifecycle_stage)
    realizability = LIFECYCLE_REALIZABILITY.get(stage, 0.5)
    condition_score = max(0.0, min(1.0, condition_score))

    estimated_value = round(asset.quantity * unit_value * condition_score * realizability, 2)
    confidence = round(0.6 + 0.4 * condition_score, 2)  # ASSUMPTION

    valuation = AssetValuation(
        asset_id=asset.id,
        estimated_value=estimated_value,
        valuation_method="PROTOTYPE_QUANTITY_CONDITION_LIFECYCLE",
        confidence=confidence,
    )
    db.add(valuation)

    asset.current_estimated_value = estimated_value
    db.commit()
    db.refresh(valuation)
    return valuation
