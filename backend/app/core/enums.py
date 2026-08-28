"""
Domain enums.

Values marked SOURCE are taken verbatim from the uploaded project
documents and must never be renamed. Values marked ASSUMPTION are
implementation choices made because the source documents intentionally
left them unspecified (per 01_PROBLEM_STATEMENT.md "Source boundary" and
07_FINANCING_ENGINE.md "Important").
"""
import enum


class LifecycleStage(str, enum.Enum):
    """SOURCE: 06_ASSET_LIFECYCLE.md canonical lifecycle."""
    PURCHASE_ORDER = "PURCHASE_ORDER"
    RAW_MATERIAL = "RAW_MATERIAL"
    PRODUCTION = "PRODUCTION"
    FINISHED_GOODS = "FINISHED_GOODS"
    SHIPMENT = "SHIPMENT"
    WAREHOUSE = "WAREHOUSE"
    DELIVERY = "DELIVERY"
    INVOICE = "INVOICE"
    RECEIVABLE = "RECEIVABLE"
    CASH_REALISATION = "CASH_REALISATION"


# SOURCE: 06_ASSET_LIFECYCLE.md — ordered forward path used to validate transitions.
LIFECYCLE_ORDER = [
    LifecycleStage.PURCHASE_ORDER,
    LifecycleStage.RAW_MATERIAL,
    LifecycleStage.PRODUCTION,
    LifecycleStage.FINISHED_GOODS,
    LifecycleStage.SHIPMENT,
    LifecycleStage.WAREHOUSE,
    LifecycleStage.DELIVERY,
    LifecycleStage.INVOICE,
    LifecycleStage.RECEIVABLE,
    LifecycleStage.CASH_REALISATION,
]


class FinancingInstrument(str, enum.Enum):
    """SOURCE: 01_PROBLEM_STATEMENT.md / 07_FINANCING_ENGINE.md."""
    PURCHASE_ORDER_FINANCING = "PURCHASE_ORDER_FINANCING"
    PROCUREMENT_FINANCING = "PROCUREMENT_FINANCING"
    INVENTORY_FINANCING = "INVENTORY_FINANCING"
    IN_TRANSIT_FINANCING = "IN_TRANSIT_FINANCING"
    WAREHOUSE_FINANCING = "WAREHOUSE_FINANCING"
    TRADE_FINANCING = "TRADE_FINANCING"
    INVOICE_FINANCING = "INVOICE_FINANCING"
    RECEIVABLES_FINANCING = "RECEIVABLES_FINANCING"


class FinancingStatus(str, enum.Enum):
    """ASSUMPTION: exact status set not specified by source; smallest set
    that supports 07_FINANCING_ENGINE.md's required actions
    (maintain/increase/reduce/transition/refinance/settle)."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REDUCED = "REDUCED"
    TRANSITIONED = "TRANSITIONED"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"


class DecisionAction(str, enum.Enum):
    """SOURCE terms drawn from 04_API_CONTRACT.md ("MAINTAIN"),
    12_EVENT_SYSTEM.md ("REDUCE_EXPOSURE"), 10_AI_AGENTS.md
    ("TRANSITION", "NEEDS_REVIEW"). INCREASE/REFINANCE/SETTLE/BLOCK are
    ASSUMPTION additions needed to cover 07_FINANCING_ENGINE.md's full
    action list (maintain/increase/reduce/transition/refinance/settle)."""
    MAINTAIN = "MAINTAIN"
    INCREASE = "INCREASE"
    REDUCE_EXPOSURE = "REDUCE_EXPOSURE"
    TRANSITION = "TRANSITION"
    REFINANCE = "REFINANCE"
    SETTLE = "SETTLE"
    BLOCK = "BLOCK"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RiskLevel(str, enum.Enum):
    """SOURCE: 08_RISK_ENGINE.md."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventType(str, enum.Enum):
    """SOURCE: 12_EVENT_SYSTEM.md, all 9 material events.
    PAYMENT_RECEIVED is an ASSUMPTION addition (also referenced in the
    Member-2 instructions doc) needed to trigger financing SETTLE, since
    no source-listed event currently closes the loop after
    RECEIVABLES_FINANCING."""
    PRODUCTION_DELAY = "PRODUCTION_DELAY"
    SHIPMENT_DELAY = "SHIPMENT_DELAY"
    INVENTORY_DETERIORATION = "INVENTORY_DETERIORATION"
    WAREHOUSE_EXCEPTION = "WAREHOUSE_EXCEPTION"
    DELIVERY_CONFIRMED = "DELIVERY_CONFIRMED"
    BUYER_RISK_CHANGED = "BUYER_RISK_CHANGED"
    RECEIVABLE_DELAY = "RECEIVABLE_DELAY"
    INVOICE_VERIFIED = "INVOICE_VERIFIED"
    DATA_CONFLICT = "DATA_CONFLICT"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"  # ASSUMPTION addition
    NEXT_LIFECYCLE_STAGE = "NEXT_LIFECYCLE_STAGE"  # deterministic simulator control


class EventSeverity(str, enum.Enum):
    """ASSUMPTION: not specified by source; needed for
    asset_lifecycle_events.severity column (05_DATABASE_SCHEMA.md)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConflictResolutionStatus(str, enum.Enum):
    """ASSUMPTION: supports data_conflicts.resolution_status
    (05_DATABASE_SCHEMA.md) and 09_RECONCILIATION_ENGINE.md's
    "resolve or qualify conflict" step."""
    RESOLVED = "RESOLVED"
    QUALIFIED = "QUALIFIED"
    UNRESOLVED = "UNRESOLVED"


class AlertSeverity(str, enum.Enum):
    """ASSUMPTION: supports alerts.severity (05_DATABASE_SCHEMA.md)."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    """ASSUMPTION: supports alerts.status (05_DATABASE_SCHEMA.md)."""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class DecisionType(str, enum.Enum):
    """ASSUMPTION: supports ai_decisions.decision_type (05_DATABASE_SCHEMA.md)."""
    FINANCING_EVALUATION = "FINANCING_EVALUATION"
    EVENT_REASSESSMENT = "EVENT_REASSESSMENT"
    RISK_REASSESSMENT = "RISK_REASSESSMENT"
