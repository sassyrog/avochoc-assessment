import pytest
from unittest.mock import patch, AsyncMock
from io import BytesIO


@pytest.fixture
def sample_jpeg():
    """Create a minimal valid JPEG file."""
    # Minimal JPEG bytes (not a real image, but has correct magic bytes)
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"


@pytest.fixture
def sample_png():
    """Create a minimal valid PNG file."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"


@pytest.fixture
async def test_asset(client, auth_headers):
    """Create a test asset for image upload tests."""
    payload = {
        "name": "Test Laptop",
        "type": "Hardware",
        "check_in_date": "2024-01-01",
        "count": 1,
        "model": "MacBook Pro",
        "serial_number": "TEST123",
    }
    response = await client.post("/api/v1/assets", json=payload, headers=auth_headers)
    return response.json()["data"]


@pytest.mark.asyncio
async def test_upload_image_success(client, auth_headers, test_asset, sample_jpeg):
    """Should successfully upload an image and update asset description."""
    mock_description = "A silver MacBook Pro laptop. The device appears to be in good condition with stickers on the lid."

    with patch("app.services.ai_service.AIService") as mock_ai_class:
        mock_ai = AsyncMock()
        mock_ai.describe_asset_image.return_value = mock_description
        mock_ai_class.return_value = mock_ai

        response = await client.post(
            f"/api/v1/assets/{test_asset['id']}/upload-image",
            files={"image": ("laptop.jpg", BytesIO(sample_jpeg), "image/jpeg")},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Asset image processed and description updated"
    assert data["data"]["description"] == mock_description
    assert data["data"]["id"] == test_asset["id"]


@pytest.mark.asyncio
async def test_upload_image_png(client, auth_headers, test_asset, sample_png):
    """Should accept PNG images."""
    with patch("app.services.ai_service.AIService") as mock_ai_class:
        mock_ai = AsyncMock()
        mock_ai.describe_asset_image.return_value = "A test device."
        mock_ai_class.return_value = mock_ai

        response = await client.post(
            f"/api/v1/assets/{test_asset['id']}/upload-image",
            files={"image": ("device.png", BytesIO(sample_png), "image/png")},
            headers=auth_headers,
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_image_asset_not_found(client, auth_headers, sample_jpeg):
    """Should return 404 when asset doesn't exist."""
    fake_asset_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(
        f"/api/v1/assets/{fake_asset_id}/upload-image",
        files={"image": ("laptop.jpg", BytesIO(sample_jpeg), "image/jpeg")},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_image_invalid_file_type(client, auth_headers, test_asset):
    """Should return 400 for unsupported file types."""
    pdf_content = b"%PDF-1.4 fake pdf content"

    response = await client.post(
        f"/api/v1/assets/{test_asset['id']}/upload-image",
        files={"image": ("document.pdf", BytesIO(pdf_content), "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "Unsupported image type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_image_unauthorized(client, test_asset, sample_jpeg):
    """Should return 401 without authentication."""
    # Note: test_asset was created with auth, but we access without auth
    response = await client.post(
        f"/api/v1/assets/{test_asset['id']}/upload-image",
        files={"image": ("laptop.jpg", BytesIO(sample_jpeg), "image/jpeg")},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_image_ai_service_failure(
    client, auth_headers, test_asset, sample_jpeg
):
    """Should return 503 when AI service fails."""
    from app.services.ai_service import AIProviderError

    with patch("app.services.ai_service.AIService") as mock_ai_class:
        mock_ai = AsyncMock()
        mock_ai.describe_asset_image.side_effect = AIProviderError("Connection refused")
        mock_ai_class.return_value = mock_ai

        response = await client.post(
            f"/api/v1/assets/{test_asset['id']}/upload-image",
            files={"image": ("laptop.jpg", BytesIO(sample_jpeg), "image/jpeg")},
            headers=auth_headers,
        )

    assert response.status_code == 503
    assert "AI service unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_image_preserves_other_asset_fields(
    client, auth_headers, test_asset, sample_jpeg
):
    """Should only update description, preserving other fields."""
    with patch("app.services.ai_service.AIService") as mock_ai_class:
        mock_ai = AsyncMock()
        mock_ai.describe_asset_image.return_value = "New AI description"
        mock_ai_class.return_value = mock_ai

        response = await client.post(
            f"/api/v1/assets/{test_asset['id']}/upload-image",
            files={"image": ("laptop.jpg", BytesIO(sample_jpeg), "image/jpeg")},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()["data"]

    # Original fields should be preserved
    assert data["name"] == "Test Laptop"
    assert data["type"] == "Hardware"
    assert data["model"] == "MacBook Pro"
    assert data["serial_number"] == "TEST123"

    # Description should be updated
    assert data["description"] == "New AI description"
