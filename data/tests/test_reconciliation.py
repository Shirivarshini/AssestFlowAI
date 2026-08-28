import unittest

from data.reconciliation import reconcile_asset, reconcile_all_assets
from data.sources import DEMO_ASSET_ID


class TestReconciliation(unittest.TestCase):
    def test_healthy_scenario_status_ok(self):
        state = reconcile_asset(DEMO_ASSET_ID, scenario="healthy")
        self.assertEqual(state.status, "OK")
        self.assertGreaterEqual(state.state_confidence, 0.9)

    def test_conflicting_sources_reduces_confidence(self):
        healthy = reconcile_asset(DEMO_ASSET_ID, scenario="healthy")
        conflicting = reconcile_asset(DEMO_ASSET_ID, scenario="conflicting_sources")
        self.assertLess(conflicting.state_confidence, healthy.state_confidence)

    def test_physical_financial_contractual_buckets_populated(self):
        state = reconcile_asset(DEMO_ASSET_ID, scenario="healthy")
        self.assertIsNotNone(state.physical_state)
        self.assertIsNotNone(state.financial_state)
        self.assertIsNotNone(state.contractual_state)
        self.assertIn("quantity", state.physical_state)
        self.assertIn("po_number", state.contractual_state)

    def test_unknown_asset_returns_needs_review(self):
        state = reconcile_asset("AST-9999", scenario="healthy")
        self.assertEqual(state.status, "NEEDS_REVIEW")
        self.assertEqual(state.field_values, {})

    def test_source_evidence_never_overwritten(self):
        # The canonical state must retain every source's raw observation
        # inside conflicts[].observations, not just the resolved value.
        state = reconcile_asset(DEMO_ASSET_ID, scenario="conflicting_sources")
        quantity_conflict = next(c for c in state.conflicts if c.field == "quantity")
        raw_values = {o.value for o in quantity_conflict.observations}
        self.assertEqual(raw_values, {1000, 950, 920})

    def test_reconcile_all_assets(self):
        states = reconcile_all_assets(scenario="healthy")
        self.assertIn(DEMO_ASSET_ID, states)

    def test_to_dict_is_json_serializable(self):
        import json

        state = reconcile_asset(DEMO_ASSET_ID, scenario="shipment_delay")
        serialized = json.dumps(state.to_dict())
        self.assertIsInstance(serialized, str)


if __name__ == "__main__":
    unittest.main()
