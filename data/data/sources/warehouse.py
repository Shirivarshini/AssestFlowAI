"""Simulated Warehouse connector."""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.WAREHOUSE.value


def get_records(scenario: str = "healthy") -> list:
    if scenario == "conflicting_sources":
        quantity = 950
        production_status = "COMPLETE"
        condition_score = 0.92
    else:
        quantity = 1000
        production_status = "COMPLETE"
        condition_score = 0.97

    return [
        SourceRecord(
            source_record_id="WH-5001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-08T08:00:00Z",
            payload={
                "quantity": quantity,
                "production_status": production_status,
                "condition_score": condition_score,
                "warehouse_status": "NORMAL",
            },
        ),
    ]
