import pytest


@pytest.mark.asyncio
async def test_register_with_extra_fields(client):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword",
        "name": "John Doe",
        "phone": "+1234567890",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]

    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "John Doe"
    assert data["user"]["phone"] == "+1234567890"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_returns_extra_fields(client):
    # Register first
    register_payload = {
        "email": "loginuser@example.com",
        "password": "strongpassword",
        "name": "Jane Doe",
        "phone": "9876543210",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    # Login
    login_payload = {"email": "loginuser@example.com", "password": "strongpassword"}

    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["user"]["name"] == "Jane Doe"
    assert data["user"]["phone"] == "9876543210"
