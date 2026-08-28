"""Pydantic schemas for the Member 3 finance decision engine."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Stage(str, Enum):
    PURCHASE_ORDER = "PURCHASE_ORDER"
    RAW_MATERIAL = "RAW_MATERIAL"
    PRODUCTION = "PRODUCTION"
    FINISHED_GOODS = "FINISHED_GOODS"
    SHIPMENT = "SHIPMENT"
    WAREHOUSE = "WAREHOUSE"
    DELIVERY = "DELIVERY"
    INVOICE = "INVOICE"
    PAYMENT = "PAYMENT"


class Condition(str, Enum):
    GOOD = "GOOD"
    DAMAGED = "DAMAGED"
    PARTIAL = "PARTIAL"


class ShipmentStatus(str, Enum):
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ProductionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FinancingAction(str, Enum):
    FINANCE = "FINANCE"
    LIMIT = "LIMIT"
    REDUCE = "REDUCE"
    PAUSE = "PAUSE"
    DO_NOT_FINANCE = "DO_NOT_FINANCE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NO_FINANCING_NEEDED = "NO_FINANCING_NEEDED"


class AssetState(BaseModel):
    """Canonical input contract for the finance engine."""

    asset_id: str = Field(..., min_length=1)
    stage: Stage

    purchase_value: int = Field(..., ge=0, description="INR, integer rupees")
    quantity: int = Field(..., ge=0)
    condition: Condition
    location: str = Field(..., min_length=1)

    shipment_status: ShipmentStatus
    production_status: ProductionStatus

    buyer_risk: int = Field(..., ge=0, le=100)
    production_risk: int = Field(..., ge=0, le=100)
    shipment_risk: int = Field(..., ge=0, le=100)
    asset_risk: int = Field(..., ge=0, le=100)

    data_confidence: float = Field(..., ge=0.0, le=1.0)

    required_capital: int = Field(..., ge=0)
    existing_financing: int = Field(..., ge=0)

    product: Optional[str] = None
    company: Optional[str] = None


class FinancingDecision(BaseModel):
    """API response produced by the deterministic finance engine."""

    asset_id: str
    stage: Stage

    asset_value: int
    risk_score: float
    risk_level: RiskLevel

    financing_needed: bool
    financing_need: int

    instrument: str

    maximum_safe_financing: int
    existing_financing: int
    available_financing: int
    recommended_amount: int

    action: FinancingAction
    risk_factors: List[str]

    explanation: Optional[str] = None
