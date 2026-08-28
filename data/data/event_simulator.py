"""
Event simulator.

Public interface: create_event()

Per the Member 4 brief: "The simulator creates events. It does NOT
calculate financing decisions. The future backend/AI layers will
consume these events." This module is intentionally dumb: it validates
and packages an event; it never touches risk or financing logic
(those belong to Members 3's engines per 07_FINANCING_ENGINE.md /
08_RISK_ENGINE.md, which are explicitly out of Member 4 scope).

Supported event types (12_EVENT_SYSTEM.md / project GPT instructions):
    PRODUCTION_DELAY, SHIPMENT_DELAY, INVENTORY_DETERIORATION,
    WAREHOUSE_EXCEPTION, DELIVERY_CONFIRMED, BUYER_RISK_CHANGED,
    RECEIVABLE_DELAY, INVOICE_VERIFIED, DATA_CONFLICT
"""

from datetime import datetime, timezone
from typing import Optional

from data.models import LifecycleEvent, SUPPORTED_EVENT_TYPES, LIFECYCLE_ORDER


class UnsupportedEventTypeError(ValueError):
    """Raised when create_event() is asked for an event type outside the
    documented supported set."""


# Deterministic, monotonically increasing counter so repeated demo runs in
# the same process produce stable, inspectable event IDs. Reset with
# reset_event_counter() between test cases / demo scenarios if needed.
_event_counter = 0


def reset_event_counter() -> None:
    global _event_counter
    _event_counter = 0


def _next_event_id() -> str:
    global _event_counter
    _event_counter += 1
    return f"EVT-{_event_counter:04d}"


# Default severities per event type (prototype policy -- the official
# problem statement lists these as "important events" but does not assign
# severities; this is an implementation default and can be overridden by
# passing severity= explicitly).
_DEFAULT_SEVERITY = {
    "PRODUCTION_DELAY": "MEDIUM",
    "SHIPMENT_DELAY": "MEDIUM",
    "INVENTORY_DETERIORATION": "HIGH",
    "WAREHOUSE_EXCEPTION": "MEDIUM",
    "DELIVERY_CONFIRMED": "LOW",
    "BUYER_RISK_CHANGED": "HIGH",
    "RECEIVABLE_DELAY": "MEDIUM",
    "INVOICE_VERIFIED": "LOW",
    "DATA_CONFLICT": "MEDIUM",
}

_VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def create_event(
    asset_id: str,
    event_type: str,
    from_stage: Optional[str] = None,
    to_stage: Optional[str] = None,
    source_id: str = "EVENT_SIMULATOR",
    severity: Optional[str] = None,
    payload: Optional[dict] = None,
    event_time: Optional[str] = None,
) -> LifecycleEvent:
    """
    Create a single deterministic, structured material event.

    Raises:
        UnsupportedEventTypeError: if event_type is not one of the nine
            documented supported types.
        ValueError: if a lifecycle stage transition is given but is not
            forward-moving in the canonical lifecycle order (unless
            explicitly allowed via payload={"allow_reversal": True},
            matching 06_ASSET_LIFECYCLE.md: "The engine should reject
            impossible transitions unless a demo scenario explicitly
            models a correction/reversal.")
        ValueError: if `severity` is supplied but not one of
            LOW/MEDIUM/HIGH/CRITICAL.
    """
    if event_type not in SUPPORTED_EVENT_TYPES:
        raise UnsupportedEventTypeError(
            f"Unsupported event_type '{event_type}'. Supported types: "
            f"{sorted(SUPPORTED_EVENT_TYPES)}"
        )

    payload = dict(payload or {})

    if from_stage is not None and to_stage is not None:
        allow_reversal = bool(payload.get("allow_reversal", False))
        if from_stage not in LIFECYCLE_ORDER or to_stage not in LIFECYCLE_ORDER:
            raise ValueError(f"Unknown lifecycle stage(s): {from_stage} -> {to_stage}")
        if (
            LIFECYCLE_ORDER.index(to_stage) <= LIFECYCLE_ORDER.index(from_stage)
            and not allow_reversal
        ):
            raise ValueError(
                f"Rejected transition {from_stage} -> {to_stage}: not forward-moving in the "
                f"canonical lifecycle and 'allow_reversal' was not set. "
                f"(06_ASSET_LIFECYCLE.md: invalid transitions must be rejected unless a demo "
                f"scenario explicitly models a correction/reversal.)"
            )

    resolved_severity = (
        severity
        if severity is not None
        else _DEFAULT_SEVERITY.get(event_type, "MEDIUM")
    )
    if resolved_severity not in _VALID_SEVERITIES:
        raise ValueError(
            f"Invalid severity '{resolved_severity}'. Must be one of {sorted(_VALID_SEVERITIES)}"
        )

    return LifecycleEvent(
        event_id=_next_event_id(),
        asset_id=asset_id,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        event_time=event_time or _now(),
        source_id=source_id,
        severity=resolved_severity,
        payload=payload,
    )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
