"""
Reconciliation service.

SOURCE: 09_RECONCILIATION_ENGINE.md pipeline: normalize -> map to asset ->
compare fields -> detect conflicts -> score source reliability -> resolve
or qualify -> canonical state -> confidence -> audit trail.

Member 4 owns ingestion of raw source_records; this service only performs
the comparison/conflict-detection/canonical-selection step so both teams
share one reconciliation implementation, per the GPT instructions
("Do not implement another ingestion system inside your backend").
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.enums import ConflictResolutionStatus
from app.models import Asset, SourceRecord, DataConflict, AssetState
from app.services import audit_service

# ASSUMPTION: relative reliability used to pick a canonical value when
# sources disagree. Not specified by source docs.
SOURCE_RELIABILITY = {
    "ERP": 0.9,
    "WAREHOUSE": 0.85,
    "LOGISTICS": 0.8,
    "INVOICE": 0.85,
    "TELEMETRY": 0.7,
    "FINANCIAL_INSTITUTION": 0.9,
    "PURCHASE_ORDER": 0.9,
}


def run_reconciliation(db: Session, asset: Asset) -> dict:
    records = db.query(SourceRecord).filter(SourceRecord.asset_id == asset.id).all()

    by_field: dict[str, list[SourceRecord]] = defaultdict(list)
    for r in records:
        by_field[r.field].append(r)

    canonical_state: dict[str, str] = {}
    conflicts_created: list[DataConflict] = []
    min_confidence = 1.0

    for field, recs in by_field.items():
        distinct_values = {r.value for r in recs}
        if len(distinct_values) <= 1:
            if recs:
                canonical_state[field] = recs[0].value
            continue

        # Conflict: pick canonical by highest source reliability.
        ranked = sorted(recs, key=lambda r: SOURCE_RELIABILITY.get(r.source_name, 0.5), reverse=True)
        best, second = ranked[0], ranked[1]
        confidence = round(
            SOURCE_RELIABILITY.get(best.source_name, 0.5)
            - 0.1 * (len(distinct_values) - 1),
            2,
        )
        confidence = max(0.3, confidence)
        min_confidence = min(min_confidence, confidence)
        canonical_state[field] = best.value

        status = (
            ConflictResolutionStatus.RESOLVED.value
            if confidence >= 0.6
            else ConflictResolutionStatus.QUALIFIED.value
        )

        conflict = DataConflict(
            asset_id=asset.id,
            source_a=best.source_name,
            source_b=second.source_name,
            field=field,
            value_a=best.value,
            value_b=second.value,
            resolution_status=status,
            resolution_reason=f"Selected {best.source_name} (reliability-ranked) over {second.source_name}.",
            confidence=confidence,
        )
        db.add(conflict)
        conflicts_created.append(conflict)

    if canonical_state:
        state = AssetState(
            asset_id=asset.id,
            physical_state=canonical_state.get("physical_state"),
            financial_state=canonical_state.get("financial_state"),
            contractual_state=canonical_state.get("contractual_state"),
            state_confidence=min_confidence if by_field else 1.0,
            source="RECONCILIATION_ENGINE",
        )
        db.add(state)

    db.commit()
    for c in conflicts_created:
        db.refresh(c)

    audit_service.record(
        db, "RECONCILIATION_RUN", asset.id,
        details={"fields_processed": list(by_field.keys()), "conflicts_found": len(conflicts_created)},
    )

    return {
        "asset_id": asset.id,
        "canonical_state": canonical_state,
        "conflicts": conflicts_created,
        "confidence": min_confidence if by_field else 1.0,
    }


def list_conflicts(db: Session, asset_id: str) -> list[DataConflict]:
    return (
        db.query(DataConflict)
        .filter(DataConflict.asset_id == asset_id)
        .order_by(DataConflict.created_at.desc())
        .all()
    )
