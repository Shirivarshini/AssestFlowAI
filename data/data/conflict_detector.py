"""
Conflict detector.

Public interface: detect_conflicts()

For one asset's field -> [NormalizedRecord] mapping (as produced by
mapper.py), determine whether the sources agree. This module only
DETECTS disagreement; it does not decide how to resolve it (that is
resolver.py's job), per the documented reconciliation pipeline in
09_RECONCILIATION_ENGINE.md:

    normalize -> map -> compare -> detect conflicts -> resolve/qualify
    -> canonical state -> confidence -> audit trail

Rule followed (09_RECONCILIATION_ENGINE.md):
"Never discard conflicting source evidence." All observations are
always returned, whether or not they conflict.
"""

from typing import Dict, List

from data.models import NormalizedRecord


def _values_agree(a, b) -> bool:
    """
    Equality check used to decide whether two observed values conflict.

    Numeric values are compared with a small relative tolerance so that
    e.g. 1000 vs 1000.0 is not treated as a conflict, while 1000 vs 950
    (a real discrepancy) is. This is a PROTOTYPE POLICY, not an official
    requirement -- the problem statement does not specify a tolerance.
    """
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return True
        denom = max(abs(a), abs(b), 1e-9)
        return abs(a - b) / denom < 0.001
    return a == b


def detect_field_conflict(field_observations: List[NormalizedRecord]) -> Dict:
    """
    Given all observations of a single field for a single asset, decide
    whether they conflict.

    Returns a dict:
        {
          "field": str,
          "status": "NO_CONFLICT" | "CONFLICT" | "NEEDS_REVIEW",
          "observations": [NormalizedRecord, ...],
        }

    "NEEDS_REVIEW" is used only when there is no usable evidence at all
    (e.g. every observed value is None) -- see 08_RISK_ENGINE.md safety
    principle: never silently increase confidence from absent data.
    """
    if not field_observations:
        return {"field": None, "status": "NEEDS_REVIEW", "observations": []}

    field_name = field_observations[0].field
    non_null = [obs for obs in field_observations if obs.value is not None]

    if not non_null:
        return {
            "field": field_name,
            "status": "NEEDS_REVIEW",
            "observations": field_observations,
        }

    distinct_values = []
    for obs in non_null:
        if not any(_values_agree(obs.value, v) for v in distinct_values):
            distinct_values.append(obs.value)

    status = "NO_CONFLICT" if len(distinct_values) <= 1 else "CONFLICT"
    return {"field": field_name, "status": status, "observations": field_observations}


def detect_conflicts(
    asset_fields: Dict[str, List[NormalizedRecord]],
) -> Dict[str, Dict]:
    """
    Args:
        asset_fields: { field_name: [NormalizedRecord, ...] } for ONE asset
            (i.e. mapped_records[asset_id] from mapper.map_records()).

    Returns:
        { field_name: detect_field_conflict(...) result }
    """
    return {
        field_name: detect_field_conflict(obs)
        for field_name, obs in asset_fields.items()
    }
