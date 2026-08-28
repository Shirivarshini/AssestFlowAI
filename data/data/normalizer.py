"""
Normalizer.

Public interface: normalize_records()

Converts raw SourceRecord objects (one per connector "document") into
NormalizedRecord objects (one per field observation), which is the
internal normalized representation described in the Member 4 brief:

    {
      "asset_id": "AST-1001",
      "source": "ERP",
      "source_record_id": "ERP-001",
      "field": "quantity",
      "value": 1000,
      "observed_at": "..."
    }

Design note (assumption, documented per 14_AI_CODING_RULES.md /
16_SOURCE_INDEX.md "source discipline"):
Every key in a SourceRecord's payload becomes its own NormalizedRecord.
This keeps the normalizer generic across all seven simulated source
types without hardcoding per-source field lists, and keeps each field
independently comparable during reconciliation. `currency` fields are
kept as their own normalized field (not merged into the amount) so
that currency mismatches could themselves be flagged as conflicts by
a future extension.
"""

from typing import List

from data.models import SourceRecord, NormalizedRecord


def normalize_records(source_records: List[SourceRecord]) -> List[NormalizedRecord]:
    """
    Flatten a list of raw SourceRecord into a list of NormalizedRecord,
    one per (asset, source, field) observation.
    """
    normalized: List[NormalizedRecord] = []
    for record in source_records:
        for field_name, value in record.payload.items():
            normalized.append(
                NormalizedRecord(
                    asset_id=record.asset_id,
                    source=record.source,
                    source_record_id=record.source_record_id,
                    field=field_name,
                    value=value,
                    observed_at=record.observed_at,
                )
            )
    return normalized
