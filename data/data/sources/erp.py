"""
Simulated ERP connector.

ERP is treated as a moderately reliable source for production status
and quantity (see resolver.py for the reliability ranking policy).
"""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.ERP.value


def get_records(scenario: str = "healthy") -> list:
    """
    Return deterministic simulated ERP records for a given demo scenario.

    Supported scenarios: "healthy", "shipment_delay", "conflicting_sources".
    Unknown scenarios fall back to "healthy" so callers always get data.
    """
    if scenario == "conflicting_sources":
        quantity = 1000
        production_status = "COMPLETE"
    else:
        quantity = 1000
        production_status = "COMPLETE"

    return [
        SourceRecord(
            source_record_id="ERP-001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-05T09:00:00Z",
            payload={
                "product_name": "Industrial Copper Coils",
                "quantity": quantity,
                "unit": "KG",
                "production_status": production_status,
                "unit_reference_value": 450.0,
                "currency": "INR",
            },
        ),
    ]
