from tests.test_assets import create_asset


def test_exposure_and_available_capacity_are_transaction_derived(client, db_session):
    from app.schemas import AssetCreate
    from app.services import asset_service, financing_service
    asset = asset_service.create_asset(db_session, AssetCreate(product_name="Electronics", quantity=1000, unit="EA", current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000))
    financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 200_000)
    body = client.get(f"/api/v1/assets/{asset.id}/exposure").json()
    assert body["total_outstanding"] == 200_000
    assert body["total_principal"] == 200_000
    assert body["active_financing_count"] == 1
    assert body["available_safe_capacity"] == body["maximum_safe_exposure"] - 200_000


def test_duplicate_check_creates_alert_and_audit(client, db_session):
    from app.schemas import AssetCreate
    from app.services import asset_service, financing_service
    asset = asset_service.create_asset(db_session, AssetCreate(product_name="Electronics", quantity=1, unit="EA", current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000))
    financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 100_000)
    result = client.post(f"/api/v1/assets/{asset.id}/duplicate-check", json={"instrument": "IN_TRANSIT_FINANCING"}).json()
    assert result["duplicate_detected"] is True
    assert result["recommended_action"] == "REVIEW"
    assert any(a["alert_type"] == "DUPLICATE_FINANCING" for a in client.get("/api/v1/alerts").json())
    assert any(a["action"] == "DUPLICATE_FINANCING_CHECK" for a in client.get(f"/api/v1/assets/{asset.id}/audit").json())


def test_over_leverage_check_blocks_material_excess(client):
    asset = create_asset(client, current_estimated_value=100_000)
    result = client.post(f"/api/v1/assets/{asset['id']}/leverage-check", json={"requested_amount": 200_000}).json()
    assert result["over_leveraged"] is True
    assert result["action"] == "BLOCK"
    assert result["excess_amount"] > 0


def test_orchestrator_has_structured_deterministic_fallback(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000)
    response = client.post(f"/api/v1/assets/{asset['id']}/orchestrate", json={"trigger": "SHIPMENT_DELAY"})
    assert response.status_code == 200, response.text
    body = response.json()
    for key in ("state_summary", "reconciliation", "risk", "financing", "decision", "explanation"):
        assert key in body
    assert body["explanation"]["mode"] == "DETERMINISTIC_TEMPLATE"
    assert "not a lending approval" in body["explanation"]["disclaimer"]


def test_source_evidence_is_explicitly_simulated(client, db_session):
    from app.models import SourceRecord
    asset = create_asset(client)
    db_session.add(SourceRecord(asset_id=asset["id"], source_name="ERP", field="quantity", value="1000", raw_payload={"simulated": True}))
    db_session.commit()
    evidence = client.get(f"/api/v1/assets/{asset['id']}/evidence").json()
    assert evidence[0]["data_mode"] == "SIMULATED"
    assert evidence[0]["raw_payload"] == {"simulated": True}


def test_payment_simulation_settles_exposure(client, db_session):
    from app.schemas import AssetCreate
    from app.services import asset_service, financing_service
    asset = asset_service.create_asset(db_session, AssetCreate(product_name="Invoice", quantity=1, unit="EA", current_lifecycle_stage="RECEIVABLE", current_estimated_value=500_000))
    financing_service.open_or_update_financing(db_session, asset, "RECEIVABLES_FINANCING", 100_000)
    response = client.post("/api/v1/events/simulate", json={"asset_id": asset.id, "event_type": "PAYMENT_RECEIVED"})
    assert response.status_code == 200, response.text
    assert response.json()["after"]["decision"]["action"] == "SETTLE"
    exposure = client.get(f"/api/v1/assets/{asset.id}/exposure").json()
    assert exposure["total_outstanding"] == 0
    assert client.get(f"/api/v1/assets/{asset.id}").json()["current_lifecycle_stage"] == "CASH_REALISATION"


def test_simulator_shipment_delay_returns_before_after(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000)
    response = client.post("/api/v1/events/simulate", json={"asset_id": asset["id"], "event_type": "SHIPMENT_DELAY"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["after"]["risk"]["risk_score"] > body["before"]["risk"]["risk_score"]
    assert body["after"]["trigger"] == "SHIPMENT_DELAY"
