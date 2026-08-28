from tests.test_assets import create_asset


def test_financing_evaluate_returns_contract_shape(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT", current_estimated_value=2_000_000)
    resp = client.post("/api/v1/financing/evaluate", json={"asset_id": asset["id"], "reason": "LIFECYCLE_CHANGE"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for field in [
        "asset_id", "financing_required", "recommended_instrument", "maximum_safe_amount",
        "recommended_amount", "risk_level", "confidence", "action", "decision_factors",
    ]:
        assert field in body
    assert body["recommended_instrument"] == "IN_TRANSIT_FINANCING"
    assert body["recommended_amount"] > 0


def test_financing_evaluate_not_found(client):
    resp = client.post("/api/v1/financing/evaluate", json={"asset_id": "AST-NOPE"})
    assert resp.status_code == 404


def test_get_current_financing_evaluation_is_read_only(client):
    asset = create_asset(client, current_lifecycle_stage="SHIPMENT", current_estimated_value=2_000_000)
    resp = client.get(f"/api/v1/assets/{asset['id']}/financing/evaluation")
    assert resp.status_code == 200
    assert resp.json()["recommended_instrument"] == "IN_TRANSIT_FINANCING"
    assert client.get(f"/api/v1/assets/{asset['id']}/decisions").json() == []


def test_existing_exposure_reduces_available_capacity(client, db_session):
    from app.services import asset_service, financing_service
    from app.schemas import AssetCreate

    asset = asset_service.create_asset(db_session, AssetCreate(
        product_name="Timber", quantity=10, unit="TON",
        current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000,
    ))
    before = financing_service.evaluate_financing(db_session, asset, risk_score=20, risk_level="LOW", confidence=0.9)
    financing_service.open_or_update_financing(db_session, asset, before["recommended_instrument"], before["recommended_amount"])

    db_session.refresh(asset)
    after = financing_service.evaluate_financing(db_session, asset, risk_score=20, risk_level="LOW", confidence=0.9)
    assert after["recommended_amount"] <= before["recommended_amount"]


def test_duplicate_financing_updates_existing_line(client, db_session):
    from app.services import asset_service, financing_service
    from app.schemas import AssetCreate

    asset = asset_service.create_asset(db_session, AssetCreate(
        product_name="Grain", quantity=10, unit="TON",
        current_lifecycle_stage="SHIPMENT", current_estimated_value=1_000_000,
    ))
    txn1 = financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 100000)
    txn2 = financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 150000)
    assert txn1.id == txn2.id  # updated, not duplicated
    assert txn2.outstanding_amount == 150000


def test_over_leverage_is_blocked(client, db_session):
    from app.services import asset_service, financing_service
    from app.schemas import AssetCreate
    from app.core.errors import OverLeverageError

    asset = asset_service.create_asset(db_session, AssetCreate(
        product_name="Copper", quantity=10, unit="TON",
        current_lifecycle_stage="SHIPMENT", current_estimated_value=100000,
    ))
    try:
        financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 999999)
        assert False, "expected OverLeverageError"
    except OverLeverageError as e:
        assert e.code == "OVER_LEVERAGE"


def test_financing_transition(client, db_session):
    from app.services import asset_service, financing_service
    from app.schemas import AssetCreate

    asset = asset_service.create_asset(db_session, AssetCreate(
        product_name="Rice", quantity=10, unit="TON",
        current_lifecycle_stage="DELIVERY", current_estimated_value=500000,
    ))
    txn = financing_service.open_or_update_financing(db_session, asset, "IN_TRANSIT_FINANCING", 100000)

    resp = client.post(f"/api/v1/financing/{txn.id}/transition", json={"new_instrument": "INVOICE_FINANCING"})
    assert resp.status_code == 200
    assert resp.json()["instrument"] == "INVOICE_FINANCING"
    assert resp.json()["status"] == "TRANSITIONED"


def test_financing_settlement(client, db_session):
    from app.services import asset_service, financing_service
    from app.schemas import AssetCreate

    asset = asset_service.create_asset(db_session, AssetCreate(
        product_name="Tea", quantity=10, unit="TON",
        current_lifecycle_stage="RECEIVABLE", current_estimated_value=300000,
    ))
    txn = financing_service.open_or_update_financing(db_session, asset, "RECEIVABLES_FINANCING", 50000)
    settled = financing_service.settle_financing(db_session, txn.id)
    assert settled.status == "SETTLED"
    assert settled.outstanding_amount == 0.0
