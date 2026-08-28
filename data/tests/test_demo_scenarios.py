import unittest

from data.fixtures.demo_scenarios import get_demo_scenario, list_demo_scenarios


class TestDemoScenarios(unittest.TestCase):
    def test_four_required_scenarios_present(self):
        self.assertEqual(
            set(list_demo_scenarios()),
            {
                "healthy_lifecycle",
                "shipment_delay",
                "duplicate_financing",
                "conflicting_sources",
            },
        )

    def test_healthy_lifecycle_scenario(self):
        scenario = get_demo_scenario("healthy_lifecycle")
        self.assertEqual(scenario["reconciled_state"].status, "OK")
        self.assertEqual(
            len(scenario["lifecycle_transitions"]), 9
        )  # 10 stages -> 9 transitions

    def test_shipment_delay_scenario_has_event(self):
        scenario = get_demo_scenario("shipment_delay")
        self.assertEqual(len(scenario["events"]), 1)
        self.assertEqual(scenario["events"][0].event_type, "SHIPMENT_DELAY")

    def test_duplicate_financing_scenario_has_high_exposure(self):
        scenario = get_demo_scenario("duplicate_financing")
        financial_state = scenario["reconciled_state"].financial_state
        self.assertGreater(financial_state["outstanding_amount"], 1000000)

    def test_conflicting_sources_scenario_has_conflicts(self):
        scenario = get_demo_scenario("conflicting_sources")
        state = scenario["reconciled_state"]
        conflict_fields = {
            c.field for c in state.conflicts if c.resolution_status != "NO_CONFLICT"
        }
        self.assertIn("quantity", conflict_fields)

    def test_unknown_scenario_raises(self):
        with self.assertRaises(KeyError):
            get_demo_scenario("not_a_scenario")

    def test_scenarios_are_deterministic(self):
        first = get_demo_scenario("conflicting_sources")
        second = get_demo_scenario("conflicting_sources")
        self.assertEqual(
            first["reconciled_state"].to_dict(),
            second["reconciled_state"].to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
