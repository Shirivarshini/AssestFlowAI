"""Simulated Logistics connector."""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.LOGISTICS.value


def get_records(scenario: str = "healthy") -> list:
    if scenario == "shipment_delay":
        status = "DELAYED"
        delay_days = 12
        location = "IN_TRANSIT - Port of Chennai (held)"
    else:
        status = "IN_TRANSIT"
        delay_days = 0
        location = "IN_TRANSIT - NH48 corridor"

    return [
        SourceRecord(
            source_record_id="LOG-4001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-10T15:00:00Z",
            payload={
                "shipment_status": status,
                "current_location": location,
                "delay_days": delay_days,
                "expected_delivery_date": "2026-01-25",
            },
        ),
    ]
