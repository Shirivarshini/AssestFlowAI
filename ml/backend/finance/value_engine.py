"""Feature 5a — deterministic asset valuation."""

from .schemas import AssetState, Stage

# Hackathon prototype policy, not a production valuation model.
STAGE_VALUATION_FACTORS = {
    Stage.PURCHASE_ORDER: 1.00,
    Stage.RAW_MATERIAL: 0.60,
    Stage.PRODUCTION: 0.70,
    Stage.FINISHED_GOODS: 0.90,
    Stage.SHIPMENT: 0.90,
    Stage.WAREHOUSE: 0.90,
    Stage.DELIVERY: 0.95,
    Stage.INVOICE: 1.00,
    Stage.PAYMENT: 0.00,
}


def calculate_asset_value(asset: AssetState) -> dict:
    factor = STAGE_VALUATION_FACTORS[asset.stage]
    asset_value = int(round(asset.purchase_value * factor))
    return {
        "asset_value": asset_value,
        "valuation_factor": factor,
    }
