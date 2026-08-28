"""Feature 7 — lifecycle-aware financing instrument selector."""

from .schemas import RiskLevel, Stage

STAGE_INSTRUMENT_MAP = {
    Stage.PURCHASE_ORDER: "PO_FINANCING",
    Stage.RAW_MATERIAL: "PROCUREMENT_FINANCING",
    Stage.PRODUCTION: "WIP_FINANCING",
    Stage.FINISHED_GOODS: "INVENTORY_FINANCING",
    Stage.SHIPMENT: "IN_TRANSIT_FINANCING",
    Stage.WAREHOUSE: "WAREHOUSE_FINANCING",
    Stage.DELIVERY: "RECEIVABLE_FINANCING",
    Stage.INVOICE: "INVOICE_FINANCING",
    Stage.PAYMENT: "NONE",
}

INSTRUMENT_REVIEW_REQUIRED = "INSTRUMENT_REVIEW_REQUIRED"


def select_financing_instrument(
    stage: Stage,
    risk_level: RiskLevel,
    asset=None,
) -> str:
    if stage == Stage.PAYMENT:
        return "NONE"

    if risk_level == RiskLevel.HIGH:
        return INSTRUMENT_REVIEW_REQUIRED

    return STAGE_INSTRUMENT_MAP.get(
        stage,
        INSTRUMENT_REVIEW_REQUIRED,
    )
