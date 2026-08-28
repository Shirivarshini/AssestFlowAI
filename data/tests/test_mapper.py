import unittest

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.mapper import map_records, get_asset_ids
from data.sources import DEMO_ASSET_ID


class TestMapper(unittest.TestCase):
    def setUp(self):
        raw = load_source_records(scenario="healthy")
        self.normalized = normalize_records(raw)

    def test_groups_by_asset_then_field(self):
        mapped = map_records(self.normalized)
        self.assertIn(DEMO_ASSET_ID, mapped)
        self.assertIn("quantity", mapped[DEMO_ASSET_ID])
        self.assertTrue(
            all(isinstance(v, list) for v in mapped[DEMO_ASSET_ID].values())
        )

    def test_quantity_observations_all_reference_correct_asset(self):
        mapped = map_records(self.normalized)
        for obs in mapped[DEMO_ASSET_ID]["quantity"]:
            self.assertEqual(obs.asset_id, DEMO_ASSET_ID)
            self.assertEqual(obs.field, "quantity")

    def test_get_asset_ids(self):
        ids = get_asset_ids(self.normalized)
        self.assertEqual(ids, [DEMO_ASSET_ID])


if __name__ == "__main__":
    unittest.main()
