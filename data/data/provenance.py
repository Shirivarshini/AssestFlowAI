"""
Provenance.

Public interface: get_provenance()

Builds the "which source(s) produced this canonical value" record for
each field, per 09_RECONCILIATION_ENGINE.md rule 3: "Every canonical
value should have provenance," and 05_DATABASE_SCHEMA.md's design
rule: "Preserve source evidence and separately store the canonical
state."
"""

from typing import List

from data.models import DataConflict, FieldProvenance


def get_provenance(conflict: DataConflict) -> FieldProvenance:
    """
    Derive a FieldProvenance entry from a resolved DataConflict.

    - For NO_CONFLICT / RESOLVED: sources listed are those whose value
      matches the canonical value.
    - For QUALIFIED: the single most-reliable source that was used.
    - For NEEDS_REVIEW: no sources (nothing was safely usable).
    """
    if conflict.resolution_status == "NEEDS_REVIEW":
        return FieldProvenance(
            field=conflict.field,
            value=None,
            sources=[],
            source_record_ids=[],
            resolution_status=conflict.resolution_status,
            confidence=conflict.confidence,
        )

    contributing = [
        obs
        for obs in conflict.observations
        if obs.value is not None and _matches(obs.value, conflict.canonical_value)
    ]
    # QUALIFIED resolutions are attributed to exactly the source that won the
    # reliability tie-break, even if another source happens to share the value.
    if conflict.resolution_status == "QUALIFIED" and contributing:
        contributing = [min(contributing, key=lambda o: o.reliability_rank)]

    return FieldProvenance(
        field=conflict.field,
        value=conflict.canonical_value,
        sources=sorted({o.source for o in contributing}),
        source_record_ids=sorted({o.source_record_id for o in contributing}),
        resolution_status=conflict.resolution_status,
        confidence=conflict.confidence,
    )


def _matches(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    return a == b


def get_provenance_for_asset(conflicts: List[DataConflict]) -> List[FieldProvenance]:
    """Build provenance entries for every field of one asset."""
    return [get_provenance(c) for c in conflicts]
