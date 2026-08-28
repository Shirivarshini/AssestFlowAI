"""
SQLAlchemy models.

SOURCE: 05_DATABASE_SCHEMA.md is authoritative for entity names and the
fields listed there. Primary keys, foreign keys, timestamps and a couple
of small structural additions (e.g. exposure/valuation ids) are the
smallest reasonable additions needed to make the schema runnable, per
14_AI_CODING_RULES.md ("choose the smallest reversible implementation").
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: gen_id("AST"))
    external_reference = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    owner_id = Column(String, nullable=True)
    current_lifecycle_stage = Column(String, nullable=False)
    current_location = Column(String, nullable=True)
    current_estimated_value = Column(Float, nullable=True)
    currency = Column(String, nullable=False, default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    states = relationship("AssetState", back_populates="asset", cascade="all, delete-orphan")
    events = relationship("AssetLifecycleEvent", back_populates="asset", cascade="all, delete-orphan")
    financing_transactions = relationship("FinancingTransaction", back_populates="asset", cascade="all, delete-orphan")
    valuations = relationship("AssetValuation", back_populates="asset", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="asset", cascade="all, delete-orphan")
    source_records = relationship("SourceRecord", back_populates="asset", cascade="all, delete-orphan")
    conflicts = relationship("DataConflict", back_populates="asset", cascade="all, delete-orphan")
    decisions = relationship("AIDecision", back_populates="asset", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="asset", cascade="all, delete-orphan")
    exposure = relationship("FinancingExposure", back_populates="asset", uselist=False, cascade="all, delete-orphan")


class AssetState(Base):
    __tablename__ = "asset_states"

    id = Column(String, primary_key=True, default=lambda: gen_id("STA"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    physical_state = Column(String, nullable=True)
    financial_state = Column(String, nullable=True)
    contractual_state = Column(String, nullable=True)
    condition_score = Column(Float, nullable=True)
    state_confidence = Column(Float, nullable=True)
    effective_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=True)

    asset = relationship("Asset", back_populates="states")


class AssetLifecycleEvent(Base):
    __tablename__ = "asset_lifecycle_events"

    id = Column(String, primary_key=True, default=lambda: gen_id("EVT"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    event_type = Column(String, nullable=False)
    from_stage = Column(String, nullable=True)
    to_stage = Column(String, nullable=True)
    event_time = Column(DateTime, default=datetime.utcnow)
    source_id = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)

    asset = relationship("Asset", back_populates="events")


class FinancingTransaction(Base):
    __tablename__ = "financing_transactions"

    id = Column(String, primary_key=True, default=lambda: gen_id("FIN"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    instrument = Column(String, nullable=False)
    principal = Column(Float, nullable=False)
    outstanding_amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    status = Column(String, nullable=False)
    lender_id = Column(String, nullable=True)
    collateral_reference = Column(String, nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    maturity_date = Column(DateTime, nullable=True)

    asset = relationship("Asset", back_populates="financing_transactions")


class FinancingExposure(Base):
    """SOURCE: 05_DATABASE_SCHEMA.md — "Track total exposure against an
    asset independently of individual financing products." One row per
    asset, kept in sync whenever a financing_transaction changes."""
    __tablename__ = "financing_exposure"

    id = Column(String, primary_key=True, default=lambda: gen_id("EXP"))
    asset_id = Column(String, ForeignKey("assets.id"), unique=True, nullable=False)
    total_outstanding = Column(Float, nullable=False, default=0.0)
    currency = Column(String, nullable=False, default="INR")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", back_populates="exposure")


class AssetValuation(Base):
    __tablename__ = "asset_valuations"

    id = Column(String, primary_key=True, default=lambda: gen_id("VAL"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    estimated_value = Column(Float, nullable=False)
    valuation_method = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    effective_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="valuations")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: gen_id("RSK"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    asset_risk = Column(Float, nullable=False)
    buyer_risk = Column(Float, nullable=False)
    logistics_risk = Column(Float, nullable=False)
    liquidity_risk = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(String, nullable=True)
    triggers = Column(JSON, nullable=True)

    asset = relationship("Asset", back_populates="risk_assessments")


class SourceRecord(Base):
    """SOURCE: 05_DATABASE_SCHEMA.md — "Stores raw records from simulated
    or real connectors." Populated by Member 4; never overwritten."""
    __tablename__ = "source_records"

    id = Column(String, primary_key=True, default=lambda: gen_id("SRC"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    source_name = Column(String, nullable=False)
    field = Column(String, nullable=False)
    value = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_payload = Column(JSON, nullable=True)

    asset = relationship("Asset", back_populates="source_records")


class DataConflict(Base):
    __tablename__ = "data_conflicts"

    id = Column(String, primary_key=True, default=lambda: gen_id("CNF"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    source_a = Column(String, nullable=False)
    source_b = Column(String, nullable=False)
    field = Column(String, nullable=False)
    value_a = Column(String, nullable=True)
    value_b = Column(String, nullable=True)
    resolution_status = Column(String, nullable=False)
    resolution_reason = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="conflicts")


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(String, primary_key=True, default=lambda: gen_id("DEC"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    decision_type = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    amount = Column(Float, nullable=True)
    instrument = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    decision_factors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed = Column(Integer, default=0)  # 0/1 boolean flag, kept simple for SQLite+Postgres portability
    trigger = Column(String, nullable=True)
    lifecycle_stage = Column(String, nullable=True)
    asset_value = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    existing_exposure = Column(Float, nullable=True)
    maximum_safe_exposure = Column(Float, nullable=True)

    asset = relationship("Asset", back_populates="decisions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: gen_id("ALT"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    related_event_id = Column(String, nullable=True)
    related_decision_id = Column(String, nullable=True)

    asset = relationship("Asset", back_populates="alerts")


class AuditLog(Base):
    """SOURCE: 05_DATABASE_SCHEMA.md — "Immutable-style history of
    important user/system actions." Rows are only ever inserted."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: gen_id("AUD"))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=True)
    actor = Column(String, nullable=False, default="SYSTEM")
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    actor_type = Column(String, nullable=False, default="SYSTEM")
    actor_id = Column(String, nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    source_refs = Column(JSON, nullable=True)
    related_event_id = Column(String, nullable=True)
    related_decision_id = Column(String, nullable=True)
