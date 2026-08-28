"""
Pydantic schemas.

SOURCE: 04_API_CONTRACT.md is authoritative for field names in the
dashboard/financing-evaluation examples. Other schemas follow
05_DATABASE_SCHEMA.md field names directly so the frontend never has to
guess a response shape (03_ARCHITECTURE.md rule #1).
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


# ---------- Assets ----------

class AssetCreate(BaseModel):
    external_reference: Optional[str] = None
    product_name: str
    quantity: float
    unit: str
    owner_id: Optional[str] = None
    current_lifecycle_stage: str = "PURCHASE_ORDER"
    current_location: Optional[str] = None
    current_estimated_value: Optional[float] = None
    currency: str = "INR"


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_reference: Optional[str]
    product_name: str
    quantity: float
    unit: str
    owner_id: Optional[str]
    current_lifecycle_stage: str
    current_location: Optional[str]
    current_estimated_value: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime


class LifecycleEventCreate(BaseModel):
    event_type: str
    to_stage: Optional[str] = None
    severity: Optional[str] = None
    source_id: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class LifecycleEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    event_type: str
    from_stage: Optional[str]
    to_stage: Optional[str]
    event_time: datetime
    source_id: Optional[str]
    severity: Optional[str]
    payload: Optional[dict[str, Any]]


class TimelineOut(BaseModel):
    asset_id: str
    current_lifecycle_stage: str
    events: list[LifecycleEventOut]


# ---------- Risk ----------

class RiskAssessmentOut(BaseModel):
    overall_score: float
    risk_level: str
    components: dict[str, float]
    confidence: float
    triggers: list[str]


class RiskReassessRequest(BaseModel):
    asset_id: str
    reason: Optional[str] = "MANUAL"


# ---------- Financing ----------

class FinancingEvaluateRequest(BaseModel):
    asset_id: str
    reason: str = "MANUAL"


class FinancingEvaluateResponse(BaseModel):
    asset_id: str
    financing_required: bool
    recommended_instrument: Optional[str]
    maximum_safe_amount: float
    recommended_amount: float
    risk_level: str
    confidence: float
    action: str
    decision_factors: list[str]
    existing_exposure: float = 0.0
    available_capacity: float = 0.0
    duplicate_check: Optional[dict[str, Any]] = None
    leverage_check: Optional[dict[str, Any]] = None


class FinancingTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    instrument: str
    principal: float
    outstanding_amount: float
    currency: str
    status: str
    lender_id: Optional[str]
    collateral_reference: Optional[str]
    start_date: datetime
    maturity_date: Optional[datetime]


class FinancingTransitionRequest(BaseModel):
    new_instrument: Optional[str] = None
    new_status: Optional[str] = None
    reason: Optional[str] = None


# ---------- Reconciliation ----------

class ReconciliationRunRequest(BaseModel):
    asset_id: str


class ConflictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    source_a: str
    source_b: str
    field: str
    value_a: Optional[str]
    value_b: Optional[str]
    resolution_status: str
    resolution_reason: Optional[str]
    confidence: Optional[float]
    created_at: datetime


# ---------- Decisions ----------

class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    decision_type: str
    recommendation: str
    amount: Optional[float]
    instrument: Optional[str]
    confidence: Optional[float]
    decision_factors: Optional[list[str]]
    created_at: datetime
    executed: int
    trigger: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    asset_value: Optional[float] = None
    risk_score: Optional[float] = None
    existing_exposure: Optional[float] = None
    maximum_safe_exposure: Optional[float] = None


# ---------- Alerts ----------

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    alert_type: str
    severity: str
    message: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    related_event_id: Optional[str] = None
    related_decision_id: Optional[str] = None


# ---------- Dashboard ----------

class DashboardOut(BaseModel):
    asset_counts: dict[str, int]
    total_exposure: float
    financing_opportunities: int
    risk_alerts: int
    recent_events: list[LifecycleEventOut]
    financing_transitions: list[FinancingTransactionOut]
    recent_decisions: list[DecisionOut] = []
    duplicate_financing_warnings: int = 0
    over_leverage_warnings: int = 0
    pending_alerts: int = 0


# ---------- Controls / Operations ----------

class ControlCheckRequest(BaseModel):
    requested_amount: float = 0.0
    instrument: Optional[str] = None
    lender_id: Optional[str] = None
    collateral_reference: Optional[str] = None


class OrchestrateRequest(BaseModel):
    trigger: str = "MANUAL"


class AlertUpdate(BaseModel):
    status: str


class EventSimulateRequest(BaseModel):
    asset_id: str
    event_type: str
    to_stage: Optional[str] = None
    severity: Optional[str] = None
