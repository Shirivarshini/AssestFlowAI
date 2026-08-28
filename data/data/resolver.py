"""
Conflict resolver.

Public interface: resolve_field()

=====================================================================
PROTOTYPE POLICY -- NOT AN OFFICIAL CHALLENGE FORMULA
=====================================================================
01_PROBLEM_STATEMENT.md and 09_RECONCILIATION_ENGINE.md require that
conflicts be detected, evidence be preserved, and a canonical value be
selected with an associated confidence -- but neither document
prescribes *how* to pick the canonical value. The policy below is this
prototype's implementation choice, clearly labeled as such so it is
never mistaken for an official requirement (per 16_SOURCE_INDEX.md
"source discipline").

Policy, in order of precedence:
  1. No usable evidence at all           -> NEEDS_REVIEW, confidence 0.0
  2. Only one source reports the field   -> NO_CONFLICT, confidence 0.95
  3. All sources agree                   -> NO_CONFLICT, confidence 0.95
  4. A strict majority of sources agree  -> RESOLVED using the majority
                                             value, confidence 0.80
  5. No majority (values disagree with
     no majority winner)                 -> QUALIFIED using the most
                                             reliable source's value,
                                             confidence 0.55

Source reliability ranking (lower = more trusted), used only as a
tie-breaker in case 5. This ordering is a documented assumption, not
part of the official challenge: ERP and Warehouse are treated as
closer to physical ground-truth for this prototype than Telemetry,
which can be noisy or partially reported mid-process.
"""

from collections import Counter
from typing import Dict, List, Optional

from data.models import (
    NormalizedRecord,
    SourceObservation,
    DataConflict,
    ResolutionStatus,
)

RELIABILITY_RANK = {
    "ERP": 1,
    "WAREHOUSE": 2,
    "PURCHASE_ORDER": 3,
    "INVOICE": 4,
    "FINANCING": 5,
    "LOGISTICS": 6,
    "TELEMETRY": 7,
}


def _reliability_rank(source: str) -> int:
    return RELIABILITY_RANK.get(source, 99)


def _to_observation(rec: NormalizedRecord) -> SourceObservation:
    return SourceObservation(
        source=rec.source,
        source_record_id=rec.source_record_id,
        value=rec.value,
        observed_at=rec.observed_at,
        reliability_rank=_reliability_rank(rec.source),
    )


def resolve_field(
    asset_id: str, field: str, observations: List[NormalizedRecord]
) -> DataConflict:
    """
    Resolve one field's observations for one asset into a DataConflict
    record (used even when there was no conflict, for a uniform shape
    and full provenance/audit trail -- 09_RECONCILIATION_ENGINE.md rule
    3: "Every canonical value should have provenance.").
    """
    obs_list = [_to_observation(r) for r in observations]
    non_null = [o for o in obs_list if o.value is not None]

    # sorted for deterministic "most reliable disagreeing pair" reporting
    obs_list_sorted = sorted(obs_list, key=lambda o: o.reliability_rank)

    if not non_null:
        return DataConflict(
            asset_id=asset_id,
            field=field,
            observations=obs_list,
            source_a=None,
            source_b=None,
            value_a=None,
            value_b=None,
            resolution_status=ResolutionStatus.NEEDS_REVIEW.value,
            resolution_reason="No source reported a non-null value for this field.",
            canonical_value=None,
            confidence=0.0,
        )

    values = [o.value for o in non_null]
    value_counts = Counter(_canonical_key(v) for v in values)
    distinct_keys = list(value_counts.keys())

    source_a = obs_list_sorted[0].source if len(obs_list_sorted) >= 1 else None
    source_b = obs_list_sorted[1].source if len(obs_list_sorted) >= 2 else None
    value_a = obs_list_sorted[0].value if len(obs_list_sorted) >= 1 else None
    value_b = obs_list_sorted[1].value if len(obs_list_sorted) >= 2 else None

    # Case: single source reported this field
    if len(non_null) == 1:
        return DataConflict(
            asset_id=asset_id,
            field=field,
            observations=obs_list,
            source_a=source_a,
            source_b=None,
            value_a=value_a,
            value_b=None,
            resolution_status=ResolutionStatus.NO_CONFLICT.value,
            resolution_reason=f"Only {source_a} reports this field; no other source to compare against.",
            canonical_value=value_a,
            confidence=0.95,
        )

    # Case: all sources agree
    if len(distinct_keys) == 1:
        return DataConflict(
            asset_id=asset_id,
            field=field,
            observations=obs_list,
            source_a=source_a,
            source_b=source_b,
            value_a=value_a,
            value_b=value_b,
            resolution_status=ResolutionStatus.NO_CONFLICT.value,
            resolution_reason=f"All {len(non_null)} reporting sources agree.",
            canonical_value=non_null[0].value,
            confidence=0.95,
        )

    # Disagreement: look for a strict majority
    winning_key, winning_count = value_counts.most_common(1)[0]
    total = len(non_null)
    is_strict_majority = winning_count > total / 2

    if is_strict_majority:
        canonical_value = next(
            o.value for o in non_null if _canonical_key(o.value) == winning_key
        )
        agreeing_sources = sorted(
            {o.source for o in non_null if _canonical_key(o.value) == winning_key}
        )
        disagreeing_sources = sorted(
            {o.source for o in non_null if _canonical_key(o.value) != winning_key}
        )
        return DataConflict(
            asset_id=asset_id,
            field=field,
            observations=obs_list,
            source_a=source_a,
            source_b=source_b,
            value_a=value_a,
            value_b=value_b,
            resolution_status=ResolutionStatus.RESOLVED.value,
            resolution_reason=(
                f"Majority agreement ({winning_count}/{total}) among {agreeing_sources}; "
                f"disagreement from {disagreeing_sources}."
            ),
            canonical_value=canonical_value,
            confidence=0.80,
        )

    # No majority: fall back to most reliable source, but flag as qualified
    most_reliable = obs_list_sorted[0]
    all_sources = sorted({o.source for o in non_null})
    return DataConflict(
        asset_id=asset_id,
        field=field,
        observations=obs_list,
        source_a=source_a,
        source_b=source_b,
        value_a=value_a,
        value_b=value_b,
        resolution_status=ResolutionStatus.QUALIFIED.value,
        resolution_reason=(
            f"No majority among disagreeing sources {all_sources}; qualified using most "
            f"reliable source ({most_reliable.source}) per prototype reliability ranking. "
            f"This is a prototype policy, not an official challenge rule."
        ),
        canonical_value=most_reliable.value,
        confidence=0.55,
    )


def _canonical_key(value):
    """Make a hashable, tolerance-aware key so 1000 and 1000.0 count as equal."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def resolve_asset_fields(
    asset_id: str, asset_fields: Dict[str, List[NormalizedRecord]]
) -> List[DataConflict]:
    """Resolve every field for one asset. Returns a list of DataConflict (one per field)."""
    return [resolve_field(asset_id, field, obs) for field, obs in asset_fields.items()]
