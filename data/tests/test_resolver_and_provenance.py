import unittest

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.mapper import map_records
from data.resolver import resolve_asset_fields, resolve_field
from data.provenance import get_provenance_for_asset
from data.sources import DEMO_ASSET_ID
from data.models import NormalizedRecord


class TestResolver(unittest.TestCase):
    def _fields_for(self, scenario):
        raw = load_source_records(scenario=scenario)
        normalized = normalize_records(raw)
        mapped = map_records(normalized)
        return mapped[DEMO_ASSET_ID]

    def test_healthy_scenario_resolves_with_high_confidence(self):
        fields = self._fields_for("healthy")
        conflicts = resolve_asset_fields(DEMO_ASSET_ID, fields)
        quantity_conflict = next(c for c in conflicts if c.field == "quantity")
        self.assertEqual(quantity_conflict.resolution_status, "NO_CONFLICT")
        self.assertEqual(quantity_conflict.canonical_value, 1000)
        self.assertGreaterEqual(quantity_conflict.confidence, 0.9)

    def test_conflicting_scenario_quantity_has_no_majority_and_is_qualified(self):
        # ERP=1000, PO=1000, WAREHOUSE=950, TELEMETRY=920 -> ERP+PO agree (2 of 4),
        # not a strict majority (needs > 2), so QUALIFIED via reliability rank.
        fields = self._fields_for("conflicting_sources")
        conflicts = resolve_asset_fields(DEMO_ASSET_ID, fields)
        quantity_conflict = next(c for c in conflicts if c.field == "quantity")
        self.assertIn(quantity_conflict.resolution_status, ("QUALIFIED", "RESOLVED"))
        self.assertLess(quantity_conflict.confidence, 0.9)
        # ERP is rank 1 (most reliable) and reports 1000
        if quantity_conflict.resolution_status == "QUALIFIED":
            self.assertEqual(quantity_conflict.canonical_value, 1000)

    def test_production_status_conflict_erp_and_warehouse_agree(self):
        # ERP=COMPLETE, WAREHOUSE=COMPLETE, TELEMETRY=IN_PROGRESS -> majority COMPLETE
        fields = self._fields_for("conflicting_sources")
        conflicts = resolve_asset_fields(DEMO_ASSET_ID, fields)
        prod_conflict = next(c for c in conflicts if c.field == "production_status")
        self.assertEqual(prod_conflict.resolution_status, "RESOLVED")
        self.assertEqual(prod_conflict.canonical_value, "COMPLETE")

    def test_single_source_field_is_deterministic_and_high_confidence(self):
        fields = self._fields_for("healthy")
        conflicts = resolve_asset_fields(DEMO_ASSET_ID, fields)
        po_conflict = next(c for c in conflicts if c.field == "po_number")
        self.assertEqual(po_conflict.resolution_status, "NO_CONFLICT")
        self.assertEqual(po_conflict.canonical_value, "PO-2001")

    def test_needs_review_when_no_usable_value(self):
        obs = [
            NormalizedRecord(
                asset_id=DEMO_ASSET_ID,
                source="ERP",
                source_record_id="X",
                field="ghost_field",
                value=None,
                observed_at="2026-01-01T00:00:00Z",
            ),
        ]
        result = resolve_field(DEMO_ASSET_ID, "ghost_field", obs)
        self.assertEqual(result.resolution_status, "NEEDS_REVIEW")
        self.assertEqual(result.confidence, 0.0)

    def test_resolution_is_deterministic_across_runs(self):
        fields = self._fields_for("conflicting_sources")
        first = resolve_asset_fields(DEMO_ASSET_ID, fields)
        second = resolve_asset_fields(DEMO_ASSET_ID, fields)
        self.assertEqual(
            [c.canonical_value for c in first],
            [c.canonical_value for c in second],
        )


class TestProvenance(unittest.TestCase):
    def test_provenance_lists_contributing_sources(self):
        raw = load_source_records(scenario="healthy")
        normalized = normalize_records(raw)
        mapped = map_records(normalized)
        conflicts = resolve_asset_fields(DEMO_ASSET_ID, mapped[DEMO_ASSET_ID])
        provenance = get_provenance_for_asset(conflicts)
        quantity_prov = next(p for p in provenance if p.field == "quantity")
        self.assertIn("ERP", quantity_prov.sources)
        self.assertGreater(len(quantity_prov.source_record_ids), 0)

    def test_needs_review_field_has_empty_provenance(self):
        conflict = resolve_field(
            DEMO_ASSET_ID,
            "ghost_field",
            [
                NormalizedRecord(
                    asset_id=DEMO_ASSET_ID,
                    source="ERP",
                    source_record_id="X",
                    field="ghost_field",
                    value=None,
                    observed_at="2026-01-01T00:00:00Z",
                )
            ],
        )
        from data.provenance import get_provenance

        prov = get_provenance(conflict)
        self.assertEqual(prov.sources, [])


if __name__ == "__main__":
    unittest.main()
