"""Simulated Purchase Order connector."""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.PURCHASE_ORDER.value


def get_records(scenario: str = "healthy") -> list:
    return [
        SourceRecord(
            source_record_id="PO-2001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-02T10:00:00Z",
            payload={
                "po_number": "PO-2001",
                "buyer_id": "BUYER-77",
                "quantity": 1000,
                "unit": "KG",
                "contractual_status": "CONFIRMED",
                "order_date": "2026-01-02",
                "currency": "INR",
            },
        ),
    ]
