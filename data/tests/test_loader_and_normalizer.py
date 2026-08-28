import unittest

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.sources import DEMO_ASSET_ID


class TestLoader(unittest.TestCase):
    def test_loads_all_seven_sources(self):
        records = load_source_records(scenario="healthy")
        sources = {r.source for r in records}
        self.assertEqual(
            sources,
            {
                "ERP",
                "PURCHASE_ORDER",
                "INVOICE",
                "LOGISTICS",
                "WAREHOUSE",
                "TELEMETRY",
                "FINANCING",
            },
        )

    def test_is_deterministic(self):
        a = load_source_records(scenario="healthy")
        b = load_source_records(scenario="healthy")
        self.assertEqual([r.to_dict() for r in a], [r.to_dict() for r in b])

    def test_all_records_reference_demo_asset(self):
        records = load_source_records(scenario="healthy")
        self.assertTrue(all(r.asset_id == DEMO_ASSET_ID for r in records))

    def test_source_filter(self):
        records = load_source_records(scenario="healthy", sources=["ERP", "WAREHOUSE"])
        sources = {r.source for r in records}
        self.assertEqual(sources, {"ERP", "WAREHOUSE"})

    def test_unknown_scenario_falls_back_gracefully(self):
        # Should not raise, and should still return records.
        records = load_source_records(scenario="not_a_real_scenario")
        self.assertTrue(len(records) > 0)


class TestNormalizer(unittest.TestCase):
    def test_normalizes_every_payload_field(self):
        raw = load_source_records(scenario="healthy")
        normalized = normalize_records(raw)
        erp_raw = next(r for r in raw if r.source == "ERP")
        erp_normalized = [n for n in normalized if n.source == "ERP"]
        self.assertEqual(len(erp_normalized), len(erp_raw.payload))

    def test_normalized_record_shape(self):
        raw = load_source_records(scenario="healthy")
        normalized = normalize_records(raw)
        sample = normalized[0]
        self.assertTrue(hasattr(sample, "asset_id"))
        self.assertTrue(hasattr(sample, "source"))
        self.assertTrue(hasattr(sample, "source_record_id"))
        self.assertTrue(hasattr(sample, "field"))
        self.assertTrue(hasattr(sample, "value"))
        self.assertTrue(hasattr(sample, "observed_at"))

    def test_quantity_field_present_across_sources(self):
        raw = load_source_records(scenario="conflicting_sources")
        normalized = normalize_records(raw)
        quantity_sources = {n.source for n in normalized if n.field == "quantity"}
        self.assertEqual(
            quantity_sources, {"ERP", "WAREHOUSE", "TELEMETRY", "PURCHASE_ORDER"}
        )


if __name__ == "__main__":
    unittest.main()
