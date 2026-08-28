"""Simulated Invoice connector."""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.INVOICE.value


def get_records(scenario: str = "healthy") -> list:
    if scenario in ("healthy_late_stage", "delivery_to_invoice"):
        status = "VERIFIED"
    else:
        status = "NOT_ISSUED"

    return [
        SourceRecord(
            source_record_id="INV-3001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-20T12:00:00Z",
            payload={
                "invoice_number": "INV-3001",
                "invoice_status": status,
                "invoice_amount": 450000.0,
                "currency": "INR",
                "invoice_date": "2026-01-20",
            },
        ),
    ]
