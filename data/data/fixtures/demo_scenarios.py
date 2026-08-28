"""
Demo scenario fixtures.

Public interface: get_demo_scenario(), list_demo_scenarios()

Implements the four scenarios required for Member 4's fixtures, mapped
to 15_DEMO_SCENARIOS.md:

    healthy_lifecycle     -> Scenario 1 (healthy lifecycle)
    shipment_delay        -> Scenario 2 (shipment delay)
    duplicate_financing   -> Scenario 3 (duplicate financing / over-leverage)
    conflicting_sources   -> Scenario 4 (conflicting sources)

Each fixture bundles:
    - which loader `scenario` key drives the simulated source data
    - the demo asset id
    - a reconciled CanonicalAssetState (computed on demand, not cached,
      so it always reflects the current resolver policy)
    - a deterministic sequence of LifecycleEvent objects the frontend/
      backend/AI layers can play back during a demo

This module does NOT compute financing or risk outcomes -- it only
sets up the data and events. The "Expected" notes from
15_DEMO_SCENARIOS.md are included as plain-text annotations for the
team, not as computed values, since financing/risk are out of Member
4's scope.
"""

from typing import Dict, List

from data.reconciliation import reconcile_asset
from data.event_simulator import create_event, reset_event_counter
from data.sources import DEMO_ASSET_ID
from data.models import LifecycleEvent, CanonicalAssetState

SCENARIO_NAMES = [
    "healthy_lifecycle",
    "shipment_delay",
    "duplicate_financing",
    "conflicting_sources",
]


def _healthy_lifecycle() -> Dict:
    reset_event_counter()
    asset_id = DEMO_ASSET_ID
    state = reconcile_asset(asset_id, scenario="healthy")
    events: List[LifecycleEvent] = []
    # Healthy path: walk the canonical lifecycle forward with no incidents.
    stages = [
        "PURCHASE_ORDER",
        "RAW_MATERIAL",
        "PRODUCTION",
        "FINISHED_GOODS",
        "SHIPMENT",
        "WAREHOUSE",
        "DELIVERY",
        "INVOICE",
        "RECEIVABLE",
        "CASH_REALISATION",
    ]
    transition_events = []
    for i in range(len(stages) - 1):
        transition_events.append(
            {
                "from_stage": stages[i],
                "to_stage": stages[i + 1],
            }
        )

    return {
        "name": "healthy_lifecycle",
        "description": "Scenario 1: PO -> Production -> Shipment -> Delivery -> Invoice -> Receivable -> Cash, no incidents.",
        "asset_id": asset_id,
        "loader_scenario": "healthy",
        "reconciled_state": state,
        "lifecycle_transitions": transition_events,
        "events": events,
        "expected_notes": [
            "No conflicts expected across sources.",
            "Financing instrument transitions as the asset progresses (owned by Members 2/3).",
        ],
    }


def _shipment_delay() -> Dict:
    reset_event_counter()
    asset_id = DEMO_ASSET_ID
    state = reconcile_asset(asset_id, scenario="shipment_delay")
    event = create_event(
        asset_id,
        "SHIPMENT_DELAY",
        from_stage="SHIPMENT",
        to_stage="SHIPMENT",
        severity="MEDIUM",
        payload={"allow_reversal": True, "delay_days": 12, "reason": "Port congestion"},
    )
    return {
        "name": "shipment_delay",
        "description": "Scenario 2: SHIPMENT_DELAY event triggered on an in-transit asset.",
        "asset_id": asset_id,
        "loader_scenario": "shipment_delay",
        "reconciled_state": state,
        "lifecycle_transitions": [],
        "events": [event],
        "expected_notes": [
            "Risk should increase (owned by Member 3's risk engine).",
            "Expected realization timing changes.",
            "Financing should be reassessed; reduction/maintain/transition decision appears.",
            "An alert should be created downstream.",
        ],
    }


def _duplicate_financing() -> Dict:
    reset_event_counter()
    asset_id = DEMO_ASSET_ID
    state = reconcile_asset(asset_id, scenario="duplicate_financing")
    return {
        "name": "duplicate_financing",
        "description": "Scenario 3: existing financing exposure is already close to safe exposure; a new request should be blocked or reduced.",
        "asset_id": asset_id,
        "loader_scenario": "duplicate_financing",
        "reconciled_state": state,
        "lifecycle_transitions": [],
        "events": [],
        "expected_notes": [
            "Existing exposure is high (see reconciled_state.financial_state.outstanding_amount).",
            "The financing engine (Member 3) is expected to block or reduce a new request "
            "and surface an over-leverage alert; Member 4 only supplies the exposure data.",
        ],
    }


def _conflicting_sources() -> Dict:
    reset_event_counter()
    asset_id = DEMO_ASSET_ID
    state = reconcile_asset(asset_id, scenario="conflicting_sources")
    event = create_event(
        asset_id,
        "DATA_CONFLICT",
        severity="MEDIUM",
        payload={
            "conflicting_fields": [
                c.field
                for c in state.conflicts
                if c.resolution_status in ("QUALIFIED", "RESOLVED")
                and len({o.value for o in c.observations if o.value is not None}) > 1
            ]
        },
    )
    return {
        "name": "conflicting_sources",
        "description": "Scenario 4: ERP, warehouse and telemetry disagree on quantity/production status.",
        "asset_id": asset_id,
        "loader_scenario": "conflicting_sources",
        "reconciled_state": state,
        "lifecycle_transitions": [],
        "events": [event],
        "expected_notes": [
            "Conflict(s) visible in reconciled_state.conflicts with full source evidence.",
            "Canonical state selected/qualified with reduced confidence "
            "(see reconciled_state.state_confidence).",
            "Financing should be reassessed if the conflict is material (owned by Member 3).",
        ],
    }


_BUILDERS = {
    "healthy_lifecycle": _healthy_lifecycle,
    "shipment_delay": _shipment_delay,
    "duplicate_financing": _duplicate_financing,
    "conflicting_sources": _conflicting_sources,
}


def list_demo_scenarios() -> List[str]:
    return list(SCENARIO_NAMES)


def get_demo_scenario(name: str) -> Dict:
    """
    Return a fully-built demo scenario bundle.

    Raises:
        KeyError: if `name` is not one of the four supported scenarios.
    """
    if name not in _BUILDERS:
        raise KeyError(
            f"Unknown demo scenario '{name}'. Available: {list_demo_scenarios()}"
        )
    return _BUILDERS[name]()
