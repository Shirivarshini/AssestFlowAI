"""
Asset mapper.

Public interface: map_records()

Groups NormalizedRecord entries first by asset_id, then by field, so
the conflict detector can operate on "all observations of one field
for one asset" at a time.
"""

from collections import defaultdict
from typing import Dict, List

from data.models import NormalizedRecord


def map_records(
    records: List[NormalizedRecord],
) -> Dict[str, Dict[str, List[NormalizedRecord]]]:
    """
    Args:
        records: flat list of NormalizedRecord (any assets, any fields)

    Returns:
        { asset_id: { field_name: [NormalizedRecord, ...] } }
    """
    mapped: Dict[str, Dict[str, List[NormalizedRecord]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for rec in records:
        mapped[rec.asset_id][rec.field].append(rec)
    # convert defaultdicts to plain dicts for a predictable, serializable shape
    return {asset_id: dict(fields) for asset_id, fields in mapped.items()}


def get_asset_ids(records: List[NormalizedRecord]) -> List[str]:
    """Convenience helper: distinct asset IDs present in a record list, sorted."""
    return sorted({rec.asset_id for rec in records})
