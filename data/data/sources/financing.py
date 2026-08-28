"""
Simulated Financing / financial-institution connector.

Note: this module only emits observed financing facts as source
records (e.g. "a lender reports this outstanding balance"). It does
NOT compute financing eligibility, safe exposure, or recommendations
-- that is explicitly out of Member 4's scope and belongs to the
financing engine (07_FINANCING_ENGINE.md), owned by Member 3.
"""

from data.models import SourceRecord, SourceType
from data.sources import DEMO_ASSET_ID

SOURCE = SourceType.FINANCING.value


def get_records(scenario: str = "healthy") -> list:
    if scenario == "duplicate_financing":
        outstanding_amount = 1150000.0
        instrument = "IN_TRANSIT_FINANCING"
        status = "ACTIVE"
    else:
        outstanding_amount = 400000.0
        instrument = "IN_TRANSIT_FINANCING"
        status = "ACTIVE"

    return [
        SourceRecord(
            source_record_id="FIN-7001",
            source=SOURCE,
            asset_id=DEMO_ASSET_ID,
            observed_at="2026-01-11T11:00:00Z",
            payload={
                "instrument": instrument,
                "outstanding_amount": outstanding_amount,
                "currency": "INR",
                "status": status,
                "lender_id": "LENDER-09",
            },
        ),
    ]
