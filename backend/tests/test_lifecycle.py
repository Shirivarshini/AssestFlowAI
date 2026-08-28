from tests.test_assets import create_asset


def test_valid_lifecycle_transition(client):
    asset = create_asset(client, current_lifecycle_stage="PURCHASE_ORDER")
    resp = client.post(f"/api/v1/assets/{asset['id']}/events", json={
        "event_type": "PRODUCTION_DELAY",
        "to_stage": "RAW_MATERIAL",
    })
    assert resp.status_code == 201, resp.text
    assert resp.json()["to_stage"] == "RAW_MATERIAL"

    updated = client.get(f"/api/v1/assets/{asset['id']}").json()
    assert updated["current_lifecycle_stage"] == "RAW_MATERIAL"


def test_invalid_lifecycle_transition(client):
    asset = create_asset(client, current_lifecycle_stage="PURCHASE_ORDER")
    resp = client.post(f"/api/v1/assets/{asset['id']}/events", json={
        "event_type": "DELIVERY_CONFIRMED",
        "to_stage": "CASH_REALISATION",  # illegal jump from PURCHASE_ORDER
    })
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INVALID_TRANSITION"


def test_timeline_records_events(client):
    asset = create_asset(client, current_lifecycle_stage="PURCHASE_ORDER")
    client.post(f"/api/v1/assets/{asset['id']}/events", json={
        "event_type": "PRODUCTION_DELAY", "to_stage": "RAW_MATERIAL",
    })
    client.post(f"/api/v1/assets/{asset['id']}/events", json={
        "event_type": "PRODUCTION_DELAY", "to_stage": "PRODUCTION",
    })
    resp = client.get(f"/api/v1/assets/{asset['id']}/timeline")
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_lifecycle_stage"] == "PRODUCTION"
    assert len(body["events"]) == 2
