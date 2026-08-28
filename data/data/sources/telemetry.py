"""Simulated IoT/Telemetry connector."""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.TELEMETRY.value


def get_records(scenario: str = "healthy") -> list:
    if scenario == "conflicting_sources":
        quantity = 920
        production_status = "IN_PROGRESS"
        production_completion_pct = 92
        condition_score = 0.88
    elif scenario == "inventory_deterioration":
        quantity = 1000
        production_status = "COMPLETE"
        production_completion_pct = 100
        condition_score = 0.61
    else:
        quantity = 1000
        production_status = "COMPLETE"
        production_completion_pct = 100
        condition_score = 0.95

    return [
        SourceRecord(
            source_record_id="TEL-6001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-09T06:00:00Z",
            payload={
                "quantity": quantity,
                "production_status": production_status,
                "production_completion_pct": production_completion_pct,
                "condition_score": condition_score,
            },
        ),
    ]
