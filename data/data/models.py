"""
Core data structures for the Member 4 (Data & Integration) layer.

These are intentionally framework-free: no FastAPI, no SQLAlchemy,
no React, no LLM SDK. They exist so that Members 1-3 (frontend,
backend, AI) can later consume deterministic, typed structures
without depending on this module's internals.

Naming follows 05_DATABASE_SCHEMA.md and 09_RECONCILIATION_ENGINE.md
so downstream layers do not have to translate terminology.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum

# ---------------------------------------------------------------------------
# Canonical lifecycle stages (06_ASSET_LIFECYCLE.md)
# ---------------------------------------------------------------------------


class LifecycleStage(str, Enum):
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


# Canonical forward order. Used only by this module for demo fixtures /
# event ordering sanity checks -- NOT a financing policy.
LIFECYCLE_ORDER = [s.value for s in LifecycleStage]


# ---------------------------------------------------------------------------
# Material event types (12_EVENT_SYSTEM.md / CSI_ORIGIN_2026_PS6 instructions)
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    PRODUCTION_DELAY = "PRODUCTION_DELAY"
    SHIPMENT_DELAY = "SHIPMENT_DELAY"
    INVENTORY_DETERIORATION = "INVENTORY_DETERIORATION"
    WAREHOUSE_EXCEPTION = "WAREHOUSE_EXCEPTION"
    DELIVERY_CONFIRMED = "DELIVERY_CONFIRMED"
    BUYER_RISK_CHANGED = "BUYER_RISK_CHANGED"
    RECEIVABLE_DELAY = "RECEIVABLE_DELAY"
    INVOICE_VERIFIED = "INVOICE_VERIFIED"
    DATA_CONFLICT = "DATA_CONFLICT"


SUPPORTED_EVENT_TYPES = {e.value for e in EventType}


# ---------------------------------------------------------------------------
# Source types (09_RECONCILIATION_ENGINE.md)
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    ERP = "ERP"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    INVOICE = "INVOICE"
    LOGISTICS = "LOGISTICS"
    WAREHOUSE = "WAREHOUSE"
    TELEMETRY = "TELEMETRY"
    FINANCING = "FINANCING"


# ---------------------------------------------------------------------------
# Raw source record (as emitted by a simulated connector, pre-normalization)
# ---------------------------------------------------------------------------


@dataclass
class SourceRecord:
    """
    A raw record as it would arrive from a connector, before normalization.
    Mirrors the `source_records` table in 05_DATABASE_SCHEMA.md
    ("Stores raw records from simulated or real connectors").

    `payload` deliberately stays a free-form dict: each source system has
    its own shape. normalizer.py is responsible for flattening this into
    NormalizedRecord entries.
    """

    source_record_id: str
    source: str  # SourceType value
    asset_id: str
    observed_at: str  # ISO 8601
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Normalized record (one field, one source, one observation)
# ---------------------------------------------------------------------------


@dataclass
class NormalizedRecord:
    """
    One (asset, source, field, value) observation.

    This is the internal normalized representation requested in the
    Member 4 brief:
        {
          "asset_id": "AST-1001",
          "source": "ERP",
          "source_record_id": "ERP-001",
          "field": "quantity",
          "value": 1000,
          "observed_at": "..."
        }
    """

    asset_id: str
    source: str
    source_record_id: str
    field: str
    value: Any
    observed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Conflict / resolution structures (09_RECONCILIATION_ENGINE.md, 05_DATABASE_SCHEMA.md)
# ---------------------------------------------------------------------------


class ResolutionStatus(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    RESOLVED = "RESOLVED"
    QUALIFIED = "QUALIFIED"  # resolved but with reduced confidence
    NEEDS_REVIEW = "NEEDS_REVIEW"  # could not be safely resolved


@dataclass
class SourceObservation:
    """One source's contribution to a field, used inside a conflict record."""

    source: str
    source_record_id: str
    value: Any
    observed_at: str
    reliability_rank: int  # lower = more trusted, see resolver.py


@dataclass
class DataConflict:
    """
    Mirrors the `data_conflicts` table:
        asset_id, source_a, source_b, field, value_a, value_b,
        resolution_status, resolution_reason, confidence

    Since more than two sources may disagree, `observations` holds the
    full N-way evidence, while `source_a`/`source_b`/`value_a`/`value_b`
    are kept as the two most reliable disagreeing sources so the shape
    stays compatible with 05_DATABASE_SCHEMA.md for a future relational
    table.
    """

    asset_id: str
    field: str
    observations: list  # list[SourceObservation]
    source_a: Optional[str]
    source_b: Optional[str]
    value_a: Any
    value_b: Any
    resolution_status: str
    resolution_reason: str
    canonical_value: Any
    confidence: float

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Canonical asset state (05_DATABASE_SCHEMA.md: asset_states)
# ---------------------------------------------------------------------------


@dataclass
class FieldProvenance:
    """Which source record(s) a canonical field value came from."""

    field: str
    value: Any
    sources: list  # list[str] of contributing source names
    source_record_ids: list
    resolution_status: str
    confidence: float


@dataclass
class CanonicalAssetState:
    """
    Mirrors `asset_states`:
        asset_id, physical_state, financial_state, contractual_state,
        condition_score, state_confidence, effective_at, source

    `field_values` and `provenance` are additive (not in the original
    table) so downstream consumers can see exactly which reconciled
    field values fed the summary state, per the 05_DATABASE_SCHEMA.md
    design rule: "Preserve source evidence and separately store the
    canonical state."
    """

    asset_id: str
    physical_state: Optional[str]
    financial_state: Optional[str]
    contractual_state: Optional[str]
    condition_score: Optional[float]
    state_confidence: float
    effective_at: str
    source: str  # "RECONCILIATION_ENGINE"
    field_values: dict  # field -> resolved value
    provenance: list  # list[FieldProvenance]
    conflicts: list  # list[DataConflict] (including resolved ones)
    status: str  # "OK" | "NEEDS_REVIEW"

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "physical_state": self.physical_state,
            "financial_state": self.financial_state,
            "contractual_state": self.contractual_state,
            "condition_score": self.condition_score,
            "state_confidence": self.state_confidence,
            "effective_at": self.effective_at,
            "source": self.source,
            "field_values": self.field_values,
            "provenance": [asdict(p) for p in self.provenance],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# Lifecycle event (05_DATABASE_SCHEMA.md: asset_lifecycle_events)
# ---------------------------------------------------------------------------


@dataclass
class LifecycleEvent:
    """
    Mirrors `asset_lifecycle_events`:
        id, asset_id, event_type, from_stage, to_stage, event_time,
        source_id, severity, payload

    Produced by event_simulator.py. This module does NOT compute
    financing or risk impact -- it only emits the structured event for
    the (not-yet-built) backend/AI layers to consume, per the Member 4
    scope boundary.
    """

    event_id: str
    asset_id: str
    event_type: str
    from_stage: Optional[str]
    to_stage: Optional[str]
    event_time: str
    source_id: str
    severity: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    payload: dict

    def to_dict(self) -> dict:
        return asdict(self)
