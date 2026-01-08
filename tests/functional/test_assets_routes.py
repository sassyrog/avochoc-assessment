import pytest


@pytest.mark.asyncio
async def test_create_asset_api(client, auth_headers):
    payload = {
        "name": "Tablet",
        "type": "Hardware",
        "check_in_date": "2023-03-01",
        "count": 3,
        "model": "iPad Pro",
        "serial_number": "IPAD123",
        "description": "Office tablets",
    }

    response = await client.post("/api/v1/assets", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()["data"]

    assert data["name"] == "Tablet"
    assert data["count"] == 3
    assert data["model"] == "iPad Pro"
    assert data["serial_number"] == "IPAD123"
    assert data["check_in_date"] == "2023-03-01"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_assets_api(client, auth_headers):
    # First create an asset
    payload = {
        "name": "Monitor",
        "type": "Hardware",
        "check_in_date": "2023-04-01",
        "count": 1,
        "model": "Dell",
        "serial_number": "DELL123",
    }
    await client.post("/api/v1/assets", json=payload, headers=auth_headers)

    # Get all assets
    response = await client.get("/api/v1/assets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) > 0
    # Search for the asset we just created
    found = any(a["name"] == "Monitor" for a in data)
    assert found


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    response = await client.get("/api/v1/assets")
    assert response.status_code == 401
