import unittest

from data.event_simulator import (
    create_event,
    reset_event_counter,
    UnsupportedEventTypeError,
)
from data.sources import DEMO_ASSET_ID
from data.models import SUPPORTED_EVENT_TYPES


class TestEventSimulator(unittest.TestCase):
    def setUp(self):
        reset_event_counter()

    def test_all_nine_event_types_supported(self):
        self.assertEqual(len(SUPPORTED_EVENT_TYPES), 9)
        for event_type in SUPPORTED_EVENT_TYPES:
            reset_event_counter()
            event = create_event(DEMO_ASSET_ID, event_type)
            self.assertEqual(event.event_type, event_type)

    def test_invalid_event_type_raises(self):
        with self.assertRaises(UnsupportedEventTypeError):
            create_event(DEMO_ASSET_ID, "NOT_A_REAL_EVENT")

    def test_event_ids_are_deterministic_and_increment(self):
        e1 = create_event(DEMO_ASSET_ID, "SHIPMENT_DELAY")
        e2 = create_event(DEMO_ASSET_ID, "DELIVERY_CONFIRMED")
        self.assertEqual(e1.event_id, "EVT-0001")
        self.assertEqual(e2.event_id, "EVT-0002")

    def test_valid_forward_transition_allowed(self):
        event = create_event(
            DEMO_ASSET_ID,
            "DELIVERY_CONFIRMED",
            from_stage="SHIPMENT",
            to_stage="DELIVERY",
        )
        self.assertEqual(event.from_stage, "SHIPMENT")
        self.assertEqual(event.to_stage, "DELIVERY")

    def test_invalid_backward_transition_rejected(self):
        with self.assertRaises(ValueError):
            create_event(
                DEMO_ASSET_ID,
                "DELIVERY_CONFIRMED",
                from_stage="DELIVERY",
                to_stage="SHIPMENT",
            )

    def test_backward_transition_allowed_with_explicit_override(self):
        event = create_event(
            DEMO_ASSET_ID,
            "DELIVERY_CONFIRMED",
            from_stage="DELIVERY",
            to_stage="SHIPMENT",
            payload={"allow_reversal": True, "reason": "correction"},
        )
        self.assertEqual(event.to_stage, "SHIPMENT")

    def test_default_severity_applied(self):
        event = create_event(DEMO_ASSET_ID, "INVENTORY_DETERIORATION")
        self.assertEqual(event.severity, "HIGH")

    def test_invalid_severity_rejected(self):
        with self.assertRaises(ValueError):
            create_event(DEMO_ASSET_ID, "SHIPMENT_DELAY", severity="SUPER_BAD")

    def test_same_stage_transition_rejected_without_override(self):
        with self.assertRaises(ValueError):
            create_event(
                DEMO_ASSET_ID,
                "SHIPMENT_DELAY",
                from_stage="SHIPMENT",
                to_stage="SHIPMENT",
            )


if __name__ == "__main__":
    unittest.main()
