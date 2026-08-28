from tests.test_assets import create_asset


def test_reconciliation_detects_conflict(client, db_session):
    """SOURCE: 15_DEMO_SCENARIOS.md Scenario 4 / 09_RECONCILIATION_ENGINE.md example."""
    from app.models import SourceRecord

    asset = create_asset(client, current_lifecycle_stage="PRODUCTION")

    db_session.add_all([
        SourceRecord(asset_id=asset["id"], source_name="ERP", field="physical_state", value="COMPLETE"),
        SourceRecord(asset_id=asset["id"], source_name="TELEMETRY", field="physical_state", value="92_PCT"),
        SourceRecord(asset_id=asset["id"], source_name="WAREHOUSE", field="physical_state", value="COMPLETE"),
    ])
    db_session.commit()

    resp = client.post("/api/v1/reconciliation/run", json={"asset_id": asset["id"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["canonical_state"]["physical_state"] == "COMPLETE"  # ERP/WAREHOUSE outrank TELEMETRY
    assert len(body["conflicts"]) == 1
    assert body["confidence"] < 1.0

    conflicts_resp = client.get(f"/api/v1/assets/{asset['id']}/conflicts")
    assert conflicts_resp.status_code == 200
    assert len(conflicts_resp.json()) == 1


def test_reconciliation_no_conflict_when_sources_agree(client, db_session):
    from app.models import SourceRecord

    asset = create_asset(client, current_lifecycle_stage="PRODUCTION")
    db_session.add_all([
        SourceRecord(asset_id=asset["id"], source_name="ERP", field="physical_state", value="COMPLETE"),
        SourceRecord(asset_id=asset["id"], source_name="WAREHOUSE", field="physical_state", value="COMPLETE"),
    ])
    db_session.commit()

    resp = client.post("/api/v1/reconciliation/run", json={"asset_id": asset["id"]})
    assert resp.status_code == 200
    assert resp.json()["conflicts"] == []
