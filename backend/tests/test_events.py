from tests.test_assets import create_asset


def test_shipment_delay_triggers_reassessment_and_alert(client):
    """SOURCE: 15_DEMO_SCENARIOS.md Scenario 2."""
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT", current_estimated_value=1_500_000)

    # Establish baseline risk/financing first.
    client.post("/api/v1/financing/evaluate", json={"asset_id": asset["id"]})

    resp = client.post(f"/api/v1/assets/{asset['id']}/events", json={
        "event_type": "SHIPMENT_DELAY",
        "severity": "MEDIUM",
    })
    assert resp.status_code == 201, resp.text

    risk_resp = client.get(f"/api/v1/assets/{asset['id']}/risk")
    assert risk_resp.status_code == 200
    assert risk_resp.json()["overall_score"] > 0

    alerts_resp = client.get("/api/v1/alerts")
    assert alerts_resp.status_code == 200
    assert any(a["asset_id"] == asset["id"] for a in alerts_resp.json())


def test_delivery_confirmed_advances_stage(client):
    """SOURCE: 15_DEMO_SCENARIOS.md Scenario 5 (delivery -> invoice transition)."""
    asset = create_asset(client, current_lifecycle_stage="DELIVERY", current_estimated_value=800000)
    resp = client.post(f"/api/v1/assets/{asset['id']}/events", json={"event_type": "INVOICE_VERIFIED"})
    assert resp.status_code == 201
    updated = client.get(f"/api/v1/assets/{asset['id']}").json()
    assert updated["current_lifecycle_stage"] == "INVOICE"


def test_unknown_event_type_rejected(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT")
    resp = client.post(f"/api/v1/assets/{asset['id']}/events", json={"event_type": "NOT_A_REAL_EVENT"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_events_newest_first(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT")
    client.post(f"/api/v1/assets/{asset['id']}/events", json={"event_type": "SHIPMENT_DELAY"})
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    assert resp.json()[0]["asset_id"] == asset["id"]
    assert resp.json()[0]["event_type"] == "SHIPMENT_DELAY"
