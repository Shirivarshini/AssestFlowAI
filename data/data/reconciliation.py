"""
Reconciliation orchestrator.

Public interface: reconcile_asset()

Runs the full pipeline described in 09_RECONCILIATION_ENGINE.md:

    SOURCE RECORDS
    -> normalize
    -> map to asset
    -> compare fields
    -> detect conflicts
    -> score source reliability
    -> resolve or qualify conflict
    -> canonical state
    -> confidence
    -> audit trail

This is the single function the (future) backend layer is expected to
call to get a reconciled, provenance-backed view of one asset.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.mapper import map_records
from data.conflict_detector import detect_conflicts
from data.resolver import resolve_asset_fields
from data.provenance import get_provenance_for_asset
from data.models import CanonicalAssetState, DataConflict

# ---------------------------------------------------------------------------
# Assumption (documented per 16_SOURCE_INDEX.md "source discipline"):
# 05_DATABASE_SCHEMA.md defines asset_states with single
# physical_state / financial_state / contractual_state fields, but does
# not specify their shape. This prototype represents each as a dict of
# the relevant resolved fields, grouped by which bucket they logically
# belong to. This is an implementation choice, not an official rule.
# ---------------------------------------------------------------------------

PHYSICAL_FIELDS = {
    "quantity",
    "unit",
    "product_name",
    "production_status",
    "production_completion_pct",
    "condition_score",
    "warehouse_status",
    "shipment_status",
    "current_location",
    "delay_days",
    "expected_delivery_date",
}

FINANCIAL_FIELDS = {
    "unit_reference_value",
    "instrument",
    "outstanding_amount",
    "status",
    "lender_id",
    "invoice_amount",
}

CONTRACTUAL_FIELDS = {
    "po_number",
    "buyer_id",
    "contractual_status",
    "order_date",
    "invoice_number",
    "invoice_status",
    "invoice_date",
    "currency",
}


def _bucket(field_values: Dict, allowed_fields: set) -> Dict:
    return {k: v for k, v in field_values.items() if k in allowed_fields}


def reconcile_asset(asset_id: str, scenario: str = "healthy") -> CanonicalAssetState:
    """
    Run the full reconciliation pipeline for a single asset.

    Args:
        asset_id: e.g. "AST-1001"
        scenario: which deterministic simulated dataset to load
            (see data/loader.py and data/fixtures/demo_scenarios.py)

    Returns:
        CanonicalAssetState with resolved field values, provenance,
        the full conflict/audit trail, and an overall confidence score.
    """
    raw_records = load_source_records(scenario=scenario)
    normalized = normalize_records(raw_records)
    mapped = map_records(normalized)

    asset_fields = mapped.get(asset_id, {})
    if not asset_fields:
        return CanonicalAssetState(
            asset_id=asset_id,
            physical_state=None,
            financial_state=None,
            contractual_state=None,
            condition_score=None,
            state_confidence=0.0,
            effective_at=_now(),
            source="RECONCILIATION_ENGINE",
            field_values={},
            provenance=[],
            conflicts=[],
            status="NEEDS_REVIEW",
        )

    # detect (informational; resolver re-derives status but this keeps the
    # documented pipeline step explicit and independently inspectable)
    detect_conflicts(asset_fields)

    conflicts: List[DataConflict] = resolve_asset_fields(asset_id, asset_fields)
    provenance = get_provenance_for_asset(conflicts)

    field_values = {c.field: c.canonical_value for c in conflicts}
    condition_score = field_values.get("condition_score")

    needs_review_fields = [
        c for c in conflicts if c.resolution_status == "NEEDS_REVIEW"
    ]
    qualified_fields = [c for c in conflicts if c.resolution_status == "QUALIFIED"]

    # Overall confidence: mean of per-field confidences (prototype policy,
    # not an official formula -- 07_FINANCING_ENGINE.md / 08_RISK_ENGINE.md
    # explicitly leave formulas as implementation decisions).
    confidences = [c.confidence for c in conflicts]
    state_confidence = (
        round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    )

    # Safety principle (08_RISK_ENGINE.md): low confidence / unresolved
    # data should surface for review rather than being silently accepted.
    status = "NEEDS_REVIEW" if needs_review_fields else "OK"

    canonical_state = CanonicalAssetState(
        asset_id=asset_id,
        physical_state=_bucket(field_values, PHYSICAL_FIELDS) or None,
        financial_state=_bucket(field_values, FINANCIAL_FIELDS) or None,
        contractual_state=_bucket(field_values, CONTRACTUAL_FIELDS) or None,
        condition_score=condition_score,
        state_confidence=state_confidence,
        effective_at=_now(),
        source="RECONCILIATION_ENGINE",
        field_values=field_values,
        provenance=provenance,
        conflicts=conflicts,
        status=status,
    )
    return canonical_state


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reconcile_all_assets(scenario: str = "healthy") -> Dict[str, CanonicalAssetState]:
    """Reconcile every asset present in the loaded scenario's source data."""
    raw_records = load_source_records(scenario=scenario)
    normalized = normalize_records(raw_records)
    mapped = map_records(normalized)
    return {
        asset_id: reconcile_asset(asset_id, scenario=scenario)
        for asset_id in mapped.keys()
    }
