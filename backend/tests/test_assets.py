def create_asset(client, **overrides):
    payload = {
        "product_name": "Steel Coils",
        "quantity": 100,
        "unit": "TON",
        "current_lifecycle_stage": "PURCHASE_ORDER",
        "current_estimated_value": 1_000_000,
        "currency": "INR",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/assets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_asset(client):
    asset = create_asset(client)
    assert asset["id"].startswith("AST-")
    assert asset["current_lifecycle_stage"] == "PURCHASE_ORDER"


def test_get_asset(client):
    asset = create_asset(client)
    resp = client.get(f"/api/v1/assets/{asset['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == asset["id"]


def test_get_asset_not_found(client):
    resp = client.get("/api/v1/assets/AST-DOESNOTEXIST")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_list_assets(client):
    create_asset(client)
    create_asset(client, product_name="Aluminium Sheets")
    resp = client.get("/api/v1/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_asset_invalid_stage(client):
    resp = client.post("/api/v1/assets", json={
        "product_name": "X", "quantity": 1, "unit": "EA",
        "current_lifecycle_stage": "NOT_A_STAGE",
    })
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
