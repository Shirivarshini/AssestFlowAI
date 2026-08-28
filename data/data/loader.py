"""
Source data loader.

Public interface: load_source_records()

Aggregates raw SourceRecord objects from every simulated connector in
data/sources/. This is the single entry point the rest of the pipeline
(and eventually the backend) uses to pull "raw" data before
normalization.
"""

from typing import List, Optional

from data.models import SourceRecord
from data.sources import (
    erp,
    purchase_orders,
    invoices,
    logistics,
    warehouse,
    telemetry,
    financing,
)

_SOURCE_MODULES = [
    erp,
    purchase_orders,
    invoices,
    logistics,
    warehouse,
    telemetry,
    financing,
]


def load_source_records(
    scenario: str = "healthy", sources: Optional[List[str]] = None
) -> List[SourceRecord]:
    """
    Load raw simulated source records for the given demo scenario.

    Args:
        scenario: which deterministic demo dataset variant to load
            (e.g. "healthy", "shipment_delay", "conflicting_sources",
            "duplicate_financing"). Unknown scenario names are passed
            through to each connector, which falls back to its default
            ("healthy") behavior for fields it doesn't vary.
        sources: optional allow-list of SourceType values (e.g.
            ["ERP", "WAREHOUSE"]) to restrict which connectors are
            queried. Defaults to all sources.

    Returns:
        A flat list of SourceRecord (raw, pre-normalization).
    """
    records: List[SourceRecord] = []
    for module in _SOURCE_MODULES:
        module_source_name = module.SOURCE
        if sources is not None and module_source_name not in sources:
            continue
        records.extend(module.get_records(scenario=scenario))
    return records
