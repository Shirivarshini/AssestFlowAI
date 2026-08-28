import unittest

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.mapper import map_records
from data.conflict_detector import detect_conflicts
from data.sources import DEMO_ASSET_ID


class TestConflictDetector(unittest.TestCase):
    def _fields_for(self, scenario):
        raw = load_source_records(scenario=scenario)
        normalized = normalize_records(raw)
        mapped = map_records(normalized)
        return mapped[DEMO_ASSET_ID]

    def test_no_conflict_in_healthy_scenario_quantity(self):
        fields = self._fields_for("healthy")
        result = detect_conflicts(fields)
        self.assertEqual(result["quantity"]["status"], "NO_CONFLICT")

    def test_conflict_detected_in_conflicting_sources_scenario(self):
        fields = self._fields_for("conflicting_sources")
        result = detect_conflicts(fields)
        self.assertEqual(result["quantity"]["status"], "CONFLICT")
        self.assertEqual(result["production_status"]["status"], "CONFLICT")

    def test_single_source_field_is_no_conflict(self):
        fields = self._fields_for("healthy")
        # po_number only comes from PURCHASE_ORDER
        result = detect_conflicts(fields)
        self.assertEqual(result["po_number"]["status"], "NO_CONFLICT")

    def test_all_observations_preserved_even_when_conflicting(self):
        fields = self._fields_for("conflicting_sources")
        result = detect_conflicts(fields)
        quantity_observations = result["quantity"]["observations"]
        sources = {o.source for o in quantity_observations}
        # ERP, WAREHOUSE, TELEMETRY, PURCHASE_ORDER all report quantity
        self.assertEqual(sources, {"ERP", "WAREHOUSE", "TELEMETRY", "PURCHASE_ORDER"})

    def test_needs_review_when_all_values_null(self):
        from data.models import NormalizedRecord

        obs = [
            NormalizedRecord(
                asset_id=DEMO_ASSET_ID,
                source="ERP",
                source_record_id="X",
                field="mystery_field",
                value=None,
                observed_at="2026-01-01T00:00:00Z",
            ),
        ]
        from data.conflict_detector import detect_field_conflict

        result = detect_field_conflict(obs)
        self.assertEqual(result["status"], "NEEDS_REVIEW")


if __name__ == "__main__":
    unittest.main()
